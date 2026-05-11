import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "pipeline-lab/showcases/scripts/run_native_feature_emulation.py"


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class NativeFeatureEmulationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="native-emulation-test-"))
        self.features = self.tempdir / "features.md"
        self.output_dir = self.tempdir / "runs"
        self.report = self.tempdir / "report.md"
        self.features.write_text(
            """# Features

| Source | Feature | Expected Result |
| --- | --- | --- |
| **Plane** - open source project management | **GitHub sync conflict resolution and audit trail** | Feature contract, ADR, sync-state model, conflict detection, resolution, and audit. |
| **Twenty** - open source CRM | **Enterprise duplicate merge with preview, conflict rules, and rollback** | Duplicate detection, preview, merge, audit log, rollback-safe behavior. |
| **Medusa** - commerce platform | **B2B quote-to-order approval workflow** | Multi-actor approval, price locking, contracts, expiry, conversion, and audit. |

## Best three showcase features

| Rank | Showcase | Why |
| ---: | --- | --- |
| 1 | **Twenty - Enterprise duplicate merge with preview, conflict rules, and rollback** | Best enterprise data safety case. |
| 2 | **Medusa - B2B quote-to-order approval workflow** | Best multi-actor state machine case. |
| 3 | **Plane - GitHub sync conflict resolution and audit trail** | Best integration conflict case. |
""",
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_three_native_rounds_generate_artifacts_and_improve_scores(self):
        result = run(
            [
                sys.executable,
                str(RUNNER),
                "--features-md",
                str(self.features),
                "--output-dir",
                str(self.output_dir),
                "--report",
                str(self.report),
                "--run-id",
                "stable-test",
                "--rounds",
                "3",
                "--top",
                "3",
                "--clean",
            ],
            ROOT,
        )

        self.assertIn("run_id: stable-test", result.stdout)
        summary_path = self.output_dir / "stable-test/summary.yaml"
        summary = yaml.safe_load(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["prompt_style"], "native-user-request")
        self.assertFalse(summary["direct_skill_invocations"])
        self.assertEqual(len(summary["scorecards"]), 9)

        scores_by_case = {}
        for card in summary["scorecards"]:
            scores_by_case.setdefault(card["case"], {})[card["round"]] = card["overall"]
            prompt = (Path(card["artifacts"]["feature"]).parents[1] / "prompt.md").read_text(encoding="utf-8")
            self.assertIn("normal user feature request", prompt)
            self.assertNotIn("Read and follow every NFP skill doc in order", prompt)
            self.assertNotIn("nfp-00-intake", prompt)
            self.assertNotIn("nfp-12-promote", prompt)
            for artifact in card["artifacts"].values():
                self.assertTrue(Path(artifact).exists(), artifact)

        for case_id, scores in scores_by_case.items():
            with self.subTest(case=case_id):
                self.assertLess(scores[1], scores[2])
                self.assertLess(scores[2], scores[3])
                self.assertGreaterEqual(scores[3], 0.92)

        report = self.report.read_text(encoding="utf-8")
        self.assertIn("Side By Side Scores", report)
        self.assertIn("Plan.md Conformance", report)
        self.assertIn("Prompt Improvements", report)
        self.assertIn("high quality", report)


if __name__ == "__main__":
    unittest.main()
