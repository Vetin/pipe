import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
FEATURECTL = ROOT / ".agents/pipeline-core/scripts/featurectl.py"
BENCH = ROOT / ".agents/pipeline-core/scripts/pipelinebench.py"


def ignore_generated_pipeline_lab(_src, names):
    ignored = {
        "runs",
        "repos",
        "real-runs",
        "implementation-runs",
        "materialized-runs",
        "nfp-real-runs",
        "codex-e2e-runs",
    }
    return [name for name in names if name in ignored]


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class ShowcaseTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="showcase-test-"))
        self.repo = self.make_repo()
        shutil.copytree(
            ROOT / "pipeline-lab",
            self.repo / "pipeline-lab",
            dirs_exist_ok=True,
            ignore=ignore_generated_pipeline_lab,
        )
        shutil.copytree(ROOT / ".agents", self.repo / ".agents", dirs_exist_ok=True)
        shutil.copytree(ROOT / ".ai", self.repo / ".ai", dirs_exist_ok=True)
        shutil.copytree(ROOT / "skills", self.repo / "skills", dirs_exist_ok=True)
        run(["git", "add", "."], self.repo)
        run(["git", "commit", "-m", "seed pipeline"], self.repo)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def make_repo(self):
        repo = self.tempdir / "repo"
        repo.mkdir()
        run(["git", "init", "-b", "main"], repo)
        run(["git", "config", "user.email", "test@example.com"], repo)
        run(["git", "config", "user.name", "Test User"], repo)
        (repo / "README.md").write_text("# Showcase Repo\n", encoding="utf-8")
        return repo

    def test_ten_showcase_scenarios_exist_and_initialize_worktrees(self):
        scenarios = sorted((ROOT / "pipeline-lab/showcases/scenarios").glob("*.yaml"))
        self.assertEqual(len(scenarios), 10)

        for index, scenario_path in enumerate(scenarios, start=1):
            scenario = yaml.safe_load(scenario_path.read_text(encoding="utf-8"))
            run_id = f"run-showcase-{index:02d}"
            result = run(
                [
                    sys.executable,
                    str(FEATURECTL),
                    "new",
                    "--domain",
                    scenario["domain"],
                    "--title",
                    scenario["title"],
                    "--run-id",
                    run_id,
                ],
                self.repo,
            )
            slug = slugify(scenario["title"])
            workspace = self.tempdir / f"worktrees/{scenario['domain']}-{slug}-{run_id}/.ai/feature-workspaces/{scenario['domain']}/{slug}--{run_id}"
            self.assertIn(f"feature_key: {scenario['domain']}/{slug}", result.stdout)
            self.assertTrue((workspace / "feature.yaml").exists())
            self.assertTrue((workspace / "state.yaml").exists())
            status = run([sys.executable, str(FEATURECTL), "status", "--workspace", str(workspace)], self.repo)
            self.assertIn("blocking_issues:\n  none", status.stdout)

    def test_run_showcases_creates_side_by_side_and_ten_iterations(self):
        output_dir = self.repo / "pipeline-lab/runs/showcases"

        result = run([sys.executable, str(BENCH), "run-showcases", "--output-dir", str(output_dir), "--iterations", "10"], self.repo)

        summary = yaml.safe_load((output_dir / "showcase-summary.yaml").read_text(encoding="utf-8"))
        report = (output_dir / "showcase-report.md").read_text(encoding="utf-8")
        self.assertIn("iterations: 10", result.stdout)
        self.assertEqual(summary["scenario_count"], 10)
        self.assertEqual(len(summary["iterations_log"]), 10)
        self.assertEqual(len(summary["side_by_side"]), 10)
        self.assertIn("nfp-08-tdd-implementation", report)
        self.assertIn("01-auth-reset-password", report)

    def test_run_showcases_requires_at_least_ten_iterations(self):
        output_dir = self.repo / "pipeline-lab/runs/showcases"

        result = run([sys.executable, str(BENCH), "run-showcases", "--output-dir", str(output_dir), "--iterations", "9"], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires at least 10 iterations", result.stderr)


def slugify(value):
    import re

    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-{2,}", "-", value).strip("-")


if __name__ == "__main__":
    unittest.main()
