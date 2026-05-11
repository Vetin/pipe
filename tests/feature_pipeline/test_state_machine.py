import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

try:
    from plan_test_helpers import FEATURECTL, create_workspace, load_yaml, make_repo, run
except ModuleNotFoundError:
    from tests.feature_pipeline.plan_test_helpers import FEATURECTL, create_workspace, load_yaml, make_repo, run


class StateMachineTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="state-machine-test-"))
        self.repo = make_repo(self.tempdir)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_state_rejects_invalid_step_and_next_skill(self):
        workspace = create_workspace(self.tempdir, self.repo, run_id="run-state")
        state_path = workspace / "state.yaml"
        state = load_yaml(state_path)
        state["current_step"] = "invented"
        state["next_skill"] = "nfp-99"
        state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

        result = run(["python", str(FEATURECTL), "validate", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid current_step", result.stdout)
        self.assertIn("state.yaml must not contain next_skill", result.stdout)


if __name__ == "__main__":
    unittest.main()
