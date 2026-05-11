import shutil
import tempfile
import unittest
from pathlib import Path

try:
    from plan_test_helpers import create_workspace, load_yaml, make_repo, run
except ModuleNotFoundError:
    from tests.feature_pipeline.plan_test_helpers import create_workspace, load_yaml, make_repo, run


class WorkspaceCreationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="workspace-creation-test-"))
        self.repo = make_repo(self.tempdir)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_new_feature_creates_worktree_and_core_artifacts_inside_it(self):
        workspace = create_workspace(self.tempdir, self.repo, run_id="run-workspace")
        state = load_yaml(workspace / "state.yaml")
        worktree = self.tempdir / "worktrees/auth-reset-password-run-workspace"

        self.assertTrue(worktree.is_dir())
        self.assertTrue(str(workspace).startswith(str(worktree)))
        for artifact in ("apex.md", "feature.yaml", "state.yaml", "execution.md"):
            self.assertTrue((workspace / artifact).exists(), artifact)

        branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], worktree).stdout.strip()
        self.assertEqual(branch, state["worktree"]["branch"])


if __name__ == "__main__":
    unittest.main()
