import shutil
import tempfile
import unittest
from pathlib import Path

try:
    from plan_test_helpers import FEATURECTL, create_workspace, load_yaml, make_repo, run
except ModuleNotFoundError:
    from tests.feature_pipeline.plan_test_helpers import FEATURECTL, create_workspace, load_yaml, make_repo, run


class StalenessTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="staleness-test-"))
        self.repo = make_repo(self.tempdir)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_mark_stale_cascades_from_feature_to_downstream_artifacts(self):
        workspace = create_workspace(self.tempdir, self.repo, run_id="run-staleness")

        run(
            [
                "python",
                str(FEATURECTL),
                "mark-stale",
                "--workspace",
                str(workspace),
                "--artifact",
                "feature",
                "--reason",
                "requirements changed",
            ],
            self.repo,
        )

        stale = load_yaml(workspace / "state.yaml")["stale"]
        for artifact in ("architecture", "tech_design", "slices", "evidence", "feature_card", "canonical_docs"):
            self.assertTrue(stale[artifact], artifact)


if __name__ == "__main__":
    unittest.main()
