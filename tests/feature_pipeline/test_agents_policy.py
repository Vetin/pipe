import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class AgentsPolicyTests(unittest.TestCase):
    def test_agents_requires_pipeline_for_feature_building(self):
        content = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

        for token in (
            "The Native Feature Pipeline is mandatory",
            "build, implement, add, change, or improve behavior",
            "If there is doubt, use the pipeline",
            "Use our own technology while changing it",
        ):
            self.assertIn(token, content)

    def test_agents_defines_automatic_start_and_resume_sequence(self):
        content = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

        for token in (
            "python .agents/pipeline-core/scripts/featurectl.py init --profile-project",
            ".ai/knowledge/project-index.yaml",
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
            "changes to `.agents`, `.ai/pipeline-docs`, `skills`, `featurectl.py`",
            "Do not bypass the pipeline because a change is \"internal\"",
            "minimum needed to run `init`, `new`, and `validate`",
            "record the repair in `execution.md`",
        ):
            self.assertIn(token, content)

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
