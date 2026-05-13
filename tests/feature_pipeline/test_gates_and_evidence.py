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
        events = yaml.safe_load((workspace / "events.yaml").read_text(encoding="utf-8"))
        self.assertIn("status: approved", result.stdout)
        self.assertEqual(state["gates"]["feature_contract"], "approved")
        self.assertEqual(state["gates"]["architecture"], "pending")
        self.assertIn("event_type=gate_status_changed", execution)
        self.assertIn("gate=feature_contract old_status=pending new_status=approved by=user", execution)
        self.assertEqual(events["events"][-1]["event_type"], "gate_status_changed")
        self.assertEqual(events["events"][-1]["gate"], "feature_contract")
        self.assertEqual(events["events"][-1]["old_status"], "pending")
        self.assertEqual(events["events"][-1]["new_status"], "approved")
        self.assertFalse(list(workspace.rglob("approvals.yaml")))
        self.assertFalse(list(workspace.rglob("handoff.md")))

    def test_events_schema_exists_and_describes_required_event_shapes(self):
        schema_path = ROOT / ".agents/pipeline-core/scripts/schemas/events.schema.json"

        self.assertTrue(schema_path.exists())
        schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
        self.assertIn("events", schema["required"])
        schema_text = schema_path.read_text(encoding="utf-8")
        for token in (
            "gate_status_changed",
            "slice_completed",
            "slice_retry_completed",
            "feature_promoted",
            "canonical_path",
            "supersedes",
        ):
            self.assertIn(token, schema_text)

    def test_validate_rejects_invalid_events_sidecar_records(self):
        workspace = self.create_workspace("run-invalid-events")
        events_path = workspace / "events.yaml"
        events = yaml.safe_load(events_path.read_text(encoding="utf-8"))
        events["events"].append(
            {
                "timestamp": "2026-05-13T15:20:00Z",
                "event_type": "gate_status_changed",
                "feature_key": "auth/reset-password",
                "old_status": "pending",
                "new_status": "approved",
            }
        )
        events_path.write_text(yaml.safe_dump(events, sort_keys=False), encoding="utf-8")

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace)], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("events.yaml event 2 gate_status_changed missing gate", result.stdout)

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
        execution = (workspace / "execution.md").read_text(encoding="utf-8")
        events = yaml.safe_load((workspace / "events.yaml").read_text(encoding="utf-8"))
        self.assertTrue(state["stale"]["tech_design"])
        self.assertTrue(state["stale"]["slices"])
        self.assertTrue(state["stale"]["evidence"])
        self.assertTrue(state["stale"]["feature_card"])
        self.assertTrue(state["stale"]["canonical_docs"])
        self.assertFalse(state["stale"]["feature"])
        self.assertIn("event_type=artifact_marked_stale", execution)
        self.assertIn("artifact=architecture", execution)
        self.assertEqual(events["events"][-1]["event_type"], "artifact_marked_stale")
        self.assertEqual(events["events"][-1]["artifact"], "architecture")
        self.assertEqual(events["events"][-1]["marked_stale"], ["tech_design", "slices", "evidence", "feature_card", "canonical_docs"])

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
        events = yaml.safe_load((workspace / "events.yaml").read_text(encoding="utf-8"))
        self.assertIn("completion_identity_policy", manifest)
        self.assertEqual(manifest["slices"]["S-001"]["diff_hash"], "abc123")
        self.assertEqual(slices["slices"][0]["status"], "complete")
        self.assertEqual(slices["slices"][0]["evidence_status"], "complete")
        self.assertIn(
            "event_type=slice_completed slice=S-001 attempt=1 reason=initial",
            (workspace / "execution.md").read_text(encoding="utf-8"),
        )
        self.assertEqual(events["events"][-1]["event_type"], "slice_completed")
        self.assertEqual(events["events"][-1]["slice"], "S-001")
        self.assertEqual(events["events"][-1]["attempt"], 1)

    def test_complete_slice_stores_semantic_label_outside_diff_hash(self):
        workspace = self.ready_workspace("run-semantic-label")

        self.record_full_evidence(workspace)
        run(
            [
                sys.executable,
                str(SCRIPT),
                "complete-slice",
                "--workspace",
                str(workspace),
                "--slice",
                "S-001",
                "--diff-hash",
                "s001-source-truth-hardening",
            ],
            self.repo,
        )

        manifest = yaml.safe_load((workspace / "evidence/manifest.yaml").read_text(encoding="utf-8"))
        slice_entry = manifest["slices"]["S-001"]
        self.assertEqual(slice_entry["change_label"], "s001-source-truth-hardening")
        self.assertNotIn("diff_hash", slice_entry)

    def test_complete_slice_is_idempotent_without_explicit_retry(self):
        workspace = self.ready_workspace("run-idempotent-complete")

        self.record_full_evidence(workspace)
        run(
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
        manifest_before = (workspace / "evidence/manifest.yaml").read_text(encoding="utf-8")

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
                "changed456",
            ],
            self.repo,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("slice S-001 is already complete; use --append-retry to record an explicit retry", result.stderr)
        self.assertEqual((workspace / "evidence/manifest.yaml").read_text(encoding="utf-8"), manifest_before)

    def test_complete_slice_retry_requires_reason_and_records_attempt(self):
        workspace = self.ready_workspace("run-retry-complete")

        self.record_full_evidence(workspace)
        run(
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
        missing_reason = run(
            [
                sys.executable,
                str(SCRIPT),
                "complete-slice",
                "--workspace",
                str(workspace),
                "--slice",
                "S-001",
                "--diff-hash",
                "changed456",
                "--append-retry",
            ],
            self.repo,
            check=False,
        )
        self.assertNotEqual(missing_reason.returncode, 0)
        self.assertIn("--append-retry requires --retry-reason", missing_reason.stderr)

        retry = run(
            [
                sys.executable,
                str(SCRIPT),
                "complete-slice",
                "--workspace",
                str(workspace),
                "--slice",
                "S-001",
                "--diff-hash",
                "changed456",
                "--append-retry",
                "--retry-reason",
                "rerun-after-review",
            ],
            self.repo,
        )

        self.assertIn("slice_complete: S-001", retry.stdout)
        manifest = yaml.safe_load((workspace / "evidence/manifest.yaml").read_text(encoding="utf-8"))
        execution = (workspace / "execution.md").read_text(encoding="utf-8")
        events = yaml.safe_load((workspace / "events.yaml").read_text(encoding="utf-8"))
        self.assertEqual(manifest["slices"]["S-001"]["retries"][0]["attempt"], 2)
        self.assertEqual(manifest["slices"]["S-001"]["retries"][0]["reason"], "rerun-after-review")
        self.assertEqual(manifest["slices"]["S-001"]["retries"][0]["change_label"], "changed456")
        self.assertNotIn("diff_hash", manifest["slices"]["S-001"]["retries"][0])
        self.assertIn(
            "event_type=slice_retry_completed slice=S-001 attempt=2 reason=rerun-after-review supersedes=attempt-1",
            execution,
        )
        self.assertEqual(events["events"][-1]["event_type"], "slice_retry_completed")
        self.assertEqual(events["events"][-1]["attempt"], 2)
        self.assertEqual(events["events"][-1]["supersedes"], "attempt-1")

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

    def test_validate_evidence_rejects_semantic_label_in_diff_hash(self):
        workspace = self.ready_workspace("run-semantic-diff-hash")
        self.record_full_evidence(workspace)
        manifest_path = workspace / "evidence/manifest.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        manifest["slices"]["S-001"]["diff_hash"] = "s001-semantic-label"
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

        result = run([sys.executable, str(SCRIPT), "validate", "--workspace", str(workspace), "--evidence"], self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("S-001 diff_hash must be a hexadecimal hash; use change_label for semantic labels", result.stdout)

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
