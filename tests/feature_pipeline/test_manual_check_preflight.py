import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = ROOT / "pipeline-lab/manual-check/preflight.sh"
README = ROOT / "pipeline-lab/manual-check/README.md"
REAL_CODEX_TEST = ROOT / "tests/feature_pipeline/test_real_codex_conversation.py"


class ManualCheckPreflightTests(unittest.TestCase):
    def test_manual_preflight_script_runs_required_pipeline_checks(self):
        self.assertTrue(PREFLIGHT.exists())
        self.assertTrue(os.access(PREFLIGHT, os.X_OK))
        content = PREFLIGHT.read_text(encoding="utf-8")

        for expected in (
            "featurectl.py",
            "status --workspace",
            "validate --workspace",
            "--planning-package",
            "implementation-ready --workspace",
            "worktree-status --workspace",
            "git status --short",
            "git branch --show-current",
        ):
            self.assertIn(expected, content)

    def test_manual_check_readme_documents_test_matrix_and_pass_criteria(self):
        self.assertTrue(README.exists())
        content = README.read_text(encoding="utf-8")

        for expected in (
            "Mock prompt-runner tests",
            "Real Codex behavioral e2e",
            "RUN_REAL_CODEX_E2E=1",
            "Manual pass criteria",
            "feature worktree exists",
            "no implementation code changed before gates",
            "featurectl.py validate --workspace",
        ):
            self.assertIn(expected, content)

    def test_manual_check_readme_documents_behavioral_skill_matrix(self):
        self.assertTrue(README.exists())
        content = README.read_text(encoding="utf-8")

        for expected in (
            "Behavioral Skill Matrix",
            "nfp-00-intake",
            "nfp-01-context",
            "nfp-02-feature-contract",
            "nfp-03-architecture",
            "nfp-04-tech-design",
            "nfp-05-slicing",
            "nfp-08-tdd-implementation",
            "nfp-09-review",
            "Under-specified real Codex e2e",
            "red-before-green evidence",
            "reviews/*.yaml",
        ):
            self.assertIn(expected, content)

    def test_real_codex_conversation_test_is_opt_in_and_behavioral(self):
        self.assertTrue(REAL_CODEX_TEST.exists())
        content = REAL_CODEX_TEST.read_text(encoding="utf-8")

        for expected in (
            "RUN_REAL_CODEX_E2E",
            "CODEX_BIN",
            "Create reset password. Build planning through implementation plan and stop.",
            "--planning-package",
            "feature.md",
            "architecture.md",
            "tech-design.md",
            "slices.yaml",
            "no implementation code changed before gates",
        ):
            self.assertIn(expected, content)


if __name__ == "__main__":
    unittest.main()
