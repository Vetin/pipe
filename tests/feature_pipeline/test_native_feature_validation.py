import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "pipeline-lab/showcases/scripts/validate_native_feature_outputs.py"
RUN_DIR = ROOT / "pipeline-lab/showcases/native-emulation-runs/20260512-native-debug"


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class NativeFeatureValidationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="native-validation-test-"))

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_validator_rechecks_best_three_outputs_three_times(self):
        report = self.tempdir / "validation.md"
        result = run(
            [
                sys.executable,
                str(VALIDATOR),
                "--run-dir",
                str(RUN_DIR),
                "--report",
                str(report),
                "--passes",
                "3",
            ],
            ROOT,
        )

        self.assertIn("failures: 0", result.stdout)
        content = report.read_text(encoding="utf-8")
        self.assertIn("Native Feature Output Validation", content)
        self.assertIn("| 1 | pass | 0 |", content)
        self.assertIn("| 2 | pass | 0 |", content)
        self.assertIn("| 3 | pass | 0 |", content)
        self.assertIn("all native feature outputs passed", content)


if __name__ == "__main__":
    unittest.main()
