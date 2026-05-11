import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


SCRIPT = Path(__file__).resolve().parents[2] / ".agents/pipeline-core/scripts/featurectl.py"


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class FeatureCtlCoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="featurectl-test-"))
        self.repo = self.make_repo()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def make_repo(self):
        repo = self.tempdir / "repo"
        repo.mkdir()
        run(["git", "init", "-b", "main"], repo)
        run(["git", "config", "user.email", "test@example.com"], repo)
        run(["git", "config", "user.name", "Test User"], repo)
        (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
        run(["git", "add", "README.md"], repo)
        run(["git", "commit", "-m", "initial"], repo)
        return repo

    def test_init_creates_base_structure_idempotently(self):
        result = run([sys.executable, str(SCRIPT), "init"], self.repo)
        second = run([sys.executable, str(SCRIPT), "init"], self.repo)

        self.assertIn("initialized", result.stdout)
        self.assertIn("initialized", second.stdout)
        self.assertTrue((self.repo / ".ai/features/index.yaml").exists())
        self.assertTrue((self.repo / ".agents/pipeline-core/scripts/schemas").is_dir())
        self.assertTrue((self.repo / ".agents/pipeline-core/references/generated-templates").is_dir())
        self.assertTrue((self.repo / ".agents/skills").is_dir())
        self.assertTrue((self.repo / "methodology/extracted").is_dir())
        self.assertFalse(list(self.repo.rglob("approvals.yaml")))
        self.assertFalse(list(self.repo.rglob("handoff.md")))

    def test_init_outside_git_fails_clearly(self):
        outside = self.tempdir / "outside"
        outside.mkdir()

        result = run([sys.executable, str(SCRIPT), "init"], outside, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be run inside a git repository", result.stderr)

    def test_new_creates_worktree_workspace_and_core_artifacts(self):
        result = self.new_feature("run-20260511-test")

        workspace = self.workspace("run-20260511-test")
        self.assertIn("feature_key: auth/reset-password", result.stdout)
        self.assertTrue((self.tempdir / "worktrees/auth-reset-password-run-20260511-test").is_dir())
        self.assertTrue(workspace.is_dir())
        self.assertTrue((workspace / "apex.md").exists())
        self.assertTrue((workspace / "feature.yaml").exists())
        self.assertTrue((workspace / "state.yaml").exists())
        self.assertTrue((workspace / "execution.md").exists())
        self.assertFalse(list(workspace.rglob("approvals.yaml")))
        self.assertFalse(list(workspace.rglob("handoff.md")))

        feature = yaml.safe_load((workspace / "feature.yaml").read_text(encoding="utf-8"))
        state = yaml.safe_load((workspace / "state.yaml").read_text(encoding="utf-8"))
        self.assertEqual(feature["artifact_contract_version"], "0.1.0")
        self.assertEqual(feature["feature_key"], "auth/reset-password")
        self.assertEqual(feature["domain"], "auth")
        self.assertEqual(feature["slug"], "reset-password")
        self.assertEqual(feature["title"], "Reset Password")
        self.assertEqual(feature["status"], "draft")
        self.assertEqual(feature["branch"], "feature/auth-reset-password-run-20260511-test")
        self.assertEqual(feature["canonical_path"], ".ai/features/auth/reset-password")
        self.assertEqual(feature["workspace_path"], ".ai/feature-workspaces/auth/reset-password--run-20260511-test")
        self.assertEqual(state["current_step"], "context")
        self.assertNotIn("next_skill", state)
        self.assertEqual(state["gates"]["implementation"], "blocked")

        main_branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], self.repo)
        feature_branch = run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            self.tempdir / "worktrees/auth-reset-password-run-20260511-test",
        )
        self.assertEqual(main_branch.stdout.strip(), "main")
        self.assertEqual(feature_branch.stdout.strip(), "feature/auth-reset-password-run-20260511-test")

    def test_new_duplicate_run_id_fails_before_workspace_creation(self):
        self.new_feature("run-20260511-dupe")

        result = self.new_feature("run-20260511-dupe", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("worktree path already exists", result.stderr)

    def test_status_reports_state_and_blockers(self):
        self.new_feature("run-20260511-stat")
        workspace = "../worktrees/auth-reset-password-run-20260511-stat/.ai/feature-workspaces/auth/reset-password--run-20260511-stat"

        result = run([sys.executable, str(SCRIPT), "status", "--workspace", workspace], self.repo)

        self.assertIn("feature_key: auth/reset-password", result.stdout)
        self.assertIn("current_step: context", result.stdout)
        self.assertIn("implementation: blocked", result.stdout)
        self.assertIn("blocking_issues:\n  none", result.stdout)
        self.assertIn("next_step: nfp-01-context", result.stdout)

    def test_status_reports_missing_required_file(self):
        self.new_feature("run-20260511-missing")
        workspace = self.workspace("run-20260511-missing")
        (workspace / "apex.md").unlink()

        result = run([sys.executable, str(SCRIPT), "status", "--workspace", str(workspace)], self.repo)

        self.assertIn("missing apex.md", result.stdout)

    def new_feature(self, run_id, check=True):
        return run(
            [
                sys.executable,
                str(SCRIPT),
                "new",
                "--domain",
                "auth",
                "--title",
                "Reset Password",
                "--run-id",
                run_id,
            ],
            self.repo,
            check=check,
        )

    def workspace(self, run_id):
        return self.tempdir / f"worktrees/auth-reset-password-{run_id}/.ai/feature-workspaces/auth/reset-password--{run_id}"


if __name__ == "__main__":
    unittest.main()
