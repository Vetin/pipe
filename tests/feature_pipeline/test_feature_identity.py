import shutil
import tempfile
import unittest
from pathlib import Path

try:
    from plan_test_helpers import create_workspace, load_yaml, make_repo
except ModuleNotFoundError:
    from tests.feature_pipeline.plan_test_helpers import create_workspace, load_yaml, make_repo


class FeatureIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="feature-identity-test-"))
        self.repo = make_repo(self.tempdir)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_feature_identity_is_semantic_and_stable(self):
        workspace = create_workspace(self.tempdir, self.repo, run_id="run-identity")

        feature = load_yaml(workspace / "feature.yaml")
        state = load_yaml(workspace / "state.yaml")

        self.assertEqual(feature["feature_key"], "auth/reset-password")
        self.assertEqual(feature["domain"], "auth")
        self.assertEqual(feature["slug"], "reset-password")
        self.assertEqual(feature["canonical_path"], ".ai/features/auth/reset-password")
        self.assertEqual(feature["feature_key"], state["feature_key"])
        self.assertEqual(feature["run_id"], state["run_id"])


if __name__ == "__main__":
    unittest.main()
