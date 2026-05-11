import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

try:
    from plan_test_helpers import FEATURECTL, approve_planning, create_workspace, make_repo, record_full_evidence, run, write_planning_artifacts
except ModuleNotFoundError:
    from tests.feature_pipeline.plan_test_helpers import FEATURECTL, approve_planning, create_workspace, make_repo, record_full_evidence, run, write_planning_artifacts


class PromotionTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="promotion-test-"))
        self.repo = make_repo(self.tempdir)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_promote_requires_complete_finish_state(self):
        workspace = create_workspace(self.tempdir, self.repo, run_id="run-promotion")
        write_planning_artifacts(workspace)
        approve_planning(workspace, current_step="finish")
        record_full_evidence(self.repo, workspace)
        run(["python", str(FEATURECTL), "complete-slice", "--workspace", str(workspace), "--slice", "S-001", "--diff-hash", "abc123"], self.repo)
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
                    "file_refs": ["feature.md"],
                    "reproduction_or_reasoning": "No blocking findings remain.",
                    "fix_verification_command": "python -m unittest discover -s tests",
                    "re_review_required": False,
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        result = run(["python", str(FEATURECTL), "promote", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("promotion requires finish gate complete", result.stdout)


if __name__ == "__main__":
    unittest.main()
