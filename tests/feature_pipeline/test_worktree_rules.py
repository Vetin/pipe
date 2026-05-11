import shutil
import tempfile
import unittest
from pathlib import Path

try:
    from plan_test_helpers import FEATURECTL, approve_planning, create_workspace, make_repo, run, write_planning_artifacts
except ModuleNotFoundError:
    from tests.feature_pipeline.plan_test_helpers import FEATURECTL, approve_planning, create_workspace, make_repo, run, write_planning_artifacts


class WorktreeRulesTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="worktree-rules-test-"))
        self.repo = make_repo(self.tempdir)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_implementation_status_fails_from_main_checkout(self):
        workspace = create_workspace(self.tempdir, self.repo, run_id="run-worktree-rules")
        write_planning_artifacts(workspace)
        approve_planning(workspace, current_step="worktree")

        result = run(["python", str(FEATURECTL), "worktree-status", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("current checkout is not configured feature worktree", result.stdout)


if __name__ == "__main__":
    unittest.main()
