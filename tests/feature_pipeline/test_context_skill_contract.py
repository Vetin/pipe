import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ContextSkillContractTests(unittest.TestCase):
    def test_context_skill_bootstraps_provisional_knowledge_from_real_sources(self):
        content = (ROOT / ".agents/skills/nfp-01-context/SKILL.md").read_text(encoding="utf-8")

        self.assertIn("rg \"<domain>\"", content)
        self.assertIn("Status: provisional", content)
        self.assertIn("Needs human review: yes", content)
        self.assertIn("Sources inspected:", content)
        self.assertIn("Do not invent architecture", content)
        self.assertIn("featurectl.py validate", content)


if __name__ == "__main__":
    unittest.main()
