import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TAXONOMY = ROOT / "tests/feature_pipeline/README.md"


class FeaturePipelineTestTaxonomyTests(unittest.TestCase):
    def test_test_taxonomy_documents_major_test_groups(self):
        self.assertTrue(TAXONOMY.exists())
        content = TAXONOMY.read_text(encoding="utf-8")

        for expected in (
            "Featurectl Unit Tests",
            "Artifact Validation Tests",
            "Skill Contract Tests",
            "Mock Codex Runner Tests",
            "Real Codex E2E Tests",
            "Pipelinebench Tests",
            "Manual Preflight Tests",
            "test_real_codex_conversation.py",
            "test_pipelinebench.py",
            "test_manual_check_preflight.py",
        ):
            self.assertIn(expected, content)


if __name__ == "__main__":
    unittest.main()
