import shutil
import subprocess
import sys
import tempfile
import unittest
import importlib.util
from pathlib import Path

import yaml


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
        self.assertIn("codex_debug_status_pass", content)
        self.assertIn("codex_debug_real_mode_diagnostic", content)
        self.assertIn("web_best_practices_doc", content)

    def test_codex_debug_portability_is_validated_when_enabled(self):
        spec = importlib.util.spec_from_file_location("validate_pipeline_goals", VALIDATOR)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        validate_codex_debug_run = module.validate_codex_debug_run

        run_dir = self.tempdir / "codex-debug"
        run_dir.mkdir()
        absolute_repo = str(self.tempdir / "worktrees" / "case")
        (run_dir / "summary.yaml").write_text(
            yaml.safe_dump(
                {
                    "artifact_contract_version": "0.1.0",
                    "run_id": "portable-check",
                    "mode": "mock",
                    "path_mode": "portable",
                    "uses_real_codex": False,
                    "status": "pass",
                    "comparison": {
                        "current_unit_tests_use_fake_codex": True,
                    },
                    "results": [
                        {
                            "case": "toy-feature",
                            "mode": "mock",
                            "artifacts": {
                                "feature.md": ["$WORK_ROOT/.ai/feature.md"],
                                "architecture.md": ["$WORK_ROOT/.ai/architecture.md"],
                                "tech-design.md": ["$WORK_ROOT/.ai/tech-design.md"],
                                "slices.yaml": ["$WORK_ROOT/.ai/slices.yaml"],
                            },
                        }
                    ],
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        (run_dir / "comparison.md").write_text("Uses fake Codex: `true`\n", encoding="utf-8")
        (run_dir / "validation.md").write_text("Codex Debug Pipeline Validation\n", encoding="utf-8")
        (run_dir / "real-mode-diagnostic.md").write_text(
            "uses_real_codex: true\nmissing field: demo\n",
            encoding="utf-8",
        )

        passing = validate_codex_debug_run(run_dir)
        self.assertIn("codex_debug_portable_output", {item["name"] for item in passing if item["status"] == "pass"})

        (run_dir / "comparison.md").write_text(f"Uses fake Codex: `true`\nleak: {absolute_repo}\n", encoding="utf-8")
        failing = validate_codex_debug_run(run_dir)
        portability = [item for item in failing if item["name"] == "codex_debug_portable_output"]
        self.assertEqual(portability[0]["status"], "fail")
        self.assertIn("absolute path leaks", portability[0]["detail"])


if __name__ == "__main__":
    unittest.main()
