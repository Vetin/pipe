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


class DocsetLoadingTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="docset-test-"))
        self.repo = self.make_repo()
        shutil.copytree(ROOT / ".ai/pipeline-docs", self.repo / ".ai/pipeline-docs", dirs_exist_ok=True)
        shutil.copytree(ROOT / ".ai/knowledge", self.repo / ".ai/knowledge", dirs_exist_ok=True)
        shutil.copytree(ROOT / ".ai/features", self.repo / ".ai/features", dirs_exist_ok=True)
        shutil.copytree(ROOT / ".agents/pipeline-core/references", self.repo / ".agents/pipeline-core/references", dirs_exist_ok=True)
        shutil.copytree(ROOT / "methodology", self.repo / "methodology", dirs_exist_ok=True)
        shutil.copy2(ROOT / ".ai/constitution.md", self.repo / ".ai/constitution.md")

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

    def test_load_docset_lists_required_optional_and_suggested_docs(self):
        workspace = self.repo / ".ai/feature-workspaces/auth/reset-password--run-docset"
        workspace.mkdir(parents=True)

        result = run(
            [sys.executable, str(SCRIPT), "load-docset", "--workspace", str(workspace), "--step", "architecture"],
            self.repo,
        )

        self.assertIn("step: architecture", result.stdout)
        self.assertIn("required_docs:", result.stdout)
        self.assertIn(".ai/pipeline-docs/global/architecture-standards.md", result.stdout)
        self.assertIn(".ai/knowledge/architecture-overview.md", result.stdout)
        self.assertIn(".ai/knowledge/project-index.yaml", result.stdout)
        self.assertIn(".ai/knowledge/project-snapshot.md", result.stdout)
        self.assertIn("optional_docs:", result.stdout)
        self.assertIn("missing_docs:\n  none", result.stdout)
        self.assertIn("selected_alternatives:", result.stdout)
        self.assertIn("suggested_related_files:", result.stdout)
        self.assertFalse((workspace / "architecture.md").exists())
        self.assertFalse(list(workspace.rglob("approvals.yaml")))
        self.assertFalse(list(workspace.rglob("handoff.md")))

    def test_load_docset_reports_missing_docs_without_crashing(self):
        workspace = self.repo / ".ai/feature-workspaces/auth/reset-password--run-missing-doc"
        workspace.mkdir(parents=True)
        (self.repo / ".ai/knowledge/architecture-overview.md").unlink()

        result = run(
            [sys.executable, str(SCRIPT), "load-docset", "--workspace", str(workspace), "--step", "architecture"],
            self.repo,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("missing_docs:", result.stdout)
        self.assertIn(".ai/knowledge/architecture-overview.md", result.stdout)

    def test_load_docset_unknown_step_fails_clearly(self):
        workspace = self.repo / ".ai/feature-workspaces/auth/reset-password--run-unknown-docset"
        workspace.mkdir(parents=True)

        result = run(
            [sys.executable, str(SCRIPT), "load-docset", "--workspace", str(workspace), "--step", "unknown"],
            self.repo,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown docset step", result.stderr)

    def test_context_skill_documents_provisional_knowledge_bootstrap(self):
        content = (ROOT / ".agents/skills/nfp-01-context/SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Status: provisional", content)
        self.assertIn("Needs human review: yes", content)
        self.assertIn("Sources inspected:", content)
        self.assertIn(".ai/knowledge/project-overview.md", content)
        self.assertIn(".ai/knowledge/project-index.yaml", content)
        self.assertIn(".ai/knowledge/project-snapshot.md", content)
        self.assertIn(".ai/knowledge/module-map.md", content)
        self.assertIn(".ai/knowledge/architecture-overview.md", content)

    def test_architecture_gate_requires_architecture_and_docs_consulted(self):
        workspace = self.create_workspace()
        self.write_feature_contract(workspace)
        self.set_gates(workspace, feature_contract="approved", architecture="drafted", current_step="tech_design")

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("architecture gate requires architecture.md", result.stdout)

    def test_architecture_artifact_with_docs_consulted_validates(self):
        workspace = self.create_workspace("run-arch-valid")
        self.write_feature_contract(workspace)
        self.write_architecture(workspace)
        self.append_docs_consulted(workspace)
        self.set_gates(workspace, feature_contract="approved", architecture="drafted", current_step="tech_design")

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace)], self.repo)

        self.assertIn("validation: pass", result.stdout)

    def create_workspace(self, run_id="run-arch-missing"):
        run(["git", "add", ".ai", "README.md"], self.repo)
        run(["git", "commit", "-m", f"seed docs {run_id}"], self.repo)
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

    def write_architecture(self, workspace):
        (workspace / "architecture.md").write_text(
            """# Architecture: Reset Password

## System Context
Auth owns reset flow.

## Component Interactions
Web calls Auth API, which calls token store and email service.

## Diagrams
See diagrams when needed.

## Security Model
Tokens are secret and not stored as plaintext.

## Failure Modes
Email delivery can fail.

## Observability
Audit reset attempts.

## Rollback Strategy
Disable endpoint and preserve login.

## Architecture Risks
Account enumeration.

## ADRs
None for this sample.
""",
            encoding="utf-8",
        )

    def append_docs_consulted(self, workspace):
        with (workspace / "execution.md").open("a", encoding="utf-8") as handle:
            handle.write(
                """

## Docs Consulted: Architecture

- `.ai/knowledge/architecture-overview.md`: reused worktree-first boundary.

## Docs Consulted: Feature Contract

- `.agents/pipeline-core/references/generated-templates/feature-template.md`: used required sections.
"""
            )

    def set_gates(self, workspace, *, feature_contract, architecture, current_step):
        state_path = workspace / "state.yaml"
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        state["current_step"] = current_step
        state["gates"]["feature_contract"] = feature_contract
        state["gates"]["architecture"] = architecture
        state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
