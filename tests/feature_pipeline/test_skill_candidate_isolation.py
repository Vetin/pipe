import shutil
import tempfile
import unittest
from pathlib import Path

try:
    from plan_test_helpers import BENCH, ignore_generated_pipeline_lab, make_repo, run
except ModuleNotFoundError:
    from tests.feature_pipeline.plan_test_helpers import BENCH, ignore_generated_pipeline_lab, make_repo, run


ROOT = Path(__file__).resolve().parents[2]


class SkillCandidateIsolationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="skill-candidate-test-"))
        self.repo = make_repo(self.tempdir)
        shutil.copytree(ROOT / "pipeline-lab", self.repo / "pipeline-lab", dirs_exist_ok=True, ignore=ignore_generated_pipeline_lab)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_candidate_skill_must_be_quarantined_and_not_named_skill_md(self):
        bad = self.repo / ".agents/skills/nfp-02-feature-contract/SKILL.md"
        bad.parent.mkdir(parents=True)
        bad.write_text("# Active skill\n", encoding="utf-8")
        workspace = self.tempdir / "workspace"
        workspace.mkdir()

        result = run(
            [
                "python",
                str(BENCH),
                "score-run",
                "--workspace",
                str(workspace),
                "--scenario",
                "auth-reset-password",
                "--candidate",
                str(bad),
                "--output",
                str(self.repo / "pipeline-lab/runs/score.yaml"),
            ],
            self.repo,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(list((ROOT / ".agents/skill-lab/quarantine").glob("*/**/SKILL.md")))
        self.assertIn("candidate must be under .agents/skill-lab/quarantine", result.stderr)


if __name__ == "__main__":
    unittest.main()
