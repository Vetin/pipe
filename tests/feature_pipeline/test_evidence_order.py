import shutil
import tempfile
import unittest
from pathlib import Path

try:
    from plan_test_helpers import FEATURECTL, approve_planning, create_workspace, make_repo, record_full_evidence, run, write_planning_artifacts
except ModuleNotFoundError:
    from tests.feature_pipeline.plan_test_helpers import FEATURECTL, approve_planning, create_workspace, make_repo, record_full_evidence, run, write_planning_artifacts


class EvidenceOrderTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="evidence-order-test-"))
        self.repo = make_repo(self.tempdir)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_complete_slice_rejects_green_before_red(self):
        workspace = create_workspace(self.tempdir, self.repo, run_id="run-evidence-order")
        write_planning_artifacts(workspace)
        approve_planning(workspace, current_step="tdd_implementation")
        record_full_evidence(
            self.repo,
            workspace,
            red_ts="2026-05-11T10:00:00Z",
            green_ts="2026-05-11T09:00:00Z",
        )

        result = run(
            [
                "python",
                str(FEATURECTL),
                "complete-slice",
                "--workspace",
                str(workspace),
                "--slice",
                "S-001",
                "--diff-hash",
                "abc123",
            ],
            self.repo,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("red evidence timestamp must be before green", result.stdout)


if __name__ == "__main__":
    unittest.main()
