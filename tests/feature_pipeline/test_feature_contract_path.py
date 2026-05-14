import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".agents/pipeline-core/scripts/featurectl.py"


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class FeatureContractPathTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="feature-contract-test-"))
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

    def test_intake_context_and_feature_contract_skills_have_required_contracts(self):
        for skill in ("nfp-00-intake", "nfp-01-context", "nfp-02-feature-contract"):
            content = (ROOT / f".agents/skills/{skill}/SKILL.md").read_text(encoding="utf-8")
            self.assertIn("version: '0.1.0'", content)
            self.assertIn("pipeline_contract_version: '0.1.0'", content)
            self.assertIn("Forbidden actions:", content)
            self.assertIn("approvals.yaml", content)
            self.assertIn("handoff.md", content)

        feature_contract = (ROOT / ".agents/skills/nfp-02-feature-contract/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("FR-001", feature_contract)
        self.assertIn("AC-001", feature_contract)
        self.assertIn("One-artifact stop behavior", feature_contract)

    def test_one_artifact_feature_contract_scenario_validates(self):
        workspace = self.create_workspace()
        self.write_feature_contract(workspace)
        self.append_docs_consulted(workspace)
        self.set_feature_contract_drafted(workspace)

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace)], self.repo)

        self.assertIn("validation: pass", result.stdout)
        self.assertTrue((workspace / "feature.md").exists())
        self.assertFalse((workspace / "architecture.md").exists())
        self.assertFalse((workspace / "tech-design.md").exists())
        self.assertFalse((workspace / "slices.yaml").exists())

    def test_feature_contract_gate_requires_feature_md(self):
        workspace = self.create_workspace("run-20260511-nofeature")
        self.set_feature_contract_drafted(workspace)

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("feature_contract gate requires feature.md", result.stdout)

    def create_workspace(self, run_id="run-20260511-contract"):
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

    def write_feature_contract(self, workspace):
        (workspace / "feature.md").write_text(
            """# Feature: Reset Password

## Intent
Allow registered users to reset a forgotten password.

## Motivation
Users need a safe account recovery path.

## Actors
- Registered user
- Auth API

## Problem
Users who forget passwords cannot regain access without support.

## Goals
- Provide email-based recovery.

## Non-Goals
- Admin-initiated reset is out of scope.

## Related Existing Features
- None found.

## Functional Requirements
- FR-001: A user can request a password reset by email.

## Non-Functional Requirements
- NFR-001: The response must not leak whether an account exists.

## Acceptance Criteria
- AC-001: A reset request for a known user returns a generic success message.

## Product Risks
- Account enumeration must be avoided.

## Assumptions
- An email service exists.

## Open Questions
- None.
""",
            encoding="utf-8",
        )

    def set_feature_contract_drafted(self, workspace):
        state_path = workspace / "state.yaml"
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        state["current_step"] = "architecture"
        state["gates"]["feature_contract"] = "drafted"
        state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

    def append_docs_consulted(self, workspace):
        with (workspace / "execution.md").open("a", encoding="utf-8") as handle:
            handle.write(
                """

## Docs Consulted: Feature Contract

- `README.md`
  - Used for: used repository fixture context before drafting the feature contract.
  - Confidence: high.
"""
            )


if __name__ == "__main__":
    unittest.main()
