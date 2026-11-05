"""Initialize and validate the portable project brief without network access."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
LINE_FIELDS = (
    "id", "product", "audience", "adoption", "action",
    "qualified_lead", "outcome", "scout_evidence",
)


def read_object(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("配置根节点必须为 JSON 对象。")
    return value


def initialize(path, slug, name):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or len(slug) > 40:
        raise ValueError("slug 使用小写英文字母、数字和连字符，最长 40 字符。")
    if not name.strip():
        raise ValueError("项目名不能为空。")
    data = read_object(ROOT / "config" / "project.example.json")
    data.update(slug=slug, name=name.strip())
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False,
    ) as stream:
        draft = Path(stream.name)
    try:
        draft.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.link(draft, path)
    except FileExistsError:
        existing = read_object(path)
        if existing.get("slug") != slug:
            raise ValueError("工作目录已有其他项目，请使用独立目录。") from None
        print(f"保留已有项目配置 {path}")
    else:
        print(f"已创建项目配置 {path}")
    finally:
        draft.unlink()


def filled_text(value):
    return isinstance(value, str) and bool(value.strip())


def inspect_brief(data):
    if data.get("schema_version") != 1:
        raise ValueError("不支持该项目配置版本。")
    missing = [key for key in ("slug", "name") if not filled_text(data.get(key))]
    product = data.get("product")
    if not isinstance(product, dict):
        product = {}
    missing.extend(f"product.{key}" for key in ("summary", "source") if not filled_text(product.get(key)))
    platforms = data.get("platforms")
    if not isinstance(platforms, list) or not platforms or not all(map(filled_text, platforms)):
        missing.append("platforms")
    lines = data.get("promotion_lines")
    if not isinstance(lines, list) or not lines:
        missing.append("promotion_lines")
    else:
        line_ids = set()
        for index, line in enumerate(lines):
            if not isinstance(line, dict):
                missing.append(f"promotion_lines[{index}]")
                continue
            for key in LINE_FIELDS:
                if not filled_text(line.get(key)):
                    missing.append(f"promotion_lines[{index}].{key}")
            line_id = line.get("id")
            if filled_text(line_id):
                if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", line_id) or line_id in line_ids:
                    missing.append(f"promotion_lines[{index}].id (需为唯一的小写英文标识)")
                line_ids.add(line_id)
    workflow = data.get("workflow")
    if not isinstance(workflow, dict) or workflow.get("storage") not in ("feishu", "local"):
        missing.append("workflow.storage")
    else:
        missing.extend(
            f"workflow.{key}" for key in ("video", "recurring")
            if not isinstance(workflow.get(key), bool)
        )
    return {
        "brief_ready": not missing,
        "missing": missing,
        "lark_cli_installed": shutil.which("lark-cli") is not None,
        "remote_verified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=ROOT / ".project",
                        help="项目专用配置目录，默认 .project")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--slug", required=True)
    init.add_argument("--name", required=True)
    commands.add_parser("doctor")
    args = parser.parse_args()
    path = args.directory / "project.json"
    try:
        if args.command == "init":
            initialize(path, args.slug, args.name)
        else:
            print(json.dumps(inspect_brief(read_object(path)), ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        print(f"项目配置失败。{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
