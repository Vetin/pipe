import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

try:
    from test_gates_and_evidence import GatesAndEvidenceTests, run as run_cmd
    from test_planning_readiness import write_planning_artifacts
except ModuleNotFoundError:
    from tests.feature_pipeline.test_gates_and_evidence import GatesAndEvidenceTests, run as run_cmd
    from tests.feature_pipeline.test_planning_readiness import write_planning_artifacts


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

    def test_finish_validation_requires_feature_card_operational_sections(self):
        workspace = self.completed_workspace("run-finish-sections")
        (workspace / "feature-card.md").write_text("# Feature Card: auth/reset-password\n\nThin summary.\n", encoding="utf-8")

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("feature-card.md missing heading: ## Manual Validation", result.stdout)
        self.assertIn("feature-card.md missing heading: ## Verification Debt", result.stdout)
        self.assertIn("feature-card.md missing heading: ## Claim Provenance", result.stdout)
        self.assertIn("feature-card.md missing heading: ## Rollback Guidance", result.stdout)
        self.assertIn("feature-card.md missing heading: ## Shared Knowledge Updates", result.stdout)

    def test_finish_validation_requires_shared_knowledge_paths(self):
        workspace = self.completed_workspace("run-finish-knowledge-paths")
        content = (workspace / "feature-card.md").read_text(encoding="utf-8")
        content = content.replace(".ai/knowledge/", "knowledge/")
        (workspace / "feature-card.md").write_text(content, encoding="utf-8")

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("feature-card.md must describe shared knowledge updates using .ai/knowledge paths", result.stdout)

    def test_promote_copies_workspace_and_regenerates_index(self):
        workspace = self.completed_workspace("run-promote")

        result = run([sys.executable, str(SCRIPT), "promote", "--workspace", str(workspace)], self.repo)

        canonical = self.repo / ".ai/features/auth/reset-password"
        index = yaml.safe_load((self.repo / ".ai/features/index.yaml").read_text(encoding="utf-8"))
        overview = (self.repo / ".ai/features/overview.md").read_text(encoding="utf-8")
        self.assertIn("promotion: complete", result.stdout)
        self.assertTrue((canonical / "feature-card.md").exists())
        self.assertEqual(index["features"][0]["feature_key"], "auth/reset-password")
        self.assertEqual(index["features"][0]["path"], ".ai/features/auth/reset-password")
        self.assertIn("auth/reset-password", overview)
        self.assertEqual(yaml.safe_load((canonical / "feature.yaml").read_text(encoding="utf-8"))["status"], "complete")
        source_feature = yaml.safe_load((workspace / "feature.yaml").read_text(encoding="utf-8"))
        source_state = yaml.safe_load((workspace / "state.yaml").read_text(encoding="utf-8"))
        self.assertEqual(source_feature["status"], "promoted-readonly")
        self.assertEqual(source_state["lifecycle"], "promoted-readonly")
        self.assertTrue(source_state["read_only"])
        validation = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(canonical)], self.repo)
        self.assertIn("validation: pass", validation.stdout)
        workspace_validation = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace)], self.repo)
        self.assertIn("validation: pass", workspace_validation.stdout)

    def test_validate_rejects_stale_canonical_overview(self):
        workspace = self.completed_workspace("run-stale-overview")
        run([sys.executable, str(SCRIPT), "promote", "--workspace", str(workspace)], self.repo)
        (self.repo / ".ai/features/overview.md").write_text(
            "# Feature Overview\n\nNo canonical features have been promoted yet.\n",
            encoding="utf-8",
        )

        result = run(
            [sys.executable, str(SCRIPT), "validate", "--workspace", str(self.repo / ".ai/features/auth/reset-password")],
            self.repo,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(".ai/features/overview.md missing canonical feature auth/reset-password", result.stdout)

    def test_validate_rejects_complete_canonical_feature_with_draft_status(self):
        workspace = self.completed_workspace("run-draft-canonical")
        run([sys.executable, str(SCRIPT), "promote", "--workspace", str(workspace)], self.repo)
        canonical_feature_path = self.repo / ".ai/features/auth/reset-password/feature.yaml"
        canonical_feature = yaml.safe_load(canonical_feature_path.read_text(encoding="utf-8"))
        canonical_feature["status"] = "draft"
        canonical_feature_path.write_text(yaml.safe_dump(canonical_feature, sort_keys=False), encoding="utf-8")

        result = run(
            [sys.executable, str(SCRIPT), "validate", "--workspace", str(self.repo / ".ai/features/auth/reset-password")],
            self.repo,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("canonical feature auth/reset-password is indexed complete but feature.yaml status is draft", result.stdout)

    def test_validate_rejects_active_workspace_for_complete_canonical_feature(self):
        workspace = self.completed_workspace("run-active-complete")
        run([sys.executable, str(SCRIPT), "promote", "--workspace", str(workspace)], self.repo)
        active = self.completed_workspace("run-active-conflict")

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(active)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("active workspace auth/reset-password duplicates complete canonical feature without inactive lifecycle", result.stdout)

    def test_validate_rejects_legacy_promoted_workspace_without_readonly_lifecycle(self):
        workspace = self.completed_workspace("run-active-legacy-promoted")
        run([sys.executable, str(SCRIPT), "promote", "--workspace", str(workspace)], self.repo)
        active = self.completed_workspace("run-legacy-promoted-conflict")
        feature_path = active / "feature.yaml"
        feature = yaml.safe_load(feature_path.read_text(encoding="utf-8"))
        feature["status"] = "promoted"
        feature_path.write_text(yaml.safe_dump(feature, sort_keys=False), encoding="utf-8")

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(active)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("active workspace auth/reset-password duplicates complete canonical feature without inactive lifecycle", result.stdout)

    def test_validate_rejects_stale_current_run_state(self):
        workspace = self.completed_workspace("run-stale-current-run-state")
        execution_path = workspace / "execution.md"
        execution = execution_path.read_text(encoding="utf-8")
        execution = execution.replace("Current step: finish", "Current step: slicing")
        execution_path.write_text(execution, encoding="utf-8")

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("execution.md Current Run State current step slicing does not match state.yaml current_step finish", result.stdout)

    def test_validate_rejects_deprecated_latest_status_sections(self):
        workspace = self.completed_workspace("run-deprecated-latest-status")
        execution_path = workspace / "execution.md"
        execution_path.write_text(
            execution_path.read_text(encoding="utf-8")
            + "\n## Latest Status\n\nCurrent step: finish\nNext recommended skill: nfp-12-promote\nBlocking issues: none\nLast updated: 2026-05-12T13:00:00Z\n",
            encoding="utf-8",
        )

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("execution.md must not contain deprecated ## Latest Status section", result.stdout)

    def test_validate_rejects_active_legacy_current_next_sections(self):
        workspace = self.completed_workspace("run-legacy-current-step")
        execution_path = workspace / "execution.md"
        execution_path.write_text(
            execution_path.read_text(encoding="utf-8")
            + "\n## Current Step\n\nfinish\n\n## Next Step\n\nnfp-12-promote\n",
            encoding="utf-8",
        )

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("execution.md contains active legacy ## Current Step section outside History", result.stdout)
        self.assertIn("execution.md contains active legacy ## Next Step section outside History", result.stdout)

    def test_validate_rejects_duplicate_completed_slice_events(self):
        workspace = self.completed_workspace("run-duplicate-slice-complete")
        execution_path = workspace / "execution.md"
        execution = execution_path.read_text(encoding="utf-8")
        execution = execution.replace(
            "\n## History",
            "\n- 2026-05-12T13:01:00Z event_type=slice_completed slice=S-001 attempt=1\n\n## History",
        )
        execution_path.write_text(execution, encoding="utf-8")

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("execution.md duplicate completed slice event for S-001", result.stdout)

    def test_validate_rejects_retry_without_attempt_or_reason(self):
        workspace = self.completed_workspace("run-retry-without-semantics")
        execution_path = workspace / "execution.md"
        execution = execution_path.read_text(encoding="utf-8")
        execution = execution.replace(
            "\n## History",
            "\n- 2026-05-12T13:01:00Z completed slice S-001 with evidence retry\n\n## History",
        )
        execution_path.write_text(execution, encoding="utf-8")

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("execution.md retry completed slice event for S-001 missing attempt and reason", result.stdout)

    def test_promote_conflict_aborts_by_default(self):
        first = self.completed_workspace("run-promote-first")
        run([sys.executable, str(SCRIPT), "promote", "--workspace", str(first)], self.repo)
        second = self.completed_workspace("run-promote-second")

        result = run([sys.executable, str(SCRIPT), "promote", "--workspace", str(second)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("canonical feature already exists", result.stderr)

    def test_promote_archive_as_variant_archives_incoming_workspace(self):
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
        source_feature = yaml.safe_load((second / "feature.yaml").read_text(encoding="utf-8"))
        source_state = yaml.safe_load((second / "state.yaml").read_text(encoding="utf-8"))
        self.assertTrue((archived / "feature.yaml").exists())
        self.assertEqual(canonical["run_id"], "run-promote-archive-first")
        self.assertEqual(source_feature["status"], "archived")
        self.assertEqual(source_state["lifecycle"], "archived")
        self.assertTrue(source_state["read_only"])

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
        (workspace / "reviews/verification-review.md").write_text(
            "# Verification Review\n\nPassed.\n\n## Manual Validation\n\nNot applicable.\n\n## Verification Debt\n\nNone.\n",
            encoding="utf-8",
        )
        (workspace / "evidence/final-verification-output.log").write_text("tests passed\n", encoding="utf-8")
        (workspace / "feature-card.md").write_text(
            """# Feature Card: auth/reset-password

Intent, architecture, contracts, tests, reviews, and evidence summarized.

## Manual Validation

Not applicable.

## Verification Debt

None.

## Claim Provenance

Final claims map to feature.md, slices.yaml, evidence/manifest.yaml, and final verification output.

## Rollback Guidance

Disable reset endpoints and preserve existing login behavior.

## Shared Knowledge Updates

- `.ai/knowledge/features-overview.md`: reset password feature memory updated.
- `.ai/knowledge/architecture-overview.md`: auth reset topology recorded.
- `.ai/knowledge/module-map.md`: auth/token/email ownership recorded.
- `.ai/knowledge/integration-map.md`: email delivery communication recorded.
""",
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
        execution_path = workspace / "execution.md"
        execution = execution_path.read_text(encoding="utf-8")
        current_state = """
## Current Run State

Current step: finish
Next recommended skill: nfp-12-promote
Blocking issues: none
Last updated: 2026-05-12T12:00:00Z
"""
        if "## Current Run State" in execution:
            prefix, rest = execution.split("## Current Run State", 1)
            next_heading = rest.find("\n## ")
            suffix = rest[next_heading:] if next_heading != -1 else ""
            execution_path.write_text(prefix.rstrip() + "\n\n" + current_state + suffix, encoding="utf-8")
        elif "## Latest Status" in execution:
            prefix, rest = execution.split("## Latest Status", 1)
            next_heading = rest.find("\n## ")
            suffix = rest[next_heading:] if next_heading != -1 else ""
            execution_path.write_text(prefix.rstrip() + "\n\n" + current_state + suffix, encoding="utf-8")
        else:
            execution_path.write_text(execution.rstrip() + "\n\n" + current_state, encoding="utf-8")
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
