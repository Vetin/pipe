import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ContextSkillContractTests(unittest.TestCase):
    def test_context_skill_bootstraps_provisional_knowledge_from_real_sources(self):
        content = (ROOT / ".agents/skills/nfp-01-context/SKILL.md").read_text(encoding="utf-8")

        self.assertIn("rg \"<domain>\"", content)
        self.assertIn("Status: provisional", content)
        self.assertIn("featurectl.py init --profile-project", content)
        self.assertIn(".ai/knowledge/project-index.yaml", content)
        self.assertIn(".ai/knowledge/project-snapshot.md", content)
        self.assertIn("Needs human review: yes", content)
        self.assertIn("Sources inspected:", content)
        self.assertIn("Do not invent architecture", content)
        self.assertIn("featurectl.py validate", content)

    def test_project_init_skill_profiles_features_for_brownfield_context(self):
        content = (ROOT / ".agents/skills/project-init/SKILL.md").read_text(encoding="utf-8")

        self.assertIn("name: project-init", content)
        self.assertIn("featurectl.py init --profile-project", content)
        self.assertIn(".ai/knowledge/project-index.yaml", content)
        self.assertIn("feature_catalog", content)
        self.assertIn("Current Feature Picture", content)
        self.assertIn("raw ideas", content)
        self.assertIn("executive research", content)
        self.assertIn("business analysis", content)
        self.assertIn("No implementation code is changed", content)

    def test_context_skill_prioritizes_canonical_memory_over_lab_signals(self):
        content = (ROOT / ".agents/skills/nfp-01-context/SKILL.md").read_text(encoding="utf-8")

        features_index = content.index(".ai/knowledge/features-overview.md")
        discovered_index = content.index(".ai/knowledge/discovered-signals.md")
        self.assertLess(features_index, discovered_index)
        self.assertIn("Canonical feature memory is the first retrieval layer", content)
        self.assertIn("Treat `kind: lab_signal` entries as pipeline-lab or benchmark context only", content)
        self.assertIn("Do not use lab signals as product architecture evidence", content)
        self.assertIn("verify it by reading the cited source path", content)


if __name__ == "__main__":
    unittest.main()
