import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

try:
    from test_planning_readiness import write_planning_artifacts
except ModuleNotFoundError:
    from tests.feature_pipeline.test_planning_readiness import write_planning_artifacts


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".agents/pipeline-core/scripts/featurectl.py"


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class ReviewVerificationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="review-test-"))
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

    def test_review_validation_blocks_critical_findings(self):
        workspace = self.workspace_with_review("critical", True)

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace), "--review"], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("critical review finding blocks verification", result.stdout)

    def test_review_validation_passes_nonblocking_major_finding(self):
        workspace = self.workspace_with_review("major", False, "run-review-major")

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace), "--review"], self.repo)

        self.assertIn("validation: pass", result.stdout)

    def test_critical_review_must_be_blocking(self):
        workspace = self.workspace_with_review("critical", False, "run-critical-nonblocking")

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace), "--review"], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("critical severity must be blocking", result.stdout)

    def test_verification_gate_requires_final_output_and_review(self):
        workspace = self.workspace_with_review("note", False, "run-verification-missing")
        state_path = workspace / "state.yaml"
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        state["current_step"] = "verification"
        state["gates"]["verification"] = "drafted"
        state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("verification gate requires reviews/verification-review.md", result.stdout)
        self.assertIn("verification gate requires evidence/final-verification-output.log", result.stdout)

    def test_verification_artifacts_validate(self):
        workspace = self.workspace_with_review("note", False, "run-verification-pass")
        (workspace / "evidence/final-verification-output.log").write_text("tests passed\n", encoding="utf-8")
        (workspace / "reviews/verification-review.md").write_text(
            "# Verification Review\n\nPassed.\n\n## Manual Validation\n\nNot applicable.\n\n## Verification Debt\n\nNone.\n",
            encoding="utf-8",
        )
        state_path = workspace / "state.yaml"
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        state["current_step"] = "verification"
        state["gates"]["verification"] = "complete"
        state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace)], self.repo)

        self.assertIn("validation: pass", result.stdout)

    def test_verification_review_requires_manual_validation_and_debt(self):
        workspace = self.workspace_with_review("note", False, "run-verification-sections")
        (workspace / "evidence/final-verification-output.log").write_text("tests passed\n", encoding="utf-8")
        (workspace / "reviews/verification-review.md").write_text("# Verification Review\n\nPassed.\n", encoding="utf-8")
        state_path = workspace / "state.yaml"
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        state["current_step"] = "verification"
        state["gates"]["verification"] = "complete"
        state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("verification review missing heading: ## Manual Validation", result.stdout)
        self.assertIn("verification review missing heading: ## Verification Debt", result.stdout)

    def workspace_with_review(self, severity, blocking, run_id="run-review-critical"):
        workspace = self.create_workspace(run_id)
        write_planning_artifacts(workspace)
        (workspace / "reviews").mkdir(exist_ok=True)
        (workspace / "reviews/security.yaml").write_text(
            yaml.safe_dump(
                {
                    "artifact_contract_version": "0.1.0",
                    "review_id": "REV-001",
                    "tier": "strict_review",
                    "severity": severity,
                    "finding": "Plaintext token storage risk" if severity == "critical" else "Document token expiry tests",
                    "artifact": "tech-design.md",
                    "evidence": "Review sample",
                    "recommendation": "Hash tokens",
                    "blocking": blocking,
                    "linked_requirement_ids": ["FR-001"],
                    "linked_slice_ids": ["S-001"],
                    "file_refs": ["tech-design.md"],
                    "reproduction_or_reasoning": "Token storage design must prove plaintext tokens are never persisted.",
                    "fix_verification_command": "python -m unittest tests.test_password_reset",
                    "re_review_required": blocking,
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        state_path = workspace / "state.yaml"
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        state["current_step"] = "review"
        state["gates"]["feature_contract"] = "approved"
        state["gates"]["architecture"] = "approved"
        state["gates"]["tech_design"] = "approved"
        state["gates"]["slicing_readiness"] = "approved"
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


if __name__ == "__main__":
    unittest.main()
