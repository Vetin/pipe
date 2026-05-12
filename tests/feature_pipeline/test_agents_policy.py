import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class AgentsPolicyTests(unittest.TestCase):
    def test_agents_uses_selective_pipeline_triggers(self):
        content = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

        for token in (
            "Use the Native Feature Pipeline for substantial feature-building work",
            "new product or platform features",
            "cross-module behavior changes",
            "public API, schema, event, contract, migration, or integration changes",
            "Use our own technology while changing it",
        ):
            self.assertIn(token, content)
        for token in (
            "Use lightweight repair mode",
            "one-file script bugfixes",
            "test-only fixes",
            "formatting",
            "small fixture updates",
        ):
            self.assertIn(token, content)
        self.assertNotIn("If there is doubt, use the pipeline", content)

    def test_agents_defines_automatic_start_and_resume_sequence(self):
        content = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

        for token in (
            "Run `featurectl.py init --profile-project` only when `.ai/knowledge` is missing, stale, or explicitly requested",
            ".ai/knowledge/project-index.yaml",
            ".ai/knowledge/discovered-signals.md",
            "featurectl.py new",
            "dedicated feature worktree",
            "nfp-00-intake",
            "nfp-12-promote",
            "featurectl.py load-docset",
            "featurectl.py validate --workspace <workspace>",
        ):
            self.assertIn(token, content)

    def test_agents_includes_pipeline_self_modification_guardrail(self):
        content = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

        for token in (
            "Use the pipeline for pipeline self-modification when the change affects behavior, architecture, validation, generated artifacts, or user-facing workflow",
            "minimum needed to run `init`, `new`, and `validate`",
            "record the repair in `execution.md`",
        ):
            self.assertIn(token, content)

    def test_project_init_is_bootstrap_not_feature_step(self):
        content = (ROOT / ".agents/skills/project-init/SKILL.md").read_text(encoding="utf-8")

        for token in (
            "project-init is a repository bootstrap/profile skill",
            "not an `nfp-*` feature-run step",
            ".ai/knowledge/discovered-signals.md",
        ):
            self.assertIn(token, content)

    def test_legacy_native_feature_reference_root_is_archived(self):
        content = (ROOT / "skills/native-feature-pipeline/references/README.md").read_text(encoding="utf-8")

        for token in (
            "Legacy methodology extraction",
            "Do not use this directory as a production skill reference root",
            ".agents/pipeline-core/references",
        ):
            self.assertIn(token, content)

    def test_constitution_declares_review_tier_defaults(self):
        content = (ROOT / ".ai/constitution.md").read_text(encoding="utf-8")

        self.assertIn("default_review_tier: strict_review", content)
        self.assertIn("security_sensitive_review_tier: enterprise_review", content)

    def test_showcase_runners_install_agents_policy_for_nested_codex(self):
        script_paths = [
            ROOT / "pipeline-lab/showcases/scripts/run_codex_e2e_case.py",
            ROOT / "pipeline-lab/showcases/scripts/run_real_showcase.py",
            ROOT / "pipeline-lab/showcases/scripts/implement_real_showcase.py",
        ]

        for script_path in script_paths:
            with self.subTest(script=script_path.name):
                content = script_path.read_text(encoding="utf-8")
                self.assertIn('ROOT / "AGENTS.md"', content)
                self.assertIn('worktree / "AGENTS.md"', content)


if __name__ == "__main__":
    unittest.main()
