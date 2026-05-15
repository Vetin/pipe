import shutil
import tempfile
import unittest
from pathlib import Path

try:
    from plan_test_helpers import FEATURECTL, create_workspace, load_yaml, make_repo, run, write_planning_artifacts
except ModuleNotFoundError:
    from tests.feature_pipeline.plan_test_helpers import FEATURECTL, create_workspace, load_yaml, make_repo, run, write_planning_artifacts


class GateStatusTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="gate-status-test-"))
        self.repo = make_repo(self.tempdir)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_gate_set_accepts_known_status_and_rejects_unknown_status(self):
        workspace = create_workspace(self.tempdir, self.repo, run_id="run-gate-status")
        write_planning_artifacts(workspace)

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

    def test_gate_set_blocks_feature_contract_approval_without_feature_md(self):
        workspace = create_workspace(self.tempdir, self.repo, run_id="run-missing-feature-contract")

        result = run(
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
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("feature_contract gate requires feature.md", result.stdout)
        self.assertEqual(load_yaml(workspace / "state.yaml")["gates"]["feature_contract"], "pending")

    def test_gate_set_blocks_architecture_approval_without_architecture_md(self):
        workspace = create_workspace(self.tempdir, self.repo, run_id="run-missing-architecture")
        write_planning_artifacts(workspace)
        run(
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
        (workspace / "architecture.md").unlink()

        result = run(
            [
                "python",
                str(FEATURECTL),
                "gate",
                "set",
                "--workspace",
                str(workspace),
                "--gate",
                "architecture",
                "--status",
                "approved",
                "--by",
                "test",
            ],
            self.repo,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("architecture gate requires architecture.md", result.stdout)
        self.assertEqual(load_yaml(workspace / "state.yaml")["gates"]["architecture"], "pending")

    def test_gate_set_blocks_tech_design_approval_without_tech_design_md(self):
        workspace = create_workspace(self.tempdir, self.repo, run_id="run-missing-tech-design")
        write_planning_artifacts(workspace)
        for gate in ("feature_contract", "architecture"):
            run(
                [
                    "python",
                    str(FEATURECTL),
                    "gate",
                    "set",
                    "--workspace",
                    str(workspace),
                    "--gate",
                    gate,
                    "--status",
                    "approved",
                    "--by",
                    "test",
                ],
                self.repo,
            )
        (workspace / "tech-design.md").unlink()

        result = run(
            [
                "python",
                str(FEATURECTL),
                "gate",
                "set",
                "--workspace",
                str(workspace),
                "--gate",
                "tech_design",
                "--status",
                "approved",
                "--by",
                "test",
            ],
            self.repo,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("tech_design gate requires tech-design.md", result.stdout)
        self.assertEqual(load_yaml(workspace / "state.yaml")["gates"]["tech_design"], "pending")

    def test_gate_set_blocks_approval_of_scaffold_only_artifact(self):
        workspace = create_workspace(self.tempdir, self.repo, run_id="run-scaffold-approval")
        write_planning_artifacts(workspace)
        run(
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
        architecture_path = workspace / "architecture.md"
        architecture_path.write_text(
            architecture_path.read_text(encoding="utf-8") + "\nStatus: scaffold-only\n",
            encoding="utf-8",
        )

        result = run(
            [
                "python",
                str(FEATURECTL),
                "gate",
                "set",
                "--workspace",
                str(workspace),
                "--gate",
                "architecture",
                "--status",
                "approved",
                "--by",
                "test",
            ],
            self.repo,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("architecture.md is scaffold-only and cannot satisfy planning-package validation", result.stdout)
        self.assertEqual(load_yaml(workspace / "state.yaml")["gates"]["architecture"], "pending")

    def test_gate_set_allows_architecture_after_valid_architecture_doc(self):
        workspace = create_workspace(self.tempdir, self.repo, run_id="run-valid-architecture")
        write_planning_artifacts(workspace)
        run(
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

        result = run(
            [
                "python",
                str(FEATURECTL),
                "gate",
                "set",
                "--workspace",
                str(workspace),
                "--gate",
                "architecture",
                "--status",
                "approved",
                "--by",
                "test",
            ],
            self.repo,
        )

        self.assertIn("status: approved", result.stdout)
        self.assertEqual(load_yaml(workspace / "state.yaml")["gates"]["architecture"], "approved")


if __name__ == "__main__":
    unittest.main()
