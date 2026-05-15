import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

try:
    from test_planning_readiness import write_planning_artifacts
except ModuleNotFoundError:
    from tests.feature_pipeline.test_planning_readiness import write_planning_artifacts


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".agents/pipeline-core/scripts/featurectl.py"


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class WorktreeStatusTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="worktree-status-test-"))
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

    def test_wrong_worktree_blocks_implementation(self):
        workspace = self.ready_workspace()

        result = run([sys.executable, str(SCRIPT), "worktree-status", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("worktree_status: fail", result.stdout)
        self.assertIn("current checkout is not configured feature worktree", result.stdout)

    def test_worktree_status_passes_for_planning_only_feature_worktree(self):
        workspace = self.ready_workspace("run-gate-block", approve=False)
        worktree = self.worktree("run-gate-block")

        result = run([sys.executable, str(SCRIPT), "worktree-status", "--workspace", str(workspace)], worktree)

        self.assertIn("worktree_status: pass", result.stdout)
        self.assertIn("implementation_ready: not_checked", result.stdout)

    def test_implementation_ready_blocks_from_feature_worktree_until_gates_pass(self):
        workspace = self.ready_workspace("run-implementation-ready-block", approve=False)
        worktree = self.worktree("run-implementation-ready-block")

        result = run([sys.executable, str(SCRIPT), "implementation-ready", "--workspace", str(workspace)], worktree, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("implementation_ready: false", result.stdout)
        self.assertIn("implementation requires tech_design gate approved or delegated", result.stdout)

    def test_worktree_status_passes_when_checkout_branch_and_gates_match(self):
        workspace = self.ready_workspace("run-worktree-pass")
        worktree = self.worktree("run-worktree-pass")

        result = run([sys.executable, str(SCRIPT), "worktree-status", "--workspace", str(workspace)], worktree)

        self.assertIn("worktree_status: pass", result.stdout)
        self.assertIn("implementation_ready: not_checked", result.stdout)
        self.assertIn("branch: feature/auth-reset-password-run-worktree-pass", result.stdout)

    def test_implementation_ready_passes_when_checkout_branch_and_gates_match(self):
        workspace = self.ready_workspace("run-implementation-ready-pass")
        worktree = self.worktree("run-implementation-ready-pass")

        result = run([sys.executable, str(SCRIPT), "implementation-ready", "--workspace", str(workspace)], worktree)

        self.assertIn("implementation_ready: true", result.stdout)
        self.assertIn("branch: feature/auth-reset-password-run-implementation-ready-pass", result.stdout)

    def test_implementation_ready_fails_if_slices_invalid_even_when_gates_approved(self):
        workspace = self.ready_workspace("run-implementation-ready-invalid-slices")
        worktree = self.worktree("run-implementation-ready-invalid-slices")
        slices_path = workspace / "slices.yaml"
        slices = yaml.safe_load(slices_path.read_text(encoding="utf-8"))
        slices["slices"][0]["linked_requirements"] = ["FR-999"]
        slices_path.write_text(yaml.safe_dump(slices, sort_keys=False), encoding="utf-8")

        result = run([sys.executable, str(SCRIPT), "implementation-ready", "--workspace", str(workspace)], worktree, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("implementation_ready: false", result.stdout)
        self.assertIn("links unknown requirement FR-999", result.stdout)

    def test_implementation_ready_fails_if_architecture_invalid_even_when_gates_approved(self):
        workspace = self.ready_workspace("run-implementation-ready-invalid-architecture")
        worktree = self.worktree("run-implementation-ready-invalid-architecture")
        architecture_path = workspace / "architecture.md"
        architecture = architecture_path.read_text(encoding="utf-8").replace("## Security Model", "## Security")
        architecture_path.write_text(architecture, encoding="utf-8")

        result = run([sys.executable, str(SCRIPT), "implementation-ready", "--workspace", str(workspace)], worktree, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("implementation_ready: false", result.stdout)
        self.assertIn("architecture.md missing heading: ## Security Model", result.stdout)

    def test_implementation_ready_fails_when_current_checkout_is_not_feature_worktree(self):
        workspace = self.ready_workspace("run-implementation-ready-wrong-checkout")

        result = run([sys.executable, str(SCRIPT), "implementation-ready", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("implementation_ready: false", result.stdout)
        self.assertIn("current checkout is not configured feature worktree", result.stdout)

    def ready_workspace(self, run_id="run-worktree", approve=True):
        run(
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
        )
        workspace = self.tempdir / f"worktrees/auth-reset-password-{run_id}/.ai/feature-workspaces/auth/reset-password--{run_id}"
        write_planning_artifacts(workspace)
        state_path = workspace / "state.yaml"
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        state["current_step"] = "worktree"
        state["gates"]["feature_contract"] = "approved"
        state["gates"]["architecture"] = "approved"
        state["gates"]["tech_design"] = "approved" if approve else "drafted"
        state["gates"]["slicing_readiness"] = "delegated"
        state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
        return workspace

    def worktree(self, run_id):
        return self.tempdir / f"worktrees/auth-reset-password-{run_id}"


if __name__ == "__main__":
    unittest.main()
