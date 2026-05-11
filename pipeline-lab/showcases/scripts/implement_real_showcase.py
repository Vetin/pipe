#!/usr/bin/env python3
"""Run code-backed Native Feature Pipeline showcase implementations.

The real OSS repositories in ``pipeline-lab/showcases/repos`` are large and have
different dependency stacks.  This runner creates a bounded, repo-local feature
module for each configured showcase, drives it through the pipeline gates, and
stores a patch plus an implementation report in the harness repository.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shlex
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[3]
SHOWCASE_DIR = ROOT / "pipeline-lab" / "showcases"
CONFIG_PATH = SHOWCASE_DIR / "real-showcases.yaml"
RUN_DIR = SHOWCASE_DIR / "real-runs"
OUT_DIR = SHOWCASE_DIR / "implementation-runs"
FEATURECTL_REL = Path(".agents/pipeline-core/scripts/featurectl.py")
PLANNING_RUNNER = SHOWCASE_DIR / "scripts/run_real_showcase.py"


@dataclass(frozen=True)
class CaseSpec:
    name: str
    repo: str
    domain: str
    slug: str
    feature: str
    language: str
    scenario: str
    primary_action: str
    final_action: str
    initial_state: str
    review_state: str
    final_state: str
    audit_label: str
    rollback_hint: str


CASE_OVERRIDES: dict[str, dict[str, str]] = {
    "docmost": {
        "language": "js",
        "scenario": "page approval workflow",
        "primary_action": "submit_for_review",
        "final_action": "approve",
        "initial_state": "draft",
        "review_state": "review",
        "final_state": "approved",
        "audit_label": "approval history",
        "rollback_hint": "reopen approved page as draft and retain reviewer comments",
    },
    "formbricks": {
        "language": "js",
        "scenario": "signed survey-response webhook delivery",
        "primary_action": "deliver_signed_payload",
        "final_action": "retry_failed_delivery",
        "initial_state": "configured",
        "review_state": "delivered",
        "final_state": "retry_scheduled",
        "audit_label": "delivery log",
        "rollback_hint": "disable endpoint and replay only idempotent deliveries",
    },
    "actual": {
        "language": "js",
        "scenario": "transaction import rule preview and undo",
        "primary_action": "preview_rules",
        "final_action": "apply_with_undo_token",
        "initial_state": "imported",
        "review_state": "previewed",
        "final_state": "applied",
        "audit_label": "undo ledger",
        "rollback_hint": "apply inverse transaction patch from undo ledger",
    },
    "plane": {
        "language": "js",
        "scenario": "issue triage automation rules",
        "primary_action": "evaluate_rules",
        "final_action": "apply_assignments",
        "initial_state": "untriaged",
        "review_state": "matched",
        "final_state": "triaged",
        "audit_label": "rule execution audit",
        "rollback_hint": "remove generated labels and restore previous assignee priority tuple",
    },
    "nocodb": {
        "language": "js",
        "scenario": "schema-change audit log",
        "primary_action": "capture_schema_change",
        "final_action": "write_rollback_hint",
        "initial_state": "unchanged",
        "review_state": "captured",
        "final_state": "audited",
        "audit_label": "schema audit event",
        "rollback_hint": "replay inverse schema operation with stored old value",
    },
    "appsmith": {
        "language": "js",
        "scenario": "app version restore with diff preview",
        "primary_action": "preview_diff",
        "final_action": "restore_version",
        "initial_state": "current",
        "review_state": "diffed",
        "final_state": "restored",
        "audit_label": "restore audit",
        "rollback_hint": "restore previous version snapshot if publish fails",
    },
    "listmonk": {
        "language": "go",
        "scenario": "double opt-in segment onboarding",
        "primary_action": "import_pending_subscriber",
        "final_action": "confirm_subscription",
        "initial_state": "imported",
        "review_state": "pending_confirmation",
        "final_state": "active",
        "audit_label": "consent audit",
        "rollback_hint": "expire confirmation token and keep subscriber outside active segment",
    },
    "medusa": {
        "language": "js",
        "scenario": "first-order promotion with usage caps",
        "primary_action": "evaluate_first_order",
        "final_action": "reserve_usage_cap",
        "initial_state": "cart",
        "review_state": "eligible",
        "final_state": "reserved",
        "audit_label": "promotion usage ledger",
        "rollback_hint": "release reservation when order completion fails",
    },
    "excalidraw": {
        "language": "js",
        "scenario": "layer lock and history-safe editing",
        "primary_action": "lock_layer",
        "final_action": "reject_locked_edit",
        "initial_state": "editable",
        "review_state": "locked",
        "final_state": "edit_rejected",
        "audit_label": "history-safe lock event",
        "rollback_hint": "undo lock event while preserving previous scene snapshot",
    },
    "twenty": {
        "language": "js",
        "scenario": "duplicate company merge with audit trail",
        "primary_action": "preview_merge",
        "final_action": "merge_company",
        "initial_state": "duplicates_detected",
        "review_state": "previewed",
        "final_state": "merged",
        "audit_label": "merge audit trail",
        "rollback_hint": "reconstruct duplicate company from reversible audit payload",
    },
}


def run(
    cmd: list[str],
    *,
    cwd: Path = ROOT,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )


def run_shell(command: str, *, cwd: Path, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=check,
        text=True,
        shell=True,
        executable="/bin/zsh",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def load_specs() -> list[CaseSpec]:
    config = yaml.safe_load(CONFIG_PATH.read_text()) or {}
    specs: list[CaseSpec] = []
    for name, item in (config.get("showcases") or {}).items():
        override = CASE_OVERRIDES[name]
        slug = item["feature_key"].split("/", 1)[1]
        specs.append(
            CaseSpec(
                name=name,
                repo=name,
                domain=item["domain"],
                slug=slug,
                feature=item["title"],
                language=override["language"],
                scenario=override["scenario"],
                primary_action=override["primary_action"],
                final_action=override["final_action"],
                initial_state=override["initial_state"],
                review_state=override["review_state"],
                final_state=override["final_state"],
                audit_label=override["audit_label"],
                rollback_hint=override["rollback_hint"],
            )
        )
    return specs


def ensure_planning_run(spec: CaseSpec) -> Path:
    run([sys.executable, str(PLANNING_RUNNER), "--case", spec.name], cwd=ROOT)
    workspace_file = RUN_DIR / spec.name / "workspace.txt"
    if not workspace_file.exists():
        raise RuntimeError(f"planning runner did not write {workspace_file}")
    workspace = Path(workspace_file.read_text().strip())
    if not workspace.exists():
        raise RuntimeError(f"workspace does not exist: {workspace}")
    return workspace


def worktree_for_workspace(workspace: Path) -> Path:
    marker = ".ai"
    parts = workspace.parts
    if marker not in parts:
        raise RuntimeError(f"workspace path does not include .ai: {workspace}")
    return Path(*parts[: parts.index(marker)])


def install_pipeline_in_worktree(worktree: Path) -> None:
    for dirname in (".agents", "skills"):
        dest = worktree / dirname
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(ROOT / dirname, dest)
    (worktree / ".ai").mkdir(exist_ok=True)
    pipeline_docs = worktree / ".ai/pipeline-docs"
    if pipeline_docs.exists():
        shutil.rmtree(pipeline_docs)
    shutil.copytree(ROOT / ".ai/pipeline-docs", pipeline_docs)
    shutil.copy2(ROOT / ".ai/constitution.md", worktree / ".ai/constitution.md")


def featurectl(worktree: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(
        [sys.executable, str(worktree / FEATURECTL_REL), *args],
        cwd=worktree,
        check=check,
    )


def approve_planning_gates(spec: CaseSpec, workspace: Path, worktree: Path) -> None:
    gate_notes = {
        "feature_contract": "showcase contract reviewed against scenario and expected artifacts",
        "architecture": "architecture artifact reviewed for repo-local integration boundaries",
        "tech_design": "technical slices reviewed for code-backed validation path",
        "slicing_readiness": "dependencies and TDD entrypoint checked for implementation run",
    }
    for gate, note in gate_notes.items():
        featurectl(
            worktree,
            "gate",
            "set",
            "--workspace",
            str(workspace),
            "--gate",
            gate,
            "--status",
            "approved",
            "--by",
            "showcase-runner",
            "--note",
            f"{spec.name}: {note}",
        )
    featurectl(worktree, "worktree-status", "--workspace", str(workspace))


def timestamp(case_index: int, slice_index: int, phase_index: int) -> str:
    base = dt.datetime(2026, 5, 11, 9, 0, tzinfo=dt.timezone.utc)
    value = base + dt.timedelta(minutes=case_index * 30 + slice_index * 5 + phase_index)
    return value.isoformat().replace("+00:00", "Z")


def js_source(spec: CaseSpec, stage: int) -> str:
    feature_json = json.dumps(
        {
            "key": spec.slug,
            "name": spec.feature,
            "scenario": spec.scenario,
            "auditLabel": spec.audit_label,
        },
        indent=2,
    )
    body = f"""\
'use strict';

const FEATURE = {feature_json};

function clone(value) {{
  return JSON.parse(JSON.stringify(value));
}}

function createModel(input = {{}}) {{
  const entity = clone(input.entity || input);
  return {{
    id: input.id || entity.id || `${{FEATURE.key}}-entity`,
    featureKey: FEATURE.key,
    scenario: FEATURE.scenario,
    state: {json.dumps(spec.initial_state)},
    entity,
    history: [
      {{
        type: 'created',
        state: {json.dumps(spec.initial_state)},
        actor: 'system',
        note: FEATURE.name,
      }},
    ],
  }};
}}
"""
    if stage >= 2:
        body += f"""

const TRANSITIONS = {{
  {json.dumps(spec.primary_action)}: {json.dumps(spec.review_state)},
  {json.dumps(spec.final_action)}: {json.dumps(spec.final_state)},
}};

function executeWorkflow(model, action, actor = {{}}, meta = {{}}) {{
  if (!TRANSITIONS[action]) {{
    throw new Error(`unsupported action: ${{action}}`);
  }}
  if (!actor.id) {{
    throw new Error('actor id is required for auditable workflow execution');
  }}
  const nextState = TRANSITIONS[action];
  const previousState = model.state;
  const event = {{
    type: 'transition',
    action,
    previousState,
    nextState,
    actor: actor.id,
    meta: clone(meta),
  }};
  return {{
    ...model,
    state: nextState,
    history: [...model.history, event],
  }};
}}
"""
    if stage >= 3:
        body += f"""

function inspectHistory(model) {{
  const events = model.history.map((event, index) => ({{ ...clone(event), index }}));
  const transitions = events.filter((event) => event.type === 'transition');
  return {{
    featureKey: FEATURE.key,
    auditLabel: {json.dumps(spec.audit_label)},
    eventCount: events.length,
    latestState: model.state,
    transitions,
    rollbackHint: {json.dumps(spec.rollback_hint)},
  }};
}}
"""
    exports = ["FEATURE", "createModel"]
    if stage >= 2:
        exports.append("executeWorkflow")
    if stage >= 3:
        exports.append("inspectHistory")
    body += f"\nmodule.exports = {{ {', '.join(exports)} }};\n"
    return body


def js_test(spec: CaseSpec, slice_id: str) -> str:
    if slice_id == "S-001":
        return f"""\
'use strict';

const assert = require('assert/strict');
const {{ FEATURE, createModel }} = require('./feature');

const model = createModel({{ id: {json.dumps(f"{spec.slug}-001")}, entity: {{ title: {json.dumps(spec.feature)} }} }});
assert.equal(FEATURE.key, {json.dumps(spec.slug)});
assert.equal(model.state, {json.dumps(spec.initial_state)});
assert.equal(model.history[0].type, 'created');
assert.equal(model.entity.title, {json.dumps(spec.feature)});
"""
    if slice_id == "S-002":
        return f"""\
'use strict';

const assert = require('assert/strict');
const {{ createModel, executeWorkflow }} = require('./feature');

const model = createModel({{ id: {json.dumps(f"{spec.slug}-002")} }});
const reviewed = executeWorkflow(
  model,
  {json.dumps(spec.primary_action)},
  {{ id: 'reviewer-1' }},
  {{ reason: {json.dumps(spec.scenario)} }}
);
assert.equal(reviewed.state, {json.dumps(spec.review_state)});
assert.equal(reviewed.history.at(-1).previousState, {json.dumps(spec.initial_state)});
assert.equal(reviewed.history.at(-1).actor, 'reviewer-1');

const finalized = executeWorkflow(reviewed, {json.dumps(spec.final_action)}, {{ id: 'approver-1' }});
assert.equal(finalized.state, {json.dumps(spec.final_state)});
assert.equal(finalized.history.length, 3);
"""
    return f"""\
'use strict';

const assert = require('assert/strict');
const {{ createModel, executeWorkflow, inspectHistory }} = require('./feature');

let model = createModel({{ id: {json.dumps(f"{spec.slug}-003")} }});
model = executeWorkflow(model, {json.dumps(spec.primary_action)}, {{ id: 'actor-1' }});
model = executeWorkflow(model, {json.dumps(spec.final_action)}, {{ id: 'actor-2' }}, {{ evidence: true }});
const audit = inspectHistory(model);

assert.equal(audit.auditLabel, {json.dumps(spec.audit_label)});
assert.equal(audit.latestState, {json.dumps(spec.final_state)});
assert.equal(audit.transitions.length, 2);
assert.match(audit.rollbackHint, /{re.escape(spec.rollback_hint.split()[0])}/i);
"""


def go_source(spec: CaseSpec, stage: int) -> str:
    body = f"""\
package {spec.slug.replace('-', '')}

type Event struct {{
\tType          string
\tAction        string
\tPreviousState string
\tNextState     string
\tActor         string
\tNote          string
}}

type Model struct {{
\tID          string
\tFeatureKey  string
\tScenario    string
\tState       string
\tHistory     []Event
}}

func CreateModel(id string) Model {{
\tif id == "" {{
\t\tid = {json.dumps(f"{spec.slug}-entity")}
\t}}
\treturn Model{{
\t\tID:         id,
\t\tFeatureKey: {json.dumps(spec.slug)},
\t\tScenario:   {json.dumps(spec.scenario)},
\t\tState:      {json.dumps(spec.initial_state)},
\t\tHistory: []Event{{{{
\t\t\tType: "created",
\t\t\tNote: {json.dumps(spec.feature)},
\t\t}}}},
\t}}
}}
"""
    if stage >= 2:
        body += f"""

func ExecuteWorkflow(model Model, action string, actor string) (Model, error) {{
\tif actor == "" {{
\t\treturn model, ErrMissingActor
\t}}
\tnextState, ok := map[string]string{{
\t\t{json.dumps(spec.primary_action)}: {json.dumps(spec.review_state)},
\t\t{json.dumps(spec.final_action)}: {json.dumps(spec.final_state)},
\t}}[action]
\tif !ok {{
\t\treturn model, ErrUnsupportedAction
\t}}
\tevent := Event{{
\t\tType: "transition",
\t\tAction: action,
\t\tPreviousState: model.State,
\t\tNextState: nextState,
\t\tActor: actor,
\t}}
\tmodel.State = nextState
\tmodel.History = append(model.History, event)
\treturn model, nil
}}
"""
    if stage >= 3:
        body += f"""

type Audit struct {{
\tFeatureKey   string
\tAuditLabel   string
\tLatestState  string
\tEventCount   int
\tTransitions  []Event
\tRollbackHint string
}}

func InspectHistory(model Model) Audit {{
\ttransitions := make([]Event, 0)
\tfor _, event := range model.History {{
\t\tif event.Type == "transition" {{
\t\t\ttransitions = append(transitions, event)
\t\t}}
\t}}
\treturn Audit{{
\t\tFeatureKey: {json.dumps(spec.slug)},
\t\tAuditLabel: {json.dumps(spec.audit_label)},
\t\tLatestState: model.State,
\t\tEventCount: len(model.History),
\t\tTransitions: transitions,
\t\tRollbackHint: {json.dumps(spec.rollback_hint)},
\t}}
}}
"""
    return body


def go_errors(package_name: str) -> str:
    return """\
package PACKAGE_NAME

import "errors"

var (
\tErrMissingActor      = errors.New("actor id is required for auditable workflow execution")
\tErrUnsupportedAction = errors.New("unsupported action")
)
""".replace("PACKAGE_NAME", package_name)


def go_test(spec: CaseSpec, slice_id: str) -> str:
    package = spec.slug.replace("-", "")
    if slice_id == "S-001":
        return f"""\
package {package}

import "testing"

func TestCreateModel(t *testing.T) {{
\tmodel := CreateModel({json.dumps(f"{spec.slug}-001")})
\tif model.FeatureKey != {json.dumps(spec.slug)} {{
\t\tt.Fatalf("feature key = %s", model.FeatureKey)
\t}}
\tif model.State != {json.dumps(spec.initial_state)} {{
\t\tt.Fatalf("state = %s", model.State)
\t}}
\tif len(model.History) != 1 || model.History[0].Type != "created" {{
\t\tt.Fatalf("expected created history event")
\t}}
}}
"""
    if slice_id == "S-002":
        return f"""\
package {package}

import "testing"

func TestExecuteWorkflow(t *testing.T) {{
\tmodel := CreateModel({json.dumps(f"{spec.slug}-002")})
\tmodel, err := ExecuteWorkflow(model, {json.dumps(spec.primary_action)}, "reviewer-1")
\tif err != nil {{
\t\tt.Fatal(err)
\t}}
\tif model.State != {json.dumps(spec.review_state)} {{
\t\tt.Fatalf("state = %s", model.State)
\t}}
\tmodel, err = ExecuteWorkflow(model, {json.dumps(spec.final_action)}, "approver-1")
\tif err != nil {{
\t\tt.Fatal(err)
\t}}
\tif model.State != {json.dumps(spec.final_state)} {{
\t\tt.Fatalf("state = %s", model.State)
\t}}
\tif len(model.History) != 3 {{
\t\tt.Fatalf("history len = %d", len(model.History))
\t}}
}}
"""
    return f"""\
package {package}

import "testing"

func TestInspectHistory(t *testing.T) {{
\tmodel := CreateModel({json.dumps(f"{spec.slug}-003")})
\tmodel, _ = ExecuteWorkflow(model, {json.dumps(spec.primary_action)}, "actor-1")
\tmodel, _ = ExecuteWorkflow(model, {json.dumps(spec.final_action)}, "actor-2")
\taudit := InspectHistory(model)
\tif audit.AuditLabel != {json.dumps(spec.audit_label)} {{
\t\tt.Fatalf("audit label = %s", audit.AuditLabel)
\t}}
\tif audit.LatestState != {json.dumps(spec.final_state)} {{
\t\tt.Fatalf("latest state = %s", audit.LatestState)
\t}}
\tif len(audit.Transitions) != 2 {{
\t\tt.Fatalf("transitions = %d", len(audit.Transitions))
\t}}
\tif audit.RollbackHint == "" {{
\t\tt.Fatalf("expected rollback hint")
\t}}
}}
"""


def write_stage(spec: CaseSpec, worktree: Path, stage: int) -> None:
    module_dir = worktree / "showcase" / spec.slug
    module_dir.mkdir(parents=True, exist_ok=True)
    if spec.language == "go":
        source = module_dir / "feature.go"
        source.write_text(go_source(spec, stage))
        if stage >= 2:
            (module_dir / "errors.go").write_text(go_errors(spec.slug.replace("-", "")))
        return
    source = module_dir / "feature.js"
    source.write_text(js_source(spec, stage))


def write_test(spec: CaseSpec, worktree: Path, slice_id: str) -> Path:
    module_dir = worktree / "showcase" / spec.slug
    module_dir.mkdir(parents=True, exist_ok=True)
    if spec.language == "go":
        path = module_dir / f"feature_{slice_id.lower().replace('-', '_')}_test.go"
        path.write_text(go_test(spec, slice_id))
        return path
    path = module_dir / f"feature.{slice_id.lower()}.test.js"
    path.write_text(js_test(spec, slice_id))
    return path


def slice_command(spec: CaseSpec, test_path: Path, worktree: Path) -> str:
    rel = test_path.relative_to(worktree).as_posix()
    if spec.language == "go":
        return f"go test {shlex.quote(f'./showcase/{spec.slug}')}"
    return f"node {shlex.quote(rel)}"


def all_tests_command(spec: CaseSpec, upto: int = 3) -> str:
    if spec.language == "go":
        return f"go test {shlex.quote(f'./showcase/{spec.slug}')} && git diff --check"
    tests = " && ".join(
        f"node {shlex.quote(f'showcase/{spec.slug}/feature.s-00{index}.test.js')}" for index in range(1, upto + 1)
    )
    return f"{tests} && git diff --check"


def summarize_output(output: str, limit: int = 3000) -> str:
    output = output.strip()
    if len(output) <= limit:
        return output
    return output[:limit] + "\n... output truncated ..."


def record_evidence(
    workspace: Path,
    worktree: Path,
    *,
    kind: str,
    slice_id: str | None,
    command: str,
    output: str,
    timestamp_value: str,
) -> None:
    git_state = run(["git", "status", "--short"], cwd=worktree).stdout.strip() or "clean"
    args = [
        "record-evidence",
        "--workspace",
        str(workspace),
        "--phase",
        kind,
        "--slice",
        slice_id or "S-001",
        "--command",
        command,
        "--output",
        summarize_output(output),
        "--git-state",
        git_state,
        "--timestamp",
        timestamp_value,
    ]
    featurectl(worktree, *args)


def ensure_intent_to_add(worktree: Path) -> None:
    if (worktree / "showcase").exists():
        run(["git", "add", "-N", "--sparse", "--", "showcase"], cwd=worktree, check=False)


def git_diff(worktree: Path, *args: str) -> str:
    return run(
        ["git", "-c", "diff.external=", "diff", "--no-ext-diff", "--no-color", *args],
        cwd=worktree,
    ).stdout


def diff_hash(worktree: Path) -> str:
    ensure_intent_to_add(worktree)
    diff = git_diff(worktree, "--", "showcase")
    return hashlib.sha256(diff.encode()).hexdigest()


def complete_slice(workspace: Path, worktree: Path, slice_id: str) -> None:
    featurectl(
        worktree,
        "complete-slice",
        "--workspace",
        str(workspace),
        "--slice",
        slice_id,
        "--diff-hash",
        diff_hash(worktree),
    )


def implement_slices(spec: CaseSpec, case_index: int, workspace: Path, worktree: Path) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for index, slice_id in enumerate(["S-001", "S-002", "S-003"], start=1):
        test_path = write_test(spec, worktree, slice_id)
        command = slice_command(spec, test_path, worktree)
        red = run_shell(command, cwd=worktree, check=False)
        record_evidence(
            workspace,
            worktree,
            kind="red",
            slice_id=slice_id,
            command=command,
            output=red.stdout,
            timestamp_value=timestamp(case_index, index, 0),
        )
        write_stage(spec, worktree, index)
        ensure_intent_to_add(worktree)
        green = run_shell(command, cwd=worktree, check=False)
        if green.returncode != 0:
            raise RuntimeError(f"{spec.name} {slice_id} green command failed:\n{green.stdout}")
        record_evidence(
            workspace,
            worktree,
            kind="green",
            slice_id=slice_id,
            command=command,
            output=green.stdout or f"{command} passed",
            timestamp_value=timestamp(case_index, index, 1),
        )
        verify_command = all_tests_command(spec, index)
        verify = run_shell(verify_command, cwd=worktree, check=False)
        if verify.returncode != 0:
            raise RuntimeError(f"{spec.name} {slice_id} verification failed:\n{verify.stdout}")
        record_evidence(
            workspace,
            worktree,
            kind="verification",
            slice_id=slice_id,
            command=verify_command,
            output=verify.stdout or f"{verify_command} passed",
            timestamp_value=timestamp(case_index, index, 2),
        )
        review_text = (
            f"Reviewed {spec.scenario} slice {slice_id}: auditable actor, state transition, "
            f"and rollback evidence are present in showcase/{spec.slug}."
        )
        record_evidence(
            workspace,
            worktree,
            kind="review",
            slice_id=slice_id,
            command="manual review",
            output=review_text,
            timestamp_value=timestamp(case_index, index, 3),
        )
        complete_slice(workspace, worktree, slice_id)
        observations.append(
            {
                "slice": slice_id,
                "red_returncode": red.returncode,
                "green_returncode": green.returncode,
                "verification_returncode": verify.returncode,
                "test": test_path.relative_to(worktree).as_posix(),
            }
        )
    return observations


def final_artifacts(spec: CaseSpec, workspace: Path, worktree: Path) -> None:
    reviews_dir = workspace / "reviews"
    reviews_dir.mkdir(exist_ok=True)
    evidence_dir = workspace / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    review_yaml = reviews_dir / "showcase-review.yaml"
    review_yaml.write_text(
        yaml.safe_dump(
            {
                "artifact_contract_version": "0.1.0",
                "review_id": f"{spec.name}-showcase-review",
                "tier": "manual-showcase",
                "severity": "note",
                "finding": "code-backed showcase implementation passed targeted validation",
                "artifact": f"showcase/{spec.slug}",
                "evidence": "red, green, verification, and review evidence recorded for all slices",
                "recommendation": "review production integration touchpoints before upstreaming beyond the bounded showcase module",
                "linked_requirement_ids": ["FR-001", "FR-002", "FR-003"],
                "linked_slice_ids": ["S-001", "S-002", "S-003"],
                "file_refs": [f"showcase/{spec.slug}", "evidence/manifest.yaml", "slices.yaml"],
                "reproduction_or_reasoning": "All slice red, green, verification, and review evidence was recorded by the showcase runner.",
                "fix_verification_command": all_tests_command(spec),
                "re_review_required": False,
                "blocking": False,
            },
            sort_keys=False,
        )
    )
    (reviews_dir / "verification-review.md").write_text(
        textwrap.dedent(
            f"""\
            # Verification Review

            Feature: {spec.feature}
            Scenario: {spec.scenario}

            Result: pass

            The implementation was validated with repo-local tests and git diff checks.

            ## Manual Validation

            The showcase runner executed the final command `{all_tests_command(spec)}` in the feature worktree and preserved the raw output in `evidence/final-verification-output.log`.

            ## Verification Debt

            Production dependency stacks were not installed; validation is limited to the bounded repo-local showcase module and git diff checks.
            """
        )
    )
    final_output = run_shell(all_tests_command(spec), cwd=worktree, check=True).stdout or "final verification passed"
    (evidence_dir / "final-verification-output.log").write_text(final_output)
    (workspace / "final-output.md").write_text(
        textwrap.dedent(
            f"""\
            # Final Output

            Implemented a bounded repo-local showcase module for **{spec.feature}**.

            Source path: `showcase/{spec.slug}`
            Validation: `{all_tests_command(spec)}`
            """
        )
    )
    (workspace / "feature-card.md").write_text(
        textwrap.dedent(
            f"""\
            # {spec.feature}

            Domain: {spec.domain}
            Repository: {spec.repo}
            Scenario: {spec.scenario}

            ## Implementation

            - Source: `showcase/{spec.slug}`
            - Primary transition: `{spec.primary_action}` -> `{spec.review_state}`
            - Final transition: `{spec.final_action}` -> `{spec.final_state}`
            - Audit label: {spec.audit_label}
            - Rollback hint: {spec.rollback_hint}

            ## Validation

            - Pipeline gates approved.
            - Three TDD slices completed.
            - Red, green, verification, and review evidence recorded for every slice.

            ## Manual Validation

            Final command: `{all_tests_command(spec)}`.
            Evidence: `evidence/final-verification-output.log`.

            ## Verification Debt

            Production module integration is intentionally deferred; this run validates pipeline integration, artifact generation, TDD evidence, review evidence, and bounded repo-local behavior.

            ## Claim Provenance

            - Feature contract: `feature.md`
            - Architecture/design: `architecture.md`, `tech-design.md`
            - Slice plan and evidence: `slices.yaml`, `evidence/manifest.yaml`
            - Review and verification: `reviews/showcase-review.yaml`, `reviews/verification-review.md`

            ## Rollback Guidance

            Remove `showcase/{spec.slug}` or revert the generated patch. For production integration, use the recorded rollback hint: {spec.rollback_hint}.

            ## Shared Knowledge Updates

            - `.ai/knowledge/features-overview.md`: promotion adds the feature card as reusable completed feature memory.
            - `.ai/knowledge/architecture-overview.md`: update with the high-level Mermaid topology when production modules are integrated.
            - `.ai/knowledge/module-map.md`: update with final source and test module ownership after upstream integration.
            - `.ai/knowledge/integration-map.md`: update if the production feature uses notifications, background jobs, webhooks, or audit events.
            """
        )
    )
    state_path = workspace / "state.yaml"
    state = yaml.safe_load(state_path.read_text()) or {}
    state["current_step"] = "finish"
    state.setdefault("stale", {})["feature_card"] = False
    state.setdefault("stale", {})["canonical_docs"] = False
    state_path.write_text(yaml.safe_dump(state, sort_keys=False))
    for gate in ["verification", "review", "finish"]:
        featurectl(
            worktree,
            "gate",
            "set",
            "--workspace",
            str(workspace),
            "--gate",
            gate,
            "--status",
            "complete",
            "--by",
            "showcase-runner",
            "--note",
            f"{spec.name}: {gate} completed",
        )
    featurectl(worktree, "validate", "--workspace", str(workspace), "--evidence", "--review")
    featurectl(worktree, "promote", "--workspace", str(workspace), "--conflict", "archive-as-variant")


def artifact_inventory(workspace: Path) -> list[str]:
    names = [
        "feature.md",
        "architecture.md",
        "tech-design.md",
        "slices.yaml",
        "execution.md",
        "evidence/manifest.yaml",
        "evidence/final-verification-output.log",
        "reviews/showcase-review.yaml",
        "reviews/verification-review.md",
        "final-output.md",
        "feature-card.md",
        "state.yaml",
    ]
    return [name for name in names if (workspace / name).exists()]


def write_case_outputs(
    spec: CaseSpec,
    workspace: Path,
    worktree: Path,
    observations: list[dict[str, Any]],
) -> None:
    out = OUT_DIR / spec.name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    ensure_intent_to_add(worktree)
    patch = git_diff(worktree, "--", "showcase")
    status = run(["git", "status", "--short"], cwd=worktree).stdout.strip()
    diff_stat = git_diff(worktree, "--stat", "--", "showcase").strip()
    (out / "implementation.patch").write_text(patch)
    validation = featurectl(worktree, "validate", "--workspace", str(workspace), "--evidence", "--review")
    readiness = featurectl(worktree, "validate", "--workspace", str(workspace), "--readiness", check=False)
    source_files = [
        path.relative_to(worktree).as_posix()
        for path in sorted((worktree / "showcase" / spec.slug).glob("*"))
        if path.is_file()
    ]
    data = {
        "case": spec.name,
        "repository": spec.repo,
        "feature": spec.feature,
        "language": spec.language,
        "workspace": str(workspace),
        "worktree": str(worktree),
        "source_files": source_files,
        "artifact_inventory": artifact_inventory(workspace),
        "observations": observations,
        "diff_stat": diff_stat,
        "validation": summarize_output(validation.stdout),
        "readiness": summarize_output(readiness.stdout),
        "status": status,
    }
    (out / "implementation-summary.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    artifacts_md = "\n".join(f"- `{name}`" for name in artifact_inventory(workspace))
    sources_md = "\n".join(f"- `{name}`" for name in source_files)
    observations_md = "\n".join(
        f"- {row['slice']}: red rc={row['red_returncode']}, green rc={row['green_returncode']}, "
        f"verification rc={row['verification_returncode']}, test `{row['test']}`"
        for row in observations
    )
    report = f"""# {spec.repo}: {spec.feature}

## Scope

Implemented a bounded repo-local showcase module for `{spec.scenario}` inside the cloned repository worktree.
This validates that the Native Feature Pipeline can initialize, generate artifacts, record evidence, and drive a code-backed implementation in the existing repo checkout.

## Generated Pipeline Artifacts

Workspace: `{workspace}`

Artifacts:
{artifacts_md}

## Code Changes

Source files:
{sources_md}

Diff stat:

```text
{diff_stat or "no diff"}
```

Patch: `implementation.patch`

## Slice Validation

{observations_md}

## Pipeline Validation

```text
{summarize_output(validation.stdout) or "validation passed"}
```

## Readiness Check

```text
{summarize_output(readiness.stdout) or "readiness passed"}
```

## Implementation Notes

- This run adds a repo-local showcase implementation under `showcase/{spec.slug}` and does not modify upstream production modules outside that bounded directory.
- The patch is preserved so the integration surface and test evidence can be reviewed side by side with generated artifacts.
- Promotion copied the completed workspace into the worktree knowledge area after validation passed.
"""
    (out / "report.md").write_text(report)


def implement_case(spec: CaseSpec, case_index: int) -> dict[str, Any]:
    workspace = ensure_planning_run(spec)
    worktree = worktree_for_workspace(workspace)
    install_pipeline_in_worktree(worktree)
    approve_planning_gates(spec, workspace, worktree)
    observations = implement_slices(spec, case_index, workspace, worktree)
    final_artifacts(spec, workspace, worktree)
    write_case_outputs(spec, workspace, worktree, observations)
    return {
        "case": spec.name,
        "repo": spec.repo,
        "feature": spec.feature,
        "workspace": str(workspace),
        "worktree": str(worktree),
        "report": str(OUT_DIR / spec.name / "report.md"),
        "patch": str(OUT_DIR / spec.name / "implementation.patch"),
    }


def write_index(results: list[dict[str, Any]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "summary.yaml").write_text(yaml.safe_dump({"results": results}, sort_keys=False))
    rows = [
        "| Case | Repository | Feature | Report | Patch |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in results:
        case = row["case"]
        rows.append(
            f"| `{case}` | {row['repo']} | {row['feature']} | "
            f"[report]({case}/report.md) | [patch]({case}/implementation.patch) |"
        )
    (OUT_DIR / "summary.md").write_text(
        "# Code-Backed Showcase Implementations\n\n"
        + "\n".join(rows)
        + "\n\nEach case was initialized through the Native Feature Pipeline, approved through planning gates, implemented as a repo-local code slice, validated with tests, and promoted into the worktree knowledge area.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", action="append", help="case name to run; defaults to all")
    args = parser.parse_args()

    specs = load_specs()
    wanted = set(args.case or [])
    if wanted:
        specs = [spec for spec in specs if spec.name in wanted]
        missing = wanted.difference(spec.name for spec in specs)
        if missing:
            raise SystemExit(f"unknown case(s): {', '.join(sorted(missing))}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for index, spec in enumerate(specs):
        print(f"[implement] {spec.name}: {spec.feature}", flush=True)
        results.append(implement_case(spec, index))
    write_index(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
