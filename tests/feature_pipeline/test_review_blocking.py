import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

try:
    from plan_test_helpers import FEATURECTL, approve_planning, create_workspace, make_repo, run, write_planning_artifacts
except ModuleNotFoundError:
    from tests.feature_pipeline.plan_test_helpers import FEATURECTL, approve_planning, create_workspace, make_repo, run, write_planning_artifacts


class ReviewBlockingTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="review-blocking-test-"))
        self.repo = make_repo(self.tempdir)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_critical_review_finding_blocks_verification(self):
        workspace = create_workspace(self.tempdir, self.repo, run_id="run-review-blocking")
        write_planning_artifacts(workspace)
        approve_planning(workspace, current_step="review")
        (workspace / "reviews/security.yaml").write_text(
            yaml.safe_dump(
                {
                    "artifact_contract_version": "0.1.0",
                    "review_id": "REV-001",
                    "tier": "strict_review",
                    "severity": "critical",
                    "finding": "Missing replay protection",
                    "artifact": "tech-design.md",
                    "evidence": "Contract review",
                    "recommendation": "Add nonce or timestamp replay window",
                    "blocking": True,
                    "linked_requirement_ids": ["FR-001"],
                    "linked_slice_ids": ["S-001"],
                    "file_refs": ["tech-design.md"],
                    "reproduction_or_reasoning": "Webhook signature can be replayed without freshness.",
                    "fix_verification_command": "python -m unittest tests.test_webhooks",
                    "re_review_required": True,
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        result = run(["python", str(FEATURECTL), "validate", "--workspace", str(workspace), "--review"], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("critical review finding blocks verification", result.stdout)


if __name__ == "__main__":
    unittest.main()
