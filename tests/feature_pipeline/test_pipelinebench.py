import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from test_planning_readiness import write_planning_artifacts


ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / ".agents/pipeline-core/scripts/pipelinebench.py"


def ignore_generated_pipeline_lab(_src, names):
    ignored = {
        "runs",
        "repos",
        "real-runs",
        "implementation-runs",
        "materialized-runs",
        "nfp-real-runs",
    }
    return [name for name in names if name in ignored]


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class PipelineBenchTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="pipelinebench-test-"))
        self.repo = self.make_repo()
        shutil.copytree(
            ROOT / "pipeline-lab",
            self.repo / "pipeline-lab",
            dirs_exist_ok=True,
            ignore=ignore_generated_pipeline_lab,
        )

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def make_repo(self):
        repo = self.tempdir / "repo"
        repo.mkdir()
        run(["git", "init", "-b", "main"], repo)
        (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
        return repo

    def test_list_scenarios_includes_mvp_three(self):
        result = run([sys.executable, str(BENCH), "list-scenarios"], self.repo)

        self.assertIn("auth-reset-password", result.stdout)
        self.assertIn("webhook-integration", result.stdout)
        self.assertIn("frontend-settings", result.stdout)

    def test_score_run_writes_hard_checks_and_soft_placeholders(self):
        workspace = self.workspace()
        output = self.repo / "pipeline-lab/runs/score.yaml"

        result = run(
            [
                sys.executable,
                str(BENCH),
                "score-run",
                "--workspace",
                str(workspace),
                "--scenario",
                "auth-reset-password",
                "--output",
                str(output),
            ],
            self.repo,
        )

        score = yaml.safe_load(output.read_text(encoding="utf-8"))
        self.assertIn("hard_passed: true", result.stdout)
        self.assertTrue(score["hard_passed"])
        self.assertEqual(score["soft_scores"]["requirement_quality"], "not_scored_offline")
        self.assertEqual(score["soft_scores"]["module_communication_quality"], "not_scored_offline")

    def test_score_run_fails_hard_when_required_files_are_missing(self):
        workspace = self.workspace("run-missing")
        (workspace / "architecture.md").unlink()
        output = self.repo / "pipeline-lab/runs/missing-score.yaml"

        run(
            [
                sys.executable,
                str(BENCH),
                "score-run",
                "--workspace",
                str(workspace),
                "--scenario",
                "auth-reset-password",
                "--output",
                str(output),
            ],
            self.repo,
        )

        score = yaml.safe_load(output.read_text(encoding="utf-8"))
        self.assertFalse(score["hard_passed"])
        self.assertIn("core_artifacts", [item["name"] for item in score["hard_results"]])

    def test_generate_report_from_score(self):
        workspace = self.workspace("run-report")
        output = self.repo / "pipeline-lab/runs/score.yaml"
        report = self.repo / "pipeline-lab/runs/report.md"
        run(
            [
                sys.executable,
                str(BENCH),
                "score-run",
                "--workspace",
                str(workspace),
                "--scenario",
                "auth-reset-password",
                "--output",
                str(output),
            ],
            self.repo,
        )

        result = run([sys.executable, str(BENCH), "generate-report", "--scores", str(output), "--output", str(report)], self.repo)

        self.assertIn("report:", result.stdout)
        self.assertIn("Pipeline Benchmark Report", report.read_text(encoding="utf-8"))

    def test_candidate_skill_isolation_paths_exist_and_do_not_use_skill_md(self):
        quarantine = ROOT / ".agents/skill-lab/quarantine"
        self.assertTrue(quarantine.is_dir())
        self.assertFalse(list(quarantine.glob("*/**/SKILL.md")))

    def test_score_run_accepts_quarantined_candidate_only(self):
        workspace = self.workspace("run-candidate")
        candidate = self.repo / ".agents/skill-lab/quarantine/nfp-02-feature-contract/v2/SKILL.candidate.md"
        candidate.parent.mkdir(parents=True)
        candidate.write_text("# Candidate\n", encoding="utf-8")
        output = self.repo / "pipeline-lab/runs/candidate-score.yaml"

        run(
            [
                sys.executable,
                str(BENCH),
                "score-run",
                "--workspace",
                str(workspace),
                "--scenario",
                "auth-reset-password",
                "--candidate",
                str(candidate),
                "--output",
                str(output),
            ],
            self.repo,
        )
        score = yaml.safe_load(output.read_text(encoding="utf-8"))
        self.assertEqual(score["candidate"], ".agents/skill-lab/quarantine/nfp-02-feature-contract/v2/SKILL.candidate.md")

        bad = self.repo / ".agents/skills/nfp-02-feature-contract/SKILL.md"
        bad.parent.mkdir(parents=True)
        bad.write_text("# Active skill\n", encoding="utf-8")
        result = run(
            [
                sys.executable,
                str(BENCH),
                "score-run",
                "--workspace",
                str(workspace),
                "--scenario",
                "auth-reset-password",
                "--candidate",
                str(bad),
                "--output",
                str(output),
            ],
            self.repo,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("candidate must be under .agents/skill-lab/quarantine", result.stderr)

    def workspace(self, run_id="run-bench"):
        workspace = self.tempdir / f"workspace-{run_id}"
        workspace.mkdir()
        (workspace / "state.yaml").write_text(
            yaml.safe_dump(
                {
                    "artifact_contract_version": "0.1.0",
                    "feature_key": "auth/reset-password",
                    "run_id": run_id,
                    "current_step": "readiness",
                    "worktree": {"branch": f"feature/auth-reset-password-{run_id}", "path": f"../worktrees/auth-reset-password-{run_id}"},
                    "gates": {
                        "feature_contract": "drafted",
                        "architecture": "drafted",
                        "tech_design": "drafted",
                        "slicing_readiness": "drafted",
                        "implementation": "blocked",
                        "review": "pending",
                        "verification": "pending",
                        "finish": "pending",
                    },
                    "stale": {
                        "feature": False,
                        "architecture": False,
                        "tech_design": False,
                        "slices": False,
                        "evidence": False,
                        "review": False,
                        "feature_card": True,
                        "canonical_docs": True,
                        "index": False,
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        write_planning_artifacts(workspace)
        state = yaml.safe_load((workspace / "state.yaml").read_text(encoding="utf-8"))
        state["gates"]["implementation"] = "blocked"
        (workspace / "state.yaml").write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
        return workspace


if __name__ == "__main__":
    unittest.main()
