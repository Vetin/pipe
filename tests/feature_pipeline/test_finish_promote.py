import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from test_gates_and_evidence import GatesAndEvidenceTests, run as run_cmd
from test_planning_readiness import write_planning_artifacts


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".agents/pipeline-core/scripts/featurectl.py"


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class FinishPromoteTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="promote-test-"))
        self.repo = self.make_repo()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def make_repo(self):
        repo = self.tempdir / "repo"
        repo.mkdir()
        run(["git", "init", "-b", "main"], repo)
        run(["git", "config", "user.email", "test@example.com"], repo)
        run(["git", "config", "user.name", "Test User"], repo)
        (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
        run(["git", "add", "README.md"], repo)
        run(["git", "commit", "-m", "initial"], repo)
        return repo

    def test_finish_validation_requires_feature_card(self):
        workspace = self.completed_workspace()
        (workspace / "feature-card.md").unlink()

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("finish requires feature-card.md", result.stdout)

    def test_promote_copies_workspace_and_regenerates_index(self):
        workspace = self.completed_workspace("run-promote")

        result = run([sys.executable, str(SCRIPT), "promote", "--workspace", str(workspace)], self.repo)

        canonical = self.repo / ".ai/features/auth/reset-password"
        index = yaml.safe_load((self.repo / ".ai/features/index.yaml").read_text(encoding="utf-8"))
        self.assertIn("promotion: complete", result.stdout)
        self.assertTrue((canonical / "feature-card.md").exists())
        self.assertEqual(index["features"][0]["feature_key"], "auth/reset-password")
        self.assertEqual(index["features"][0]["path"], ".ai/features/auth/reset-password")
        self.assertEqual(yaml.safe_load((canonical / "feature.yaml").read_text(encoding="utf-8"))["status"], "complete")

    def test_promote_conflict_aborts_by_default(self):
        first = self.completed_workspace("run-promote-first")
        run([sys.executable, str(SCRIPT), "promote", "--workspace", str(first)], self.repo)
        second = self.completed_workspace("run-promote-second")

        result = run([sys.executable, str(SCRIPT), "promote", "--workspace", str(second)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("canonical feature already exists", result.stderr)

    def test_promote_archive_as_variant_archives_existing_canonical(self):
        first = self.completed_workspace("run-promote-archive-first")
        run([sys.executable, str(SCRIPT), "promote", "--workspace", str(first)], self.repo)
        second = self.completed_workspace("run-promote-archive-second")

        result = run(
            [sys.executable, str(SCRIPT), "promote", "--workspace", str(second), "--conflict", "archive-as-variant"],
            self.repo,
        )

        self.assertIn("promotion: archived-variant", result.stdout)
        archived = self.repo / ".ai/features-archive/auth/reset-password/run-promote-archive-second"
        canonical = yaml.safe_load((self.repo / ".ai/features/auth/reset-password/feature.yaml").read_text(encoding="utf-8"))
        self.assertTrue((archived / "feature.yaml").exists())
        self.assertEqual(canonical["run_id"], "run-promote-archive-first")

    def completed_workspace(self, run_id="run-finish"):
        workspace = self.create_workspace(run_id)
        write_planning_artifacts(workspace)
        self.record_and_complete_slice(workspace)
        (workspace / "reviews").mkdir(exist_ok=True)
        (workspace / "reviews/security.yaml").write_text(
            yaml.safe_dump(
                {
                    "artifact_contract_version": "0.1.0",
                    "review_id": "REV-001",
                    "tier": "strict_review",
                    "severity": "note",
                    "finding": "No blocker",
                    "artifact": "workspace",
                    "evidence": "Manual review",
                    "recommendation": "Proceed",
                    "blocking": False,
                    "linked_requirement_ids": ["FR-001"],
                    "linked_slice_ids": ["S-001"],
                    "file_refs": ["feature.md", "slices.yaml"],
                    "reproduction_or_reasoning": "Completed slice has ordered evidence and no blocking findings.",
                    "fix_verification_command": "python -m unittest discover -s tests",
                    "re_review_required": False,
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        (workspace / "reviews/verification-review.md").write_text("# Verification Review\n\nPassed.\n", encoding="utf-8")
        (workspace / "evidence/final-verification-output.log").write_text("tests passed\n", encoding="utf-8")
        (workspace / "feature-card.md").write_text(
            "# Feature Card: auth/reset-password\n\nIntent, architecture, contracts, tests, reviews, and evidence summarized.\n",
            encoding="utf-8",
        )
        state_path = workspace / "state.yaml"
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        state["current_step"] = "finish"
        state["gates"]["feature_contract"] = "approved"
        state["gates"]["architecture"] = "approved"
        state["gates"]["tech_design"] = "approved"
        state["gates"]["slicing_readiness"] = "approved"
        state["gates"]["verification"] = "complete"
        state["gates"]["finish"] = "complete"
        state["stale"]["feature_card"] = False
        state["stale"]["canonical_docs"] = False
        state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
        return workspace

    def create_workspace(self, run_id):
        run(
            [
                sys.executable,
                str(SCRIPT),
                "new",
                "--domain",
                "auth",
                "--title",
                "Reset Password",
                "--run-id",
                run_id,
            ],
            self.repo,
        )
        return self.tempdir / f"worktrees/auth-reset-password-{run_id}/.ai/feature-workspaces/auth/reset-password--{run_id}"

    def record_and_complete_slice(self, workspace):
        helper = GatesAndEvidenceTests()
        helper.repo = self.repo
        helper.record_full_evidence(workspace)
        run([sys.executable, str(SCRIPT), "complete-slice", "--workspace", str(workspace), "--slice", "S-001", "--diff-hash", "abc123"], self.repo)


if __name__ == "__main__":
    unittest.main()
