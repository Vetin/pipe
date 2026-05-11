import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "pipeline-lab/showcases/scripts/run_init_profile_showcases.py"


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class InitProfileShowcaseTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="init-profile-showcase-test-"))
        self.repo_a = self.make_repo("survey-app", "Signed Webhooks", "webhook_service.py")
        self.repo_b = self.make_repo("crm-app", "Company Merge", "merge_service.py")
        self.config = self.tempdir / "cases.yaml"
        self.output_dir = self.tempdir / "runs"
        self.report = self.tempdir / "report.md"
        self.config.write_text(
            f"""artifact_contract_version: '0.1.0'
cases:
  survey-webhooks:
    title: Survey Webhooks
    original_codebase:
      repo_path: {self.repo_a}
    feature_request: Sign webhook payloads.
    expected_result: Delivery logs and retries.
  company-merge:
    title: Company Merge
    original_codebase:
      repo_path: {self.repo_b}
    feature_request: Merge duplicate companies.
    expected_result: Audit trail and rollback.
""",
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def make_repo(self, name, feature, service_file):
        repo = self.tempdir / name
        repo.mkdir()
        run(["git", "init", "-b", "main"], repo)
        run(["git", "config", "user.email", "test@example.com"], repo)
        run(["git", "config", "user.name", "Test User"], repo)
        (repo / "package.json").write_text(f'{{"name": "{name}", "scripts": {{"test": "pytest"}}}}', encoding="utf-8")
        (repo / "docs").mkdir()
        (repo / "docs/features.md").write_text(f"# Feature: {feature}\n", encoding="utf-8")
        (repo / "src").mkdir()
        (repo / "src" / service_file).write_text("export function runFeature() { return true; }\n", encoding="utf-8")
        (repo / "tests").mkdir()
        (repo / "tests" / f"test_{service_file}").write_text("def test_feature(): pass\n", encoding="utf-8")
        run(["git", "add", "."], repo)
        run(["git", "commit", "-m", "seed"], repo)
        return repo

    def test_runner_profiles_repositories_three_times_and_compares_outputs(self):
        result = run(
            [
                sys.executable,
                str(RUNNER),
                "--cases",
                str(self.config),
                "--output-dir",
                str(self.output_dir),
                "--report",
                str(self.report),
                "--run-id",
                "stable-test",
                "--passes",
                "3",
                "--clean",
            ],
            ROOT,
        )

        self.assertIn("failures: 0", result.stdout)
        summary = yaml.safe_load((self.output_dir / "stable-test/summary.yaml").read_text(encoding="utf-8"))
        self.assertEqual(summary["passes"], 3)
        self.assertEqual(len(summary["results"]), 6)
        self.assertFalse(summary["failures"])
        self.assertTrue(all(item["stable_metrics"] for item in summary["comparisons"]))
        report = self.report.read_text(encoding="utf-8")
        self.assertIn("Init Profile Showcase Validation", report)
        self.assertIn("Side By Side", report)
        self.assertIn("Current Feature Picture", report)


if __name__ == "__main__":
    unittest.main()
