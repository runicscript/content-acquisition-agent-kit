#!/usr/bin/env python3
"""Provision and verify a project-owned Feishu workspace with the official CLI."""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
APP_ID = re.compile(r"cli_[A-Za-z0-9]+")
TOKEN = re.compile(r"[A-Za-z0-9_-]+")
BOOTSTRAP_COMMANDS = {
    ("config", "init"), ("profile", "add"), ("profile", "list"),
    ("auth", "login"), ("auth", "qrcode"), ("auth", "check"), ("auth", "status"),
}
BASE_COMMANDS = {
    "+field-list", "+record-list", "+record-search", "+record-get", "+record-upsert",
}


class SetupError(Exception):
    pass


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def get_id(data, *keys):
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if isinstance(value, str) and TOKEN.fullmatch(value):
                return value
    raise SetupError("飞书返回中缺少可验证的 " + "/".join(keys))


def write_state(path, data):
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     delete=False) as temporary:
        name = temporary.name
        try:
            json.dump(data, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
            os.replace(name, path)
        finally:
            Path(name).unlink(missing_ok=True)


@contextmanager
def local_lock(directory):
    directory.mkdir(mode=0o700, exist_ok=True)
    path = directory / "feishu.lock"
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise SetupError("已有飞书任务运行或上次异常退出。确认旧进程停止后再移除 .project/feishu.lock。") from exc
    try:
        with os.fdopen(fd, "w") as lock:
            lock.write(str(os.getpid()))
        yield
    finally:
        path.unlink()


def local_path(directory, name):
    result = directory / name
    if result.is_symlink():
        raise SetupError(f"拒绝使用符号链接作为飞书运行状态或配置路径 ({name})。")
    return result


def error_details(stderr, stdout):
    for output in (stderr, stdout):
        try:
            error = json.loads(output).get("error", {})
        except (ValueError, AttributeError):
            continue
        if isinstance(error, dict) and error:
            details = [str(error[key]) for key in ("type", "subtype", "code") if key in error]
            scopes = error.get("missing_scopes")
            if isinstance(scopes, list):
                details.extend(scope for scope in scopes
                               if isinstance(scope, str) and re.fullmatch(r"[\w.:/-]+", scope))
            return " / ".join(details)
    return "没有可解析的错误摘要"


class Lark:
    def __init__(self, directory, slug):
        self.directory = local_path(directory, "lark-cli")
        local_path(self.directory, "config.json")
        self.profile = f"acq-{slug}"
        # Inherited Lark config, credential, endpoint and proxy overrides must not take effect.
        self.env = {k: v for k, v in os.environ.items()
                    if not k.upper().startswith(("LARKSUITE_CLI_", "OPENCLAW_", "HERMES_"))
                    and k.upper() != "LARK_CHANNEL"}
        self.env.update(
            LARKSUITE_CLI_CONFIG_DIR=str(self.directory),
            LARKSUITE_CLI_NO_UPDATE_NOTIFIER="1",
            LARKSUITE_CLI_NO_SKILLS_NOTIFIER="1",
        )

    def argv(self, args):
        return ["lark-cli", "--profile", self.profile, *args]

    def json(self, args, *, content=None):
        try:
            result = subprocess.run(self.argv(args), env=self.env, input=content or "",
                                    capture_output=True, text=True, encoding="utf-8",
                                    timeout=100, check=False)
        except subprocess.TimeoutExpired as exc:
            raise SetupError(f"{' '.join(args[:2])} 超时。") from exc
        if result.returncode:
            raise SetupError(f"{' '.join(args[:2])} 失败 ({result.returncode})，"
                             + error_details(result.stderr, result.stdout))
        try:
            data = json.loads(result.stdout)
        except ValueError as exc:
            raise SetupError(f"{' '.join(args[:2])} 未返回可解析的 JSON。") from exc
        if not isinstance(data, dict):
            raise SetupError(f"{' '.join(args[:2])} 返回类型异常。")
        return data

    def call(self, *args, content=None):
        result = self.json([*args, "--as", "user", "--format", "json"], content=content)
        if result.get("ok") is not True or result.get("identity") != "user":
            raise SetupError(f"{' '.join(args[:2])} 未返回成功的用户身份响应。")
        data = result.get("data")
        if not isinstance(data, dict):
            raise SetupError(f"{' '.join(args[:2])} 缺少响应数据。")
        return data

    def identity(self, app_id, brand, tenant_key=None):
        me = self.json(["whoami", "--as", "user"])
        if (me.get("profile"), me.get("appId"), me.get("brand"), me.get("identity"),
                me.get("available")) != (self.profile, app_id, brand, "user", True):
            raise SetupError("飞书 profile、App ID、品牌或用户授权不匹配。")
        open_id = get_id(me.get("onBehalfOf"), "openId")
        # This is the sole raw endpoint. The CLI has no typed OAuth user-info command.
        info = self.call("api", "GET", "/open-apis/authen/v1/user_info")
        if isinstance(info.get("data"), dict) and info.get("code") == 0:
            info = info["data"]
        actual_tenant = get_id(info, "tenant_key")
        if get_id(info, "open_id") != open_id or (tenant_key and actual_tenant != tenant_key):
            raise SetupError("飞书用户身份或租户与期望不符。")
        return {"profile": self.profile, "app_id": app_id, "brand": brand,
                "tenant_key": actual_tenant, "open_id": open_id}

    def files(self, parent=""):
        rows, page = [], ""
        seen_pages = set()
        while True:
            args = ["drive", "files", "list"]
            if parent:
                args += ["--folder-token", parent, "--page-size", "200"]
            if page:
                args += ["--page-token", page]
            data = self.call(*args)
            rows.extend(items(data, "files") if "files" in data else [])
            if not data.get("has_more"):
                return rows
            page = get_id(data, "next_page_token", "page_token")
            if page in seen_pages:
                raise SetupError("云空间分页异常。")
            seen_pages.add(page)

    def wiki_rows(self, target, parent):
        rows, page = [], ""
        seen_pages = set()
        while True:
            args = ["wiki", "+node-list", "--space-id", target["space_id"],
                    "--parent-node-token", parent]
            if page:
                args += ["--page-token", page]
            data = self.call(*args)
            rows.extend(items(data, "nodes"))
            if not data.get("has_more"):
                return rows
            page = get_id(data, "page_token")
            if page in seen_pages:
                raise SetupError("Wiki 子节点分页异常。")
            seen_pages.add(page)

    def base_rows(self, shortcut, key, *args):
        rows = []
        while True:
            data = self.call("base", shortcut, *args, "--offset", str(len(rows)), "--limit", "100")
            batch = items(data, key)
            rows.extend(batch)
            total = data.get("total")
            if isinstance(total, int) and len(rows) >= total:
                return rows
            if total is None and len(batch) < 100:
                return rows
            if not batch or len(rows) > 1000:
                raise SetupError(f"{shortcut} 分页异常。")


def items(data, key):
    result = data.get(key)
    if not isinstance(result, list) or any(not isinstance(row, dict) for row in result):
        raise SetupError(f"飞书列表缺少有效的 {key}。")
    return result


def matching(rows, title, kind=None):
    exact = [row for row in rows if row.get("name", row.get("table_name")) == title]
    if len(exact) > 1 or (exact and kind and exact[0].get("type") != kind):
        raise SetupError(f"资源「{title}」重名或类型冲突，需核对后继续。")
    return exact[0] if exact else None


def wiki_token(value):
    if TOKEN.fullmatch(value):
        return value
    url = urlsplit(value)
    match = re.fullmatch(r"/wiki/([A-Za-z0-9_-]+)/?", url.path)
    if url.scheme != "https" or not url.hostname or url.username or not match:
        raise SetupError("请提供目标 Wiki 的 HTTPS 页面链接或节点 ID。")
    return match[1]


def wiki_target(lark, token):
    result = lark.call("wiki", "+node-get", "--node-token", token)
    node = get_id(result, "node_token")
    space = get_id(result, "space_id")
    if node != token or not space.isdecimal():
        raise SetupError("Wiki 父节点或空间回读不匹配。")
    return {"space_id": space, "node_token": node}


def wiki_match(lark, target, parent, title, kind):
    rows = [
        dict(row, name=row.get("title"), type=row.get("obj_type"))
        for row in lark.wiki_rows(target, parent)
    ]
    row = matching(rows, title, kind)
    if row and row.get("node_type") != "origin":
        raise SetupError(f"Wiki 资源「{title}」不是实体节点。")
    return row


class Provision:
    def __init__(self, lark, path, state, apply, retry_pending):
        self.lark, self.path, self.state = lark, path, state
        self.apply, self.retry_pending = apply, retry_pending

    def ensure(self, key, find, create, id_keys):
        saved = self.state["resources"].get(key)
        current = find()
        if saved is not None:
            if (current is None or get_id(current, *id_keys) != saved["id"] or
                    ("node_token" in saved and current.get("node_token") != saved["node_token"])):
                raise SetupError(f"{key} 未通过回读校验。请核对项目资源映射。")
            return saved["id"]
        if not self.apply:
            raise SetupError(f"项目未完成配置，缺少 {key}。")
        pending = self.state.get("pending")
        if pending not in (None, key):
            raise SetupError(f"上一次创建 {pending} 的结果待核对，请先恢复该步骤。")
        if current is not None:
            if pending != key:
                raise SetupError(f"{key} 存在未登记的同名资源，已停止以免复用错误对象。")
            expected_id = self.state.get("pending_id")
            if expected_id and get_id(current, *id_keys) != expected_id:
                raise SetupError(f"{key} 的回读 ID 与上次成功响应不同。")
        else:
            if pending and (not self.retry_pending or self.state.get("pending_id")):
                raise SetupError(f"上一次创建 {key} 后未收到明确结果。复查同名资源，"
                                 "只有确认未创建才使用 --retry-pending。")
            self.state["pending"] = key
            write_state(self.path, self.state)
            created = create()
            # A success response can identify a write while folder/table listings are still catching up.
            created_id = get_id(created, *id_keys)
            self.state["pending_id"] = created_id
            write_state(self.path, self.state)
            current = find()
            if current is None or get_id(current, *id_keys) != created_id:
                raise SetupError(f"{key} 尚未通过回读。可稍后重跑，脚本会先重新查询。")
        self.state["resources"][key] = {"id": get_id(current, *id_keys)}
        if "node_token" in current:
            self.state["resources"][key]["node_token"] = get_id(current, "node_token")
        if isinstance(current.get("url"), str) and current["url"].startswith("https://"):
            self.state["resources"][key]["url"] = current["url"]
        self.state.pop("pending", None)
        self.state.pop("pending_id", None)
        write_state(self.path, self.state)
        return self.state["resources"][key]["id"]

    def verify_fields(self, base, table_id, expected):
        rows = self.lark.base_rows("+field-list", "fields", "--base-token", base,
                                   "--table-id", table_id)
        actual = {row.get("name", row.get("field_name")): row for row in rows}
        field_ids = {}
        for field in expected:
            name = field["name"]
            observed = actual.get(name)
            if observed is None or observed.get("type") != field["type"]:
                raise SetupError(f"表结构不匹配，缺少正确类型的字段「{name}」。")
            if field.get("style", {}).get("type") == "url":
                if (observed.get("style") or {}).get("type") != "url":
                    raise SetupError(f"字段「{name}」不是链接。")
            if "options" in field:
                required = {option["name"] for option in field["options"]}
                received = {option.get("name") for option in observed.get("options", [])}
                if observed.get("multiple") or not required <= received:
                    raise SetupError(f"字段「{name}」缺少预期的单选选项。")
            field_ids[name] = get_id(observed, "field_id", "id")
        return field_ids

    def run(self, schema, contents):
        lark = self.lark
        folder_name = self.state["folder_name"]
        tables = schema["tables"]
        first_key = "showcases"
        first = tables[first_key]
        base_name = schema["base_name"]
        wiki = self.state.get("wiki")
        if wiki:
            def create_node(parent, title, kind):
                return lark.call("wiki", "+node-create", "--space-id", wiki["space_id"],
                                 "--parent-node-token", parent, "--title", title,
                                 "--obj-type", kind)

            parent = wiki["node_token"]
            folder = self.ensure(
                "wiki_project", lambda: wiki_match(lark, wiki, parent, folder_name, "docx"),
                lambda: create_node(parent, folder_name, "docx"), ("node_token",),
            )
            base = self.ensure(
                "base", lambda: wiki_match(lark, wiki, folder, base_name, "bitable"),
                lambda: create_node(folder, base_name, "bitable"), ("obj_token",),
            )
        else:
            folder = self.ensure(
                "folder", lambda: matching(lark.files(), folder_name, "folder"),
                lambda: lark.call("drive", "+create-folder", "--name", folder_name),
                ("folder_token", "token"),
            )
            base = self.ensure(
                "base", lambda: matching(lark.files(folder), base_name, "bitable"),
                lambda: lark.call("base", "+base-create", "--name", base_name,
                                  "--folder-token", folder, "--time-zone", self.state["timezone"],
                                  "--table-name", first["name"], "--fields",
                                  json.dumps(first["fields"], ensure_ascii=False)).get("base"),
                ("base_token", "app_token", "token"),
            )
        for key, table in tables.items():
            lookup = lambda: matching(
                lark.base_rows("+table-list", "tables", "--base-token", base), table["name"]
            )
            resource = f"table.{key}"
            if not wiki and key == first_key and resource not in self.state["resources"]:
                if not self.apply or self.state.get("pending") == resource:
                    raise SetupError("Showcase 状态未登记。")
                row = lookup()
                if row is None:
                    raise SetupError("Base 存在，但首表未成功创建。请在项目 Base 内核查后恢复。")
                field_ids = self.verify_fields(base, get_id(row, "table_id", "id"), table["fields"])
                self.state["resources"][resource] = {
                    "id": get_id(row, "table_id", "id"), "fields": field_ids,
                }
                write_state(self.path, self.state)
            table_id = self.ensure(
                resource, lookup,
                lambda: lark.call("base", "+table-create", "--base-token", base,
                                  "--name", table["name"], "--fields",
                                  json.dumps(table["fields"], ensure_ascii=False)).get("table"),
                ("table_id", "id"),
            )
            field_ids = self.verify_fields(base, table_id, table["fields"])
            saved = self.state["resources"][resource]
            if saved.get("fields") is not None and saved["fields"] != field_ids:
                raise SetupError(f"{table['name']} 字段映射有变化，请核对项目 Base。")
            if self.apply and "fields" not in saved:
                saved["fields"] = field_ids
                write_state(self.path, self.state)
        names = {row.get("name", row.get("table_name")) for row in
                 lark.base_rows("+table-list", "tables", "--base-token", base)}
        expected_names = {table["name"] for table in tables.values()}
        if not expected_names <= names or (not wiki and not self.state.get("ready")
                                          and names != expected_names):
            raise SetupError("Base 回读表结构不符，请核查是否有多余的初始默认表。")

        for key, doc in schema["documents"].items():
            title = doc["title"]
            doc_id = self.ensure(
                f"doc.{key}", lambda: (wiki_match(lark, wiki, folder, title, "docx") if wiki
                                      else matching(lark.files(folder), title, "docx")),
                lambda: lark.call("docs", "+create", "--title", title,
                                  "--parent-token", folder, "--doc-format", "markdown",
                                  "--content", "-", content=contents[key]).get("document"),
                ("document_id", "obj_token", "token"),
            )
            result = lark.call("docs", "+fetch", "--doc", doc_id, "--doc-format", "markdown")
            document = result.get("document")
            if (get_id(document, "document_id") != doc_id or
                    not isinstance(document.get("content"), str) or not document["content"].strip()):
                raise SetupError(f"文档「{title}」未通过内容回读。")
        if self.apply and not self.state.get("ready"):
            self.state["ready"] = True
            write_state(self.path, self.state)


def flag(args, name):
    values = []
    for index, arg in enumerate(args):
        if arg == name:
            if index + 1 >= len(args):
                raise SetupError(f"{name} 缺少参数。")
            values.append(args[index + 1])
        elif arg.startswith(name + "="):
            values.append(arg.split("=", 1)[1])
    if len(values) != 1:
        raise SetupError(f"{name} 必须指定一次。")
    return values[0]


def forbid_flags(args, *names):
    if any(arg == name or arg.startswith(name + "=") for name in names for arg in args):
        raise SetupError("该飞书命令包含受限制的参数。")


def run_lark(lark, args, state):
    forbid_flags(args, "--profile", "--as", "--yes", "--")
    command = tuple(args[:2])
    if command in BOOTSTRAP_COMMANDS:
        if command in {("config", "init"), ("profile", "add")}:
            forbid_flags(args, "--name", "--use")
            if lark.directory.exists() and (lark.directory / "config.json").exists():
                raise SetupError("此项目已有飞书配置。需要重做时请先检查项目本地配置和状态。")
            if command == ("config", "init") and args[2:] != ["--new"]:
                raise SetupError("config init 使用 --new。手工建应用后使用 profile add。")
            if command == ("profile", "add"):
                if "--app-secret-stdin" not in args or not APP_ID.fullmatch(flag(args, "--app-id")):
                    raise SetupError("profile add 需要新应用的 --app-id 与 --app-secret-stdin。")
            args = [*args, "--name", lark.profile]
        return subprocess.run(lark.argv(args), env=lark.env, check=False).returncode

    if not state or state.get("pending") or not state.get("ready"):
        raise SetupError("项目的飞书工作区尚未完成配置。")
    binding = state["binding"]
    if lark.identity(binding["app_id"], binding["brand"], binding["tenant_key"]) != binding:
        raise SetupError("当前飞书授权人与配置时不同。")
    resources = state["resources"]
    wiki = state.get("wiki")
    if wiki:
        folder = resources["wiki_project"]["id"]
        if not any(row.get("node_token") == folder and row.get("node_type") == "origin"
                   for row in lark.wiki_rows(wiki, wiki["node_token"])):
            raise SetupError("项目页已不在绑定的 Wiki 位置。")
    else:
        folder = resources["folder"]["id"]
    if command[0:1] == ("base",) and len(command) == 2 and command[1] in BASE_COMMANDS:
        table_ids = {value["id"] for key, value in resources.items() if key.startswith("table.")}
        if (flag(args, "--base-token") != resources["base"]["id"] or
                flag(args, "--table-id") not in table_ids):
            raise SetupError("Base 或数据表超出当前项目。")
        if wiki and not any(row.get("obj_token") == resources["base"]["id"] and
                            row.get("node_token") == resources["base"]["node_token"] and
                            row.get("node_type") == "origin"
                            for row in lark.wiki_rows(wiki, folder)):
            raise SetupError("Base 已不在绑定的 Wiki 项目页下。")
    elif command == ("docs", "+create"):
        forbid_flags(args, "--parent-position")
        if flag(args, "--parent-token") != folder:
            raise SetupError("文档目标目录超出当前项目。")
    elif command in {("docs", "+fetch"), ("docs", "+update")}:
        doc_id = flag(args, "--doc")
        if wiki:
            allowed = any(row.get("obj_type") == "docx" and row.get("node_type") == "origin"
                          and row.get("obj_token") == doc_id for row in lark.wiki_rows(wiki, folder))
        else:
            allowed = any(row.get("type") == "docx" and row.get("token") == doc_id
                          for row in lark.files(folder))
        if not allowed:
            raise SetupError("文档不属于当前项目目录。请传入文档 ID。")
        if command == ("docs", "+update"):
            if flag(args, "--command") not in {"append", "str_replace", "block_insert_after"}:
                raise SetupError("运营文档只允许追加、插入或定点文字修改。")
    else:
        raise SetupError("该命令超出项目允许的飞书操作。")
    return subprocess.run(lark.argv([*args, "--as", "user"]), env=lark.env, check=False).returncode


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="project slug, e.g. my-product")
    parser.add_argument("--project-name", help="display name for the new folder")
    parser.add_argument("--brief", type=Path, help="Markdown to upload to the new tenant")
    parser.add_argument("--timezone")
    parser.add_argument("--brand", choices=("feishu", "lark"), default="feishu")
    parser.add_argument("--app-id", help="dedicated app ID")
    parser.add_argument("--tenant-key", help="independently confirmed target tenant key")
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument("--wiki-parent", help="authorized Wiki page URL or node ID")
    destination.add_argument("--drive", action="store_true", help="explicitly use a Drive folder")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="create missing Feishu resources")
    mode.add_argument("--verify", action="store_true", help="verify saved resources without remote writes")
    mode.add_argument("--identity", action="store_true", help="read identity from isolated profile")
    mode.add_argument("--lark", nargs=argparse.REMAINDER, help="run a project-scoped lark-cli command")
    parser.add_argument("--retry-pending", action="store_true",
                        help="retry only after verifying the earlier write never happened")
    args = parser.parse_args()
    if not SLUG.fullmatch(args.project) or len(args.project) > 40:
        parser.error("--project needs a lower-case slug of at most 40 characters")
    if args.retry_pending and not args.apply:
        parser.error("--retry-pending requires --apply")
    if args.apply or args.identity:
        if not APP_ID.fullmatch(args.app_id or ""):
            parser.error("--app-id must be the dedicated application ID")
    if args.apply and not TOKEN.fullmatch(args.tenant_key or ""):
        parser.error("--tenant-key must be independently confirmed before --apply")
    try:
        ZoneInfo(args.timezone or "Asia/Shanghai")
    except (ZoneInfoNotFoundError, ValueError):
        parser.error("--timezone must be an IANA time zone available on this host")
    return args


def main(args, root=ROOT):
    directory = local_path(root, ".project")
    state_path = local_path(directory, "feishu.json")
    schema = read_json(root / "schema" / "feishu.json")
    lark = Lark(directory, args.project)
    display = (args.project_name or args.project).strip()
    if not display or len(display) > 80 or any(ord(char) < 32 for char in display):
        raise SetupError("项目显示名需为 1 至 80 个可见字符。")
    if not (args.apply or args.verify or args.identity or args.lark is not None):
        print(json.dumps({
            "mode": "offline-plan", "project": args.project, "display_name": display,
            "profile": lark.profile, "config_directory": ".project/lark-cli",
            "state": ".project/feishu.json",
            "timezone": (args.timezone or "Asia/Shanghai") if args.drive else None,
            "destination": "drive" if args.drive else "wiki",
            "schema": schema, "brief_supplied": bool(args.brief),
        }, ensure_ascii=False, indent=2))
        return 0

    with local_lock(directory):
        project_path = local_path(directory, "project.json")
        if project_path.is_file() and read_json(project_path).get("slug") != args.project:
            raise SetupError("--project 与 .project/project.json 的项目编号不一致。")
        state = read_json(state_path) if state_path.is_file() else None
        if state is not None and (state.get("project"), state.get("schema_version")) != (
                args.project, schema["version"]):
            raise SetupError("当前副本的项目编号或飞书结构版本不同。请使用正确的项目副本。")
        if args.lark is not None:
            return run_lark(lark, args.lark, state)
        if args.identity:
            print(json.dumps(lark.identity(args.app_id, args.brand), ensure_ascii=False))
            return 0

        if args.apply:
            binding = lark.identity(args.app_id, args.brand, args.tenant_key)
        elif state and state.get("ready") and not state.get("pending"):
            saved = state["binding"]
            binding = lark.identity(saved["app_id"], saved["brand"], saved["tenant_key"])
        else:
            raise SetupError("项目的飞书工作区尚未完成配置。")
        if state is not None and binding != state["binding"]:
            raise SetupError("飞书授权与已保存的项目绑定不同。")

        requested_wiki = wiki_token(args.wiki_parent) if args.wiki_parent else None
        wiki = state.get("wiki") if state else None
        if state:
            if ((requested_wiki and (not wiki or requested_wiki != wiki["node_token"]))
                    or (wiki and args.drive)):
                raise SetupError("目标 Wiki 与已绑定的项目位置不同。")
            if wiki and wiki_target(lark, wiki["node_token"]) != wiki:
                raise SetupError("目标 Wiki 已变化。请核对后继续。")
        elif requested_wiki:
            wiki = wiki_target(lark, requested_wiki)
        elif not args.drive:
            raise SetupError("请先确认目标 Wiki，再用 --wiki-parent 提供它的页面链接或节点 ID。")
        if wiki and args.timezone:
            raise SetupError("Wiki 原生 Base 使用飞书默认时区；--timezone 仅用于云盘模式。")

        contents = {}
        if args.apply:
            brief = args.brief or directory / "brief.md"
            if not brief.is_file():
                raise SetupError("缺少已核准上传的产品简介。请提供 --brief 或 .project/brief.md。")
            for key, doc in schema["documents"].items():
                source = root / doc["template"] if "template" in doc else brief
                contents[key] = source.read_text(encoding="utf-8")
                if not contents[key].strip():
                    raise SetupError(f"飞书文档「{doc['title']}」没有正文。")
            if state is not None and args.project_name and display != state["display_name"]:
                raise SetupError("项目显示名与已有飞书绑定不同。")
        if state is not None and args.timezone and args.timezone != state["timezone"]:
            raise SetupError("时区与已配置项目不同。")
        if state is None:
            state = {"project": args.project, "display_name": display,
                     "schema_version": schema["version"], "timezone": args.timezone or "Asia/Shanghai",
                     "folder_name": f"{display} · 内容获客 · {secrets.token_hex(4)}",
                     "binding": binding, "resources": {}, "ready": False}
            if wiki:
                state["wiki"] = wiki
            write_state(state_path, state)
        Provision(lark, state_path, state, args.apply, args.retry_pending).run(schema, contents)
        print(json.dumps({
            "status": "ready", "project": args.project, "profile": lark.profile,
            "state": ".project/feishu.json", "mode": "apply" if args.apply else "verify",
        }, ensure_ascii=False))
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main(parse_args()))
    except (SetupError, OSError, ValueError) as exc:
        print(f"飞书配置停止。{exc}", file=sys.stderr)
        sys.exit(1)
