import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "pipeline-lab/showcases/scripts/run_real_showcase.py"
CONFIG = ROOT / "pipeline-lab/showcases/real-showcases.yaml"


class RealShowcaseRunnerTests(unittest.TestCase):
    def test_real_showcase_config_has_ten_cases(self):
        config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))["showcases"]

        self.assertEqual(len(config), 10)
        for name, case in config.items():
            self.assertIn("repo_path", case, name)
            self.assertIn("domain", case, name)
            self.assertIn("title", case, name)
            self.assertIn("run_id", case, name)
            self.assertIn("/", case["feature_key"])

    def test_runner_prunes_stale_worktrees_before_rerun(self):
        content = RUNNER.read_text(encoding="utf-8")

        self.assertIn('"worktree", "remove", "--force"', content)
        self.assertIn('"worktree", "prune"', content)
        self.assertIn('"branch", "-D"', content)


if __name__ == "__main__":
    unittest.main()
