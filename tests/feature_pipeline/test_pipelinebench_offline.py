import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

try:
    from plan_test_helpers import BENCH, ignore_generated_pipeline_lab, make_repo, run, write_planning_artifacts
except ModuleNotFoundError:
    from tests.feature_pipeline.plan_test_helpers import BENCH, ignore_generated_pipeline_lab, make_repo, run, write_planning_artifacts


class PipelineBenchOfflineTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="pipelinebench-offline-test-"))
        self.repo = make_repo(self.tempdir)
        shutil.copytree(
            Path(__file__).resolve().parents[2] / "pipeline-lab",
            self.repo / "pipeline-lab",
            dirs_exist_ok=True,
            ignore=ignore_generated_pipeline_lab,
        )

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_score_run_separates_hard_checks_from_soft_placeholders(self):
        workspace = self.tempdir / "workspace"
        workspace.mkdir()
        (workspace / "state.yaml").write_text(
            yaml.safe_dump(
                {
                    "artifact_contract_version": "0.1.0",
                    "feature_key": "auth/reset-password",
                    "run_id": "run-bench-offline",
                    "current_step": "readiness",
                    "worktree": {"branch": "feature/auth-reset-password-run-bench-offline", "path": "../worktrees/auth-reset-password-run-bench-offline"},
                    "gates": {"implementation": "blocked"},
                    "stale": {},
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        write_planning_artifacts(workspace)
        output = self.repo / "pipeline-lab/runs/score.yaml"

        run(["python", str(BENCH), "score-run", "--workspace", str(workspace), "--scenario", "auth-reset-password", "--output", str(output)], self.repo)

        score = yaml.safe_load(output.read_text(encoding="utf-8"))
        self.assertTrue(score["hard_passed"])
        self.assertIn("hard_results", score)
        self.assertIn("schema_valid", [item["name"] for item in score["hard_results"]])
        self.assertIn("docs_consulted_recorded", [item["name"] for item in score["hard_results"]])
        self.assertEqual(score["soft_scores"]["review_quality"], "not_scored_offline")


if __name__ == "__main__":
    unittest.main()
