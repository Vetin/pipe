import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEBUG_RUNNER = ROOT / "pipeline-lab/showcases/scripts/run_codex_debug_pipeline.py"


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class CodexDebugRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="codex-debug-test-"))
        self.repo = self.make_repo()
        self.config = self.write_case_config()
        self.output_dir = self.tempdir / "debug-runs"

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def make_repo(self):
        repo = self.tempdir / "toy-repo"
        repo.mkdir()
        run(["git", "init", "-b", "main"], repo)
        run(["git", "config", "user.email", "test@example.com"], repo)
        run(["git", "config", "user.name", "Test User"], repo)
        (repo / "README.md").write_text("# Toy Repo\n", encoding="utf-8")
        run(["git", "add", "."], repo)
        run(["git", "commit", "-m", "seed"], repo)
        return repo

    def write_case_config(self):
        config = self.tempdir / "cases.yaml"
        config.write_text(
            yaml.safe_dump(
                {
                    "artifact_contract_version": "0.1.0",
                    "cases": {
                        "toy-feature": {
                            "title": "Toy Feature",
                            "domain": "toy",
                            "original_codebase": {
                                "repo_path": "toy-repo",
                                "base_ref": "HEAD",
                            },
                            "target_branch": "nfp/toy-feature",
                            "feature_request": "Add a stable greeting feature to the toy repository.",
                            "expected_result": "Artifacts, implementation notes, tests, and final summary are produced.",
                        }
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        return config

    def test_mock_mode_runs_nested_e2e_and_validates_artifacts(self):
        result = run(
            [
                sys.executable,
                str(DEBUG_RUNNER),
                "--config",
                str(self.config),
                "--case",
                "toy-feature",
                "--run-id",
                "stable-debug",
                "--output-dir",
                str(self.output_dir),
                "--mode",
                "mock",
                "--clean",
            ],
            ROOT,
        )

        run_dir = self.output_dir / "stable-debug"
        summary = yaml.safe_load((run_dir / "summary.yaml").read_text(encoding="utf-8"))
        validation = (run_dir / "validation.md").read_text(encoding="utf-8")
        comparison = (run_dir / "comparison.md").read_text(encoding="utf-8")
        e2e_run = yaml.safe_load((run_dir / "e2e/toy-feature/stable-debug/run.yaml").read_text(encoding="utf-8"))
        repo = Path(e2e_run["repo"])

        self.assertIn("status: pass", result.stdout)
        self.assertEqual(summary["mode"], "mock")
        self.assertFalse(summary["uses_real_codex"])
        self.assertEqual(summary["status"], "pass")
        self.assertEqual(summary["case_count"], 1)
        self.assertTrue(summary["comparison"]["current_unit_tests_use_fake_codex"])
        self.assertEqual(e2e_run["execution_mode"], "mock")
        self.assertFalse(e2e_run["uses_real_codex"])
        self.assertTrue((repo / ".ai/feature-workspaces/debug/toy-feature/feature.md").exists())
        self.assertTrue((repo / ".ai/feature-workspaces/debug/toy-feature/architecture.md").exists())
        self.assertIn("0 | `pass`", validation)
        self.assertIn("Uses fake Codex: `true`", comparison)
        self.assertIn("explicit execution_mode", comparison)

    def test_real_mode_fails_fast_when_codex_binary_is_missing(self):
        result = run(
            [
                sys.executable,
                str(DEBUG_RUNNER),
                "--config",
                str(self.config),
                "--case",
                "toy-feature",
                "--run-id",
                "missing-real",
                "--output-dir",
                str(self.output_dir),
                "--mode",
                "real",
                "--codex-bin",
                str(self.tempdir / "missing-codex"),
                "--clean",
            ],
            ROOT,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("real Codex executable is missing", result.stderr)
        self.assertFalse((self.output_dir / "missing-real/summary.yaml").exists())


if __name__ == "__main__":
    unittest.main()
