import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "pipeline-lab/showcases/scripts/validate_pipeline_goals.py"


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class PipelineGoalValidationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="pipeline-goal-test-"))

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_goal_validator_runs_three_passes_and_compares_skills(self):
        report = self.tempdir / "goals.md"
        result = run(
            [
                sys.executable,
                str(VALIDATOR),
                "--passes",
                "3",
                "--report",
                str(report),
            ],
            ROOT,
        )

        self.assertIn("failures: 0", result.stdout)
        content = report.read_text(encoding="utf-8")
        self.assertIn("Pipeline Goal Validation", content)
        self.assertIn("Skill Side By Side", content)
        self.assertIn("| `nfp-01-context` | pass |", content)
        self.assertIn("| `project-init` | pass |", content)
        self.assertIn("vision_native_workflow", content)
        self.assertIn("init_showcase_three_passes", content)
        self.assertIn("init_showcase_feature_catalogs", content)
        self.assertIn("web_best_practices_doc", content)


if __name__ == "__main__":
    unittest.main()
