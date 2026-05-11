import shutil
import tempfile
import unittest
from pathlib import Path

try:
    from plan_test_helpers import FEATURECTL, create_workspace, load_yaml, make_repo, run
except ModuleNotFoundError:
    from tests.feature_pipeline.plan_test_helpers import FEATURECTL, create_workspace, load_yaml, make_repo, run


class GateStatusTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="gate-status-test-"))
        self.repo = make_repo(self.tempdir)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_gate_set_accepts_known_status_and_rejects_unknown_status(self):
        workspace = create_workspace(self.tempdir, self.repo, run_id="run-gate-status")

        ok = run(
            [
                "python",
                str(FEATURECTL),
                "gate",
                "set",
                "--workspace",
                str(workspace),
                "--gate",
                "feature_contract",
                "--status",
                "approved",
                "--by",
                "test",
            ],
            self.repo,
        )
        bad = run(
            [
                "python",
                str(FEATURECTL),
                "gate",
                "set",
                "--workspace",
                str(workspace),
                "--gate",
                "feature_contract",
                "--status",
                "auto-approved",
                "--by",
                "test",
            ],
            self.repo,
            check=False,
        )

        self.assertIn("status: approved", ok.stdout)
        self.assertEqual(load_yaml(workspace / "state.yaml")["gates"]["feature_contract"], "approved")
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("invalid gate status", bad.stderr)


if __name__ == "__main__":
    unittest.main()
