import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "project_setup.py"


class ProjectSetupTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.directory = Path(temp.name) / "project"

    def run_setup(self, *arguments):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--directory", str(self.directory), *arguments],
            capture_output=True, text=True, check=True,
        )

    def test_init_never_overwrites_existing_project(self):
        self.run_setup("init", "--slug", "example", "--name", "示例项目")
        config = self.directory / "project.json"
        data = json.loads(config.read_text())
        data["product"]["summary"] = "已确认说明"
        config.write_text(json.dumps(data))
        self.run_setup("init", "--slug", "example", "--name", "示例项目")
        self.assertEqual(json.loads(config.read_text())["product"]["summary"], "已确认说明")
        with self.assertRaises(subprocess.CalledProcessError):
            self.run_setup("init", "--slug", "other", "--name", "另一个项目")

    def test_doctor_reports_missing_project_inputs_without_network(self):
        self.run_setup("init", "--slug", "example", "--name", "示例项目")
        report = json.loads(self.run_setup("doctor").stdout)
        self.assertIn("product.summary", report["missing"])
        self.assertIn("promotion_lines", report["missing"])
        self.assertIn("platforms", report["missing"])
        self.assertFalse(report["brief_ready"])

    def test_reviewed_brief_passes_without_claiming_remote_verification(self):
        self.run_setup("init", "--slug", "example", "--name", "示例项目")
        config = self.directory / "project.json"
        data = json.loads(config.read_text())
        data.update(product={"summary": "演示产品", "source": "负责人提供"},
                    platforms=["小红书"], promotion_lines=[{
                        "id": "self-serve", "product": "演示产品", "audience": "店主", "adoption": "自助",
                        "action": "访问体验页", "qualified_lead": "明确提出体验问题",
                        "outcome": "首次完成演示", "scout_evidence": "可见产品演示",
                    }])
        config.write_text(json.dumps(data))
        report = json.loads(self.run_setup("doctor").stdout)
        self.assertFalse(report["brief_ready"])
        self.assertIn("promotion_lines[0].audience_profile.trigger", report["missing"])

        profile = {"trigger": "客户催确认订单", "signals": ["公开询问如何核对订单"],
                   "exclusions": ["同行只是在发布广告"], "status": "hypothesis"}
        data["promotion_lines"][0]["audience_profile"] = profile
        config.write_text(json.dumps(data))
        report = json.loads(self.run_setup("doctor").stdout)
        self.assertTrue(report["brief_ready"])
        self.assertFalse(report["remote_verified"])

        profile["signals"] = [" "]
        config.write_text(json.dumps(data))
        report = json.loads(self.run_setup("doctor").stdout)
        self.assertIn("promotion_lines[0].audience_profile.signals", report["missing"])
        profile["signals"] = ["公开询问如何核对订单"]

        data["promotion_lines"].append(dict(data["promotion_lines"][0], audience="团队"))
        config.write_text(json.dumps(data))
        report = json.loads(self.run_setup("doctor").stdout)
        self.assertFalse(report["brief_ready"])
        self.assertTrue(any(item.startswith("promotion_lines[1].id") for item in report["missing"]))
