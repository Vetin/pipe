import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

try:
    from test_planning_readiness import write_planning_artifacts
except ModuleNotFoundError:
    from tests.feature_pipeline.test_planning_readiness import write_planning_artifacts


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".agents/pipeline-core/scripts/featurectl.py"


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class GatesAndEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="evidence-test-"))
        self.repo = self.make_repo()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def make_repo(self):
        repo = self.tempdir / "repo"
        repo.mkdir()
        run(["git", "init", "-b", "main"], repo)
        run(["git", "config", "user.email", "test@example.com"], repo)
        run(["git", "config", "user.name", "Test User"], repo)
        (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
        run(["git", "add", "README.md"], repo)
        run(["git", "commit", "-m", "initial"], repo)
        return repo

    def test_gate_set_updates_state_and_execution_without_approvals_file(self):
        workspace = self.create_workspace()

        result = run(
            [
                sys.executable,
                str(SCRIPT),
                "gate",
                "set",
                "--workspace",
                str(workspace),
                "--gate",
                "feature_contract",
                "--status",
                "approved",
                "--by",
                "user",
                "--note",
                "Approved",
            ],
            self.repo,
        )

        state = yaml.safe_load((workspace / "state.yaml").read_text(encoding="utf-8"))
        execution = (workspace / "execution.md").read_text(encoding="utf-8")
        self.assertIn("status: approved", result.stdout)
        self.assertEqual(state["gates"]["feature_contract"], "approved")
        self.assertEqual(state["gates"]["architecture"], "pending")
        self.assertIn("old_status=pending new_status=approved by=user", execution)
        self.assertFalse(list(workspace.rglob("approvals.yaml")))
        self.assertFalse(list(workspace.rglob("handoff.md")))

    def test_mark_stale_cascades_downstream_flags(self):
        workspace = self.create_workspace("run-stale")

        run(
            [
                sys.executable,
                str(SCRIPT),
                "mark-stale",
                "--workspace",
                str(workspace),
                "--artifact",
                "architecture",
                "--reason",
                "changed ADR",
            ],
            self.repo,
        )

        state = yaml.safe_load((workspace / "state.yaml").read_text(encoding="utf-8"))
        self.assertTrue(state["stale"]["tech_design"])
        self.assertTrue(state["stale"]["slices"])
        self.assertTrue(state["stale"]["evidence"])
        self.assertTrue(state["stale"]["feature_card"])
        self.assertTrue(state["stale"]["canonical_docs"])
        self.assertFalse(state["stale"]["feature"])

    def test_record_evidence_and_complete_slice(self):
        workspace = self.ready_workspace()

        self.record_full_evidence(workspace)
        result = run(
            [
                sys.executable,
                str(SCRIPT),
                "complete-slice",
                "--workspace",
                str(workspace),
                "--slice",
                "S-001",
                "--diff-hash",
                "abc123",
            ],
            self.repo,
        )

        self.assertIn("slice_complete: S-001", result.stdout)
        manifest = yaml.safe_load((workspace / "evidence/manifest.yaml").read_text(encoding="utf-8"))
        slices = yaml.safe_load((workspace / "slices.yaml").read_text(encoding="utf-8"))
        self.assertEqual(manifest["slices"]["S-001"]["diff_hash"], "abc123")
        self.assertEqual(slices["slices"][0]["status"], "complete")
        self.assertEqual(slices["slices"][0]["evidence_status"], "complete")

    def test_complete_slice_fails_when_green_is_before_red(self):
        workspace = self.ready_workspace("run-bad-order")
        self.record_full_evidence(workspace, red_ts="2026-05-11T10:00:00Z", green_ts="2026-05-11T09:00:00Z")

        result = run(
            [
                sys.executable,
                str(SCRIPT),
                "complete-slice",
                "--workspace",
                str(workspace),
                "--slice",
                "S-001",
                "--diff-hash",
                "abc123",
            ],
            self.repo,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("red evidence timestamp must be before green", result.stdout)

    def test_validate_evidence_detects_unknown_slice(self):
        workspace = self.ready_workspace("run-unknown-slice")
        (workspace / "evidence").mkdir(exist_ok=True)
        (workspace / "evidence/manifest.yaml").write_text(
            yaml.safe_dump(
                {
                    "artifact_contract_version": "0.1.0",
                    "feature_key": "auth/reset-password",
                    "slices": {"S-999": {}},
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace), "--evidence"], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("evidence manifest references unknown slice: S-999", result.stdout)

    def create_workspace(self, run_id="run-gates"):
        run(
            [
                sys.executable,
                str(SCRIPT),
                "new",
                "--domain",
                "auth",
                "--title",
                "Reset Password",
                "--run-id",
                run_id,
            ],
            self.repo,
        )
        return self.tempdir / f"worktrees/auth-reset-password-{run_id}/.ai/feature-workspaces/auth/reset-password--{run_id}"

    def ready_workspace(self, run_id="run-evidence"):
        workspace = self.create_workspace(run_id)
        write_planning_artifacts(workspace)
        state_path = workspace / "state.yaml"
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        state["current_step"] = "tdd_implementation"
        state["gates"]["feature_contract"] = "approved"
        state["gates"]["architecture"] = "approved"
        state["gates"]["tech_design"] = "approved"
        state["gates"]["slicing_readiness"] = "approved"
        state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
        return workspace

    def record_full_evidence(self, workspace, *, red_ts="2026-05-11T09:00:00Z", green_ts="2026-05-11T10:00:00Z"):
        commands = [
            ("red", "python -m unittest tests.test_password_reset", "expected failure", red_ts),
            ("green", "python -m unittest tests.test_password_reset", "ok", green_ts),
            ("verification", "python -m unittest discover -s tests", "ok", "2026-05-11T11:00:00Z"),
            ("review", "", "No critical findings.", "2026-05-11T12:00:00Z"),
        ]
        for phase, command, output, timestamp in commands:
            cmd = [
                sys.executable,
                str(SCRIPT),
                "record-evidence",
                "--workspace",
                str(workspace),
                "--slice",
                "S-001",
                "--phase",
                phase,
                "--output",
                output,
                "--timestamp",
                timestamp,
            ]
            if command:
                cmd.extend(["--command", command])
            if phase in {"red", "green"}:
                cmd.extend(["--git-state", "## feature branch\n"])
            run(cmd, self.repo)


if __name__ == "__main__":
    unittest.main()
