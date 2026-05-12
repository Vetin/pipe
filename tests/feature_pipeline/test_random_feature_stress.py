import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "pipeline-lab/showcases/scripts/run_random_feature_stress.py"


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class RandomFeatureStressTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="random-feature-stress-test-"))
        self.output_dir = self.tempdir / "runs"

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_runner_requires_at_least_ten_features_and_iterations(self):
        result = run(
            [
                sys.executable,
                str(RUNNER),
                "--output-dir",
                str(self.output_dir),
                "--feature-count",
                "9",
                "--iterations",
                "10",
            ],
            ROOT,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires at least 10 features", result.stderr)

        result = run(
            [
                sys.executable,
                str(RUNNER),
                "--output-dir",
                str(self.output_dir),
                "--feature-count",
                "10",
                "--iterations",
                "9",
            ],
            ROOT,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires at least 10 iterations", result.stderr)

    def test_ten_random_features_rebuild_and_compare_shared_knowledge(self):
        result = run(
            [
                sys.executable,
                str(RUNNER),
                "--output-dir",
                str(self.output_dir),
                "--run-id",
                "stable-test",
                "--seed",
                "20260512",
                "--feature-count",
                "10",
                "--iterations",
                "10",
                "--clean",
            ],
            ROOT,
        )

        run_dir = self.output_dir / "stable-test"
        summary = yaml.safe_load((run_dir / "summary.yaml").read_text(encoding="utf-8"))
        feature_list = yaml.safe_load((run_dir / "feature-list.yaml").read_text(encoding="utf-8"))
        report = (run_dir / "side-by-side.md").read_text(encoding="utf-8")
        improvement_plan = (run_dir / "improvement-plan.md").read_text(encoding="utf-8")
        rollback_plan = (run_dir / "rollback-plan.md").read_text(encoding="utf-8")

        self.assertIn("run_id: stable-test", result.stdout)
        self.assertEqual(summary["feature_count"], 10)
        self.assertEqual(summary["iterations"], 10)
        self.assertEqual(summary["total_feature_runs"], 100)
        self.assertEqual(summary["status"], "pass")
        self.assertEqual(summary["open_improvements"], [])
        self.assertEqual(len(feature_list["features"]), 10)
        self.assertEqual(len(summary["iteration_results"]), 10)
        self.assertTrue(all(item["status"] == "pass" for item in summary["iteration_results"]))
        self.assertIn("generic shared-knowledge path bullets", summary["common_mistakes"])
        self.assertIn("shared knowledge decision table", " ".join(summary["applied_improvements"]).lower())

        scorecards = sorted(run_dir.glob("iterations/iteration-*/scorecards/*.yaml"))
        self.assertEqual(len(scorecards), 100)

        first_feature = feature_list["features"][0]
        architecture = (run_dir / "features" / first_feature["id"] / "artifacts/architecture.md").read_text(encoding="utf-8")
        feature_card = (run_dir / "features" / first_feature["id"] / "artifacts/feature-card.md").read_text(encoding="utf-8")

        for content in (architecture, feature_card):
            self.assertIn("Shared Knowledge Decision Table", content)
            self.assertIn(".ai/knowledge/features-overview.md", content)
            self.assertIn(".ai/knowledge/architecture-overview.md", content)
            self.assertIn("Future reuse", content)
            self.assertIn("Evidence", content)

        self.assertIn("Side By Side Knowledge Comparison", report)
        self.assertIn("10/10", report)
        self.assertIn("No open improvements remain", improvement_plan)
        self.assertIn("No target repositories were mutated", rollback_plan)

    def test_skills_require_shared_knowledge_decision_tables(self):
        architecture_skill = (ROOT / ".agents/skills/nfp-03-architecture/SKILL.md").read_text(encoding="utf-8")
        finish_skill = (ROOT / ".agents/skills/nfp-11-finish/SKILL.md").read_text(encoding="utf-8")
        architecture_template = (ROOT / ".agents/pipeline-core/references/generated-templates/architecture-template.md").read_text(encoding="utf-8")
        feature_card_template = (ROOT / ".agents/pipeline-core/references/generated-templates/feature-card-template.md").read_text(encoding="utf-8")

        for content in (architecture_skill, finish_skill, architecture_template, feature_card_template):
            self.assertIn("Shared Knowledge Decision Table", content)
            self.assertIn("Decision", content)
            self.assertIn("Evidence", content)
            self.assertIn("Future reuse", content)


if __name__ == "__main__":
    unittest.main()
