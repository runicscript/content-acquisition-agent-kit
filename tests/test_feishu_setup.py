import copy
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts import feishu_setup as setup


class FakeLark:
    def __init__(self, schema):
        self.profile = "acq-demo"
        self.schema = schema
        self.root = []
        self.children = []
        self.tables = {}
        self.writes = []
        self.timeout_after_create = None
        self.tenant = "target_tenant"
        self.user = "ou_fixture"

    def identity(self, app_id, brand, tenant_key=None):
        if tenant_key and tenant_key != self.tenant:
            raise setup.SetupError("tenant mismatch")
        return {"profile": self.profile, "app_id": app_id, "brand": brand,
                "tenant_key": self.tenant, "open_id": self.user}

    def files(self, parent=""):
        return copy.deepcopy(self.children if parent else self.root)

    def base_rows(self, shortcut, key, *args):
        if shortcut == "+table-list":
            return [{"id": table_id, "name": table["name"]} for table_id, table in self.tables.items()]
        fields = self.tables[args[-1]]["fields"]
        return [dict(field, id=f"fld{index}") for index, field in enumerate(fields)]

    def add_table(self, name, fields):
        table_id = f"tbl{len(self.tables)}"
        self.tables[table_id] = {"name": name, "fields": fields}
        return {"id": table_id}

    def call(self, service, command, *args, content=None):
        flags = dict(zip(args[::2], args[1::2]))
        if command == "+fetch":
            return {"document": {"document_id": flags["--doc"], "content": "fixture"}}
        self.writes.append(command)
        if command == "+create-folder":
            self.root.append({"name": flags["--name"], "type": "folder", "token": "fixtureFolder"})
            return {"folder_token": "fixtureFolder"}
        if command == "+base-create":
            self.children.append({"name": flags["--name"], "type": "bitable", "token": "fixtureBase"})
            self.add_table(flags["--table-name"], json.loads(flags["--fields"]))
            return {"base": {"base_token": "fixtureBase"}}
        if command == "+table-create":
            return {"table": self.add_table(flags["--name"], json.loads(flags["--fields"]))}
        if service == "docs" and command == "+create":
            doc_id = f"fixtureDoc{len(self.children)}"
            self.children.append({"name": flags["--title"], "type": "docx", "token": doc_id})
            if self.timeout_after_create == flags["--title"]:
                raise setup.SetupError("timeout")
            return {"document": {"document_id": doc_id}}
        raise AssertionError((service, command))


class FeishuSetupTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.project = self.root / ".project"
        self.project.mkdir()
        (self.project / "project.json").write_text('{"slug": "demo"}', encoding="utf-8")
        (self.project / "brief.md").write_text("fixture project brief", encoding="utf-8")
        self.state = self.project / "feishu.json"
        schema_path = setup.ROOT / "schema" / "feishu.json"
        self.schema = setup.read_json(schema_path)
        (self.root / "schema").mkdir()
        (self.root / "schema" / "feishu.json").write_bytes(schema_path.read_bytes())
        for document in self.schema["documents"].values():
            if "template" in document:
                path = self.root / document["template"]
                path.parent.mkdir(exist_ok=True)
                path.write_text("fixture template", encoding="utf-8")
        self.fake = FakeLark(self.schema)

    def run_setup(self, **overrides):
        params = dict(
            project="demo", project_name="Demo", brief=None, timezone=None, brand="feishu",
            app_id="cli_fixture", tenant_key="target_tenant", apply=True, verify=False,
            identity=False, lark=None, retry_pending=False,
        )
        params.update(overrides)
        with patch.object(setup, "Lark", return_value=self.fake), redirect_stdout(io.StringIO()):
            return setup.main(SimpleNamespace(**params), self.root)

    def test_plan_is_offline_and_does_not_create_state(self):
        self.run_setup(apply=False)
        self.assertEqual(self.fake.writes, [])
        self.assertFalse(self.state.exists())

    def test_provisions_then_verifies_and_reuses_resources(self):
        self.run_setup()
        writes = list(self.fake.writes)
        state = self.state.read_bytes()
        self.assertTrue(setup.read_json(self.state)["ready"])
        self.assertEqual(len(writes), 7)
        self.run_setup()
        self.run_setup(apply=False, verify=True)
        self.assertEqual(self.fake.writes, writes)
        self.assertEqual(self.state.read_bytes(), state)

    def test_tenant_and_user_mismatch_stop_before_write(self):
        self.fake.tenant = "wrong_tenant"
        with self.assertRaisesRegex(setup.SetupError, "tenant mismatch"):
            self.run_setup()
        self.assertEqual(self.fake.writes, [])
        self.assertFalse(self.state.exists())
        self.fake.tenant = "target_tenant"
        self.run_setup()
        self.fake.user = "ou_different"
        with self.assertRaisesRegex(setup.SetupError, "项目绑定"):
            self.run_setup(apply=False, verify=True)
        self.assertEqual(len(self.fake.writes), 7)

    def test_reconciles_timeout_after_remote_creation(self):
        self.fake.timeout_after_create = self.schema["documents"]["brief"]["title"]
        with self.assertRaisesRegex(setup.SetupError, "timeout"):
            self.run_setup()
        self.assertEqual(setup.read_json(self.state)["pending"], "doc.brief")
        self.run_setup()
        self.assertTrue(setup.read_json(self.state)["ready"])
        self.assertEqual(len(self.fake.writes), 7)

    def test_does_not_repeat_an_unknown_write_when_resource_is_missing(self):
        with patch.object(self.fake, "call", side_effect=setup.SetupError("timeout")):
            with self.assertRaisesRegex(setup.SetupError, "timeout"):
                self.run_setup()
        self.assertEqual(setup.read_json(self.state)["pending"], "folder")
        with self.assertRaisesRegex(setup.SetupError, "retry-pending"):
            self.run_setup()
        self.assertEqual(self.fake.writes, [])
        self.run_setup(retry_pending=True)
        self.assertTrue(setup.read_json(self.state)["ready"])

    def test_pending_confirmed_id_cannot_be_replaced_or_retried(self):
        self.run_setup()
        state = setup.read_json(self.state)
        state["pending"] = "doc.brief"
        state["pending_id"] = state["resources"].pop("doc.brief")["id"]
        state["ready"] = False
        setup.write_state(self.state, state)
        brief = next(item for item in self.fake.children if item["token"] == state["pending_id"])
        brief["token"] = "unrelatedDoc"
        with self.assertRaisesRegex(setup.SetupError, "回读 ID"):
            self.run_setup()
        self.fake.children.remove(brief)
        with self.assertRaisesRegex(setup.SetupError, "retry-pending"):
            self.run_setup(retry_pending=True)
        self.assertEqual(len(self.fake.writes), 7)

    def test_verify_fails_on_empty_document_readback(self):
        self.run_setup()
        state = self.state.read_bytes()
        with patch.object(self.fake, "call", return_value={
            "document": {"document_id": setup.read_json(self.state)["resources"]["doc.brief"]["id"],
                         "content": " "},
        }):
            with self.assertRaisesRegex(setup.SetupError, "内容回读"):
                self.run_setup(apply=False, verify=True)
        self.assertEqual(self.state.read_bytes(), state)

    def test_live_identity_uses_bound_profile_and_authenticated_tenant(self):
        lark = setup.Lark(self.project, "demo")
        whoami = {"profile": "acq-demo", "appId": "cli_fixture", "brand": "feishu",
                  "identity": "user", "available": True, "onBehalfOf": {"openId": "ou_fixture"}}
        userinfo = {"ok": True, "identity": "user",
                    "data": {"open_id": "ou_fixture", "tenant_key": "target_tenant"}}
        with patch.object(lark, "json", side_effect=[whoami, userinfo]) as call:
            binding = lark.identity("cli_fixture", "feishu", "target_tenant")
            self.assertEqual(binding["open_id"], "ou_fixture")
            self.assertEqual(call.call_args.args[0], [
                "api", "GET", "/open-apis/authen/v1/user_info", "--as", "user", "--format", "json",
            ])
        with patch.object(lark, "json", side_effect=[whoami, userinfo]):
            with self.assertRaisesRegex(setup.SetupError, "租户"):
                lark.identity("cli_fixture", "feishu", "other_tenant")

    def test_project_slug_and_workspace_overrides_are_rejected(self):
        with self.assertRaisesRegex(setup.SetupError, "项目编号"):
            self.run_setup(project="wrong")
        with patch.dict(setup.os.environ, {
            "LARKSUITE_CLI_USER_ACCESS_TOKEN": "unused",
            "LARKSUITE_CLI_PROFILE": "wrong",
            "OPENCLAW_HOME": "other",
            "HERMES_HOME": "other",
            "HERMES_AGENT_ID": "other",
            "LARK_CHANNEL": "other",
        }):
            lark = setup.Lark(self.project, "demo")
        self.assertNotIn("LARKSUITE_CLI_USER_ACCESS_TOKEN", lark.env)
        self.assertNotIn("LARKSUITE_CLI_PROFILE", lark.env)
        self.assertNotIn("OPENCLAW_HOME", lark.env)
        self.assertNotIn("HERMES_HOME", lark.env)
        self.assertNotIn("HERMES_AGENT_ID", lark.env)
        self.assertNotIn("LARK_CHANNEL", lark.env)
        self.assertEqual(lark.env["LARKSUITE_CLI_CONFIG_DIR"], str(self.project / "lark-cli"))
        self.assertEqual(lark.argv(["whoami"])[:3], ["lark-cli", "--profile", "acq-demo"])


if __name__ == "__main__":
    unittest.main()
