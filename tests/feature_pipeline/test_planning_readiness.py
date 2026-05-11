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


class PlanningReadinessTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="readiness-test-"))
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

    def test_full_planning_package_validates_but_readiness_requires_approval_or_delegation(self):
        workspace = self.create_workspace()
        write_planning_artifacts(workspace)
        self.set_gates(workspace, feature_contract="drafted", architecture="drafted", tech_design="drafted", slicing_readiness="drafted")

        basic = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace)], self.repo)
        readiness = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace), "--readiness"], self.repo, check=False)

        self.assertIn("validation: pass", basic.stdout)
        self.assertNotEqual(readiness.returncode, 0)
        self.assertIn("readiness requires feature_contract gate approved or delegated", readiness.stdout)
        self.assertFalse((workspace / "src").exists())

    def test_readiness_passes_with_approved_or_delegated_gates(self):
        workspace = self.create_workspace("run-readiness-pass")
        write_planning_artifacts(workspace)
        self.set_gates(
            workspace,
            feature_contract="approved",
            architecture="approved",
            tech_design="approved",
            slicing_readiness="delegated",
        )

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace), "--readiness"], self.repo)

        self.assertIn("validation: pass", result.stdout)

    def test_slices_validation_blocks_allowed_and_forbidden_files(self):
        workspace = self.create_workspace("run-slices-forbidden")
        write_planning_artifacts(workspace)
        slices_path = workspace / "slices.yaml"
        data = yaml.safe_load(slices_path.read_text(encoding="utf-8"))
        data["slices"][0]["allowed_files"] = ["src/auth.py"]
        slices_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        self.set_gates(workspace, feature_contract="approved", architecture="approved", tech_design="approved", slicing_readiness="drafted")

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must not use allowed_files in v1", result.stdout)

    def test_slices_validation_blocks_unknown_requirement_links(self):
        workspace = self.create_workspace("run-slices-bad-link")
        write_planning_artifacts(workspace)
        slices_path = workspace / "slices.yaml"
        data = yaml.safe_load(slices_path.read_text(encoding="utf-8"))
        data["slices"][0]["linked_requirements"] = ["FR-999"]
        slices_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        self.set_gates(workspace, feature_contract="approved", architecture="approved", tech_design="approved", slicing_readiness="drafted")

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("links unknown requirement FR-999", result.stdout)

    def create_workspace(self, run_id="run-readiness"):
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

    def set_gates(self, workspace, *, feature_contract, architecture, tech_design, slicing_readiness):
        state_path = workspace / "state.yaml"
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        state["current_step"] = "readiness"
        state["gates"]["feature_contract"] = feature_contract
        state["gates"]["architecture"] = architecture
        state["gates"]["tech_design"] = tech_design
        state["gates"]["slicing_readiness"] = slicing_readiness
        state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")


def write_planning_artifacts(workspace):
    (workspace / "feature.md").write_text(
        """# Feature: Reset Password

## Intent
Allow reset.

## Motivation
Recovery.

## Actors
- User

## Problem
Forgotten passwords.

## Goals
- Recover account.

## Non-Goals
- Admin reset.

## Related Existing Features
- None.

## Functional Requirements
- FR-001: Request reset.

## Non-Functional Requirements
- NFR-001: Do not leak accounts.

## Acceptance Criteria
- AC-001: Generic success response.

## Product Risks
- Enumeration.

## Assumptions
- Email exists.

## Open Questions
- None.
""",
        encoding="utf-8",
    )
    (workspace / "architecture.md").write_text(
        """# Architecture: Reset Password

## System Context
Auth owns reset.

## Component Interactions
API calls token store and email service.

## Diagrams
None.

## Security Model
Hash tokens.

## Failure Modes
Email failure.

## Observability
Audit.

## Rollback Strategy
Disable endpoint.

## Architecture Risks
Enumeration.

## ADRs
None.
""",
        encoding="utf-8",
    )
    (workspace / "tech-design.md").write_text(
        """# Technical Design: Reset Password

## Implementation Summary
Add reset request and completion flow.

## Modules And Responsibilities
Auth service owns orchestration.

## Contracts
Internal API contract.

## API/Event/Schema Details
Request and completion payloads are structured.

## Core Code Sketches
PasswordResetService.requestReset(email).

## Data Model
Token hash and expiry.

## Error Handling
Generic public responses.

## Security Considerations
Do not store plaintext token.

## Test Strategy
Unit and integration tests.

## Migration Plan
Add token table.

## Rollback Plan
Disable reset endpoints.

## Integration Notes
Email service required.
""",
        encoding="utf-8",
    )
    (workspace / "slices.yaml").write_text(
        yaml.safe_dump(
            {
                "artifact_contract_version": "0.1.0",
                "feature_key": "auth/reset-password",
                "slices": [
                    {
                        "id": "S-001",
                        "title": "Request reset token",
                        "linked_requirements": ["FR-001"],
                        "linked_acceptance_criteria": ["AC-001"],
                        "linked_adrs": [],
                        "linked_contracts": [],
                        "dependencies": [],
                        "priority": 1,
                        "expected_touchpoints": ["src/auth/password_reset.py", "tests/test_password_reset.py"],
                        "scope_confidence": "medium",
                        "tdd": {
                            "failing_test_file": "tests/test_password_reset.py",
                            "red_command": "python -m unittest tests.test_password_reset",
                            "expected_failure": "password reset not implemented",
                            "green_command": "python -m unittest tests.test_password_reset",
                        },
                        "verification_commands": ["python -m unittest discover -s tests"],
                        "review_focus": ["No account enumeration"],
                        "evidence_status": "pending",
                        "status": "pending",
                        "iteration_budget": 10,
                        "rollback_point": "pre-slice git state",
                        "independent_verification": "python -m unittest tests.test_password_reset",
                        "failure_triage_notes": "Classify failures as test_expected, implementation_bug, test_bug, design_gap, scope_change, environment_failure, or flaky.",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    with (workspace / "execution.md").open("a", encoding="utf-8") as handle:
        handle.write(
            """

## Docs Consulted: Architecture

- `.ai/knowledge/architecture-overview.md`: reused known boundary.

## Docs Consulted: Feature Contract

- `.agents/pipeline-core/references/generated-templates/feature-template.md`: used required contract sections.

## Docs Consulted: Technical Design

- `.ai/knowledge/tech-design-overview.md`: reused implementation artifact rules.

## Docs Consulted: Slicing

- `.agents/pipeline-core/references/generated-templates/slice-template.yaml`: used required TDD slice fields.
"""
        )


if __name__ == "__main__":
    unittest.main()
