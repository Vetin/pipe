import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
EMULATOR = ROOT / "pipeline-lab/showcases/scripts/run_native_feature_emulation.py"
JUDGE = ROOT / "pipeline-lab/showcases/scripts/judge_native_feature_builds.py"


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class NativeFeatureJudgeTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="native-judge-test-"))
        self.features = self.tempdir / "features.md"
        self.runs = self.tempdir / "runs"
        self.report = self.tempdir / "report.md"
        self.judge_md = self.tempdir / "judge.md"
        self.judge_yaml = self.tempdir / "judge.yaml"
        self.features.write_text(
            """# Features

| Source | Feature | Expected Result |
| --- | --- | --- |
| **Twenty** - open source CRM | **Enterprise duplicate merge with preview, conflict rules, and rollback** | Duplicate detection, preview, merge, audit log, rollback-safe behavior. |

## Best three showcase features

| Rank | Showcase | Why |
| ---: | --- | --- |
| 1 | **Twenty - Enterprise duplicate merge with preview, conflict rules, and rollback** | Best enterprise data safety case. |
""",
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_judge_scores_native_emulation_and_methodology_coverage(self):
        run(
            [
                sys.executable,
                str(EMULATOR),
                "--features-md",
                str(self.features),
                "--output-dir",
                str(self.runs),
                "--report",
                str(self.report),
                "--run-id",
                "judge-source",
                "--rounds",
                "3",
                "--top",
                "1",
                "--clean",
            ],
            ROOT,
        )
        result = run(
            [
                sys.executable,
                str(JUDGE),
                "--summary",
                str(self.runs / "judge-source/summary.yaml"),
                "--output-md",
                str(self.judge_md),
                "--output-yaml",
                str(self.judge_yaml),
            ],
            ROOT,
        )

        self.assertIn("latest_overall:", result.stdout)
        judged = yaml.safe_load(self.judge_yaml.read_text(encoding="utf-8"))
        self.assertEqual(judged["judge_mode"], "deterministic-llm-style")
        run_result = judged["runs"][0]
        self.assertTrue(run_result["high_quality"])
        self.assertGreaterEqual(run_result["overall"], 0.86)
        self.assertIn("adaptive_rigor", run_result["methodology_coverage"]["dimensions"])
        self.assertIn("Run Comparison", self.judge_md.read_text(encoding="utf-8"))

    def test_judge_fails_direct_internal_skill_prompt(self):
        run(
            [
                sys.executable,
                str(EMULATOR),
                "--features-md",
                str(self.features),
                "--output-dir",
                str(self.runs),
                "--report",
                str(self.report),
                "--run-id",
                "bad-prompt",
                "--rounds",
                "3",
                "--top",
                "1",
                "--clean",
            ],
            ROOT,
        )
        prompt = next((self.runs / "bad-prompt").glob("round-03/*/prompt.md"))
        prompt.write_text(prompt.read_text(encoding="utf-8") + "\nRun nfp-00-intake then nfp-12-promote.\n", encoding="utf-8")
        result = run(
            [
                sys.executable,
                str(JUDGE),
                "--summary",
                str(self.runs / "bad-prompt/summary.yaml"),
                "--output-md",
                str(self.judge_md),
                "--output-yaml",
                str(self.judge_yaml),
            ],
            ROOT,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        judged = yaml.safe_load(self.judge_yaml.read_text(encoding="utf-8"))
        self.assertIn("prompt directly invokes internal skill sequence", judged["runs"][0]["hard_failures"])


if __name__ == "__main__":
    unittest.main()
