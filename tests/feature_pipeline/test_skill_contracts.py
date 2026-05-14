import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / ".agents/skills"
REFERENCES = ROOT / ".agents/pipeline-core/references"


class SkillContractTests(unittest.TestCase):
    def test_every_nfp_skill_has_uniform_contract_fields(self):
        skills = sorted(SKILLS_DIR.glob("nfp-*/SKILL.md"))
        self.assertEqual(len(skills), 13)

        for skill in skills:
            content = skill.read_text(encoding="utf-8")
            with self.subTest(skill=skill.parent.name):
                for field in (
                    "name:",
                    "description:",
                    "version:",
                    "pipeline_contract_version:",
                    "## Skill Contract",
                    "Inputs:",
                    "Owned artifacts:",
                    "Forbidden actions:",
                    "Validation command:",
                    "Docs consulted requirement:",
                    "Next step fallback:",
                ):
                    self.assertIn(field, content)

    def test_official_artifact_model_documents_event_scope_and_review_boundaries(self):
        artifact_model = (REFERENCES / "artifact-model.md").read_text(encoding="utf-8")
        workflow = (REFERENCES / "workflow-state-machine.md").read_text(encoding="utf-8")
        review = (REFERENCES / "review-and-verification.md").read_text(encoding="utf-8")
        apex_template = (REFERENCES / "generated-templates/apex-template.md").read_text(encoding="utf-8")
        execution_template = (REFERENCES / "generated-templates/execution-template.md").read_text(encoding="utf-8")

        for expected in (
            "events.yaml",
            "machine-readable event history",
            "execution.md",
            "human-readable run journal",
            "scope-change.md",
            "state.yaml",
        ):
            self.assertIn(expected, artifact_model)

        for expected in (
            "featurectl.py step set",
            "featurectl.py scope-change",
            "validate --planning-package",
            "validate --implementation",
        ):
            self.assertIn(expected, workflow)

        for expected in (
            "reviews/*.yaml",
            "reviews/*-review.md",
            "YAML findings",
            "Markdown summaries",
        ):
            self.assertIn(expected, review)

        self.assertIn("events.yaml", apex_template)
        self.assertIn("events.yaml = machine-readable event source of truth", execution_template)
        self.assertIn("execution.md = human-readable run narrative", execution_template)

    def test_key_skills_expose_new_operational_rules(self):
        readiness = (SKILLS_DIR / "nfp-06-readiness/SKILL.md").read_text(encoding="utf-8")
        tdd = (SKILLS_DIR / "nfp-08-tdd-implementation/SKILL.md").read_text(encoding="utf-8")
        review = (SKILLS_DIR / "nfp-09-review/SKILL.md").read_text(encoding="utf-8")

        self.assertIn("--planning-package", readiness)
        self.assertIn("--implementation", readiness)
        self.assertIn("planning-stop", readiness)

        self.assertIn("## Subagent Availability", tdd)
        self.assertIn("subagents_used", tdd)
        self.assertIn("fallback_reason", tdd)

        self.assertIn("reviews/*.yaml", review)
        self.assertIn("reviews/*-review.md", review)
        self.assertIn("Markdown summaries", review)


if __name__ == "__main__":
    unittest.main()
