import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

try:
    from plan_test_helpers import FEATURECTL, create_workspace, make_repo, run, write_planning_artifacts
except ModuleNotFoundError:
    from tests.feature_pipeline.plan_test_helpers import FEATURECTL, create_workspace, make_repo, run, write_planning_artifacts


class SlicesValidationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="slices-validation-test-"))
        self.repo = make_repo(self.tempdir)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_slices_require_tdd_commands_and_known_dependencies(self):
        workspace = create_workspace(self.tempdir, self.repo, run_id="run-slices")
        write_planning_artifacts(workspace)
        slices_path = workspace / "slices.yaml"
        data = yaml.safe_load(slices_path.read_text(encoding="utf-8"))
        data["slices"][0]["tdd"]["red_command"] = ""
        data["slices"][0]["dependencies"] = ["S-999"]
        slices_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        state_path = workspace / "state.yaml"
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        state["gates"]["slicing_readiness"] = "drafted"
        state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

        result = run(["python", str(FEATURECTL), "validate", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("depends on unknown slice S-999", result.stdout)
        self.assertIn("tdd missing red_command", result.stdout)

    def test_slices_require_loop_ready_fields(self):
        workspace = create_workspace(self.tempdir, self.repo, run_id="run-slices-loop")
        write_planning_artifacts(workspace)
        slices_path = workspace / "slices.yaml"
        data = yaml.safe_load(slices_path.read_text(encoding="utf-8"))
        del data["slices"][0]["iteration_budget"]
        data["slices"][0]["rollback_point"] = ""
        slices_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        state_path = workspace / "state.yaml"
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        state["gates"]["slicing_readiness"] = "drafted"
        state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

        result = run(["python", str(FEATURECTL), "validate", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing iteration_budget", result.stdout)
        self.assertIn("rollback_point must not be empty", result.stdout)

    def test_slices_require_task_graph_fields(self):
        workspace = create_workspace(self.tempdir, self.repo, run_id="run-slices-graph")
        write_planning_artifacts(workspace)
        slices_path = workspace / "slices.yaml"
        data = yaml.safe_load(slices_path.read_text(encoding="utf-8"))
        data["slices"][0]["complexity"] = 11
        data["slices"][0]["critical_path"] = "yes"
        data["slices"][0]["parallelizable"] = "no"
        data["slices"][0]["file_ownership"] = []
        data["slices"][0]["conflict_risk"] = "unknown"
        data["slices"][0]["dependency_notes"] = ""
        data["slices"][0]["test_strategy"] = ""
        slices_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        state_path = workspace / "state.yaml"
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        state["gates"]["slicing_readiness"] = "drafted"
        state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

        result = run(["python", str(FEATURECTL), "validate", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("complexity must be an integer from 1 to 10", result.stdout)
        self.assertIn("critical_path must be true or false", result.stdout)
        self.assertIn("parallelizable must be true or false", result.stdout)
        self.assertIn("file_ownership must be a non-empty list", result.stdout)
        self.assertIn("conflict_risk must be low, medium, or high", result.stdout)
        self.assertIn("dependency_notes must not be empty", result.stdout)
        self.assertIn("test_strategy must not be empty", result.stdout)


if __name__ == "__main__":
    unittest.main()
