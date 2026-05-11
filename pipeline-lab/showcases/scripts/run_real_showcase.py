#!/usr/bin/env python3
"""Run a planning-only Native Feature Pipeline showcase inside a cloned repo."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "pipeline-lab/showcases/real-showcases.yaml"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--report-dir", default="pipeline-lab/showcases/real-runs")
    args = parser.parse_args(argv)
    config = load_config()[args.case]
    repo = ROOT / config["repo_path"]
    report_dir = ROOT / args.report_dir / args.case
    try:
        run_case(args.case, repo, config, report_dir)
    except Exception as exc:
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / "report.md").write_text(f"# Showcase Failure: {args.case}\n\n{exc}\n", encoding="utf-8")
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def run_case(case: str, repo: Path, config: dict[str, Any], report_dir: Path) -> None:
    if not (repo / ".git").exists():
        raise RuntimeError(f"missing cloned repo: {repo}")
    install_pipeline(repo)
    git_config(repo)
    workspace = create_workspace(repo, config)
    install_pipeline_context(worktree_for_workspace(workspace))
    findings = inspect_repo(repo, config)
    write_planning_artifacts(workspace, config, findings)
    set_drafted_gates(workspace)
    validate = run([sys.executable, ".agents/pipeline-core/scripts/featurectl.py", "validate", "--workspace", str(workspace)], repo, check=False)
    readiness = run([sys.executable, ".agents/pipeline-core/scripts/featurectl.py", "validate", "--workspace", str(workspace), "--readiness"], repo, check=False)
    report = render_report(case, repo, workspace, config, findings, validate, readiness)
    (workspace / "repo-report.md").write_text(report, encoding="utf-8")
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "report.md").write_text(report, encoding="utf-8")
    (report_dir / "workspace.txt").write_text(str(workspace) + "\n", encoding="utf-8")
    print(f"case: {case}")
    print(f"workspace: {workspace}")
    print(f"validate_rc: {validate.returncode}")
    print(f"readiness_rc: {readiness.returncode}")


def install_pipeline(repo: Path) -> None:
    shutil.copy2(ROOT / "AGENTS.md", repo / "AGENTS.md")
    for dirname in (".agents", ".ai", "skills"):
        src = ROOT / dirname
        dest = repo / dirname
        if dest.exists():
            shutil.rmtree(dest)
        ignore = shutil.ignore_patterns("feature-workspaces", "features-archive", "logs") if dirname == ".ai" else None
        shutil.copytree(src, dest, ignore=ignore)


def worktree_for_workspace(workspace: Path) -> Path:
    marker = ".ai"
    parts = workspace.parts
    if marker not in parts:
        raise RuntimeError(f"workspace path does not include .ai: {workspace}")
    return Path(*parts[: parts.index(marker)])


def install_pipeline_context(worktree: Path) -> None:
    shutil.copy2(ROOT / "AGENTS.md", worktree / "AGENTS.md")
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


def git_config(repo: Path) -> None:
    run(["git", "config", "user.email", "showcase@example.com"], repo, check=False)
    run(["git", "config", "user.name", "Showcase Runner"], repo, check=False)


def create_workspace(repo: Path, config: dict[str, Any]) -> Path:
    worktree = repo.parent / "worktrees" / f"{config['domain']}-{slugify(config['title'])}-{config['run_id']}"
    branch = f"feature/{config['domain']}-{slugify(config['title'])}-{config['run_id']}"
    if worktree.exists():
        run(["git", "worktree", "remove", "--force", str(worktree)], repo, check=False)
    if worktree.exists():
        shutil.rmtree(worktree)
    run(["git", "worktree", "prune"], repo, check=False)
    run(["git", "branch", "-D", branch], repo, check=False)
    result = run(
        [
            sys.executable,
            ".agents/pipeline-core/scripts/featurectl.py",
            "new",
            "--domain",
            config["domain"],
            "--title",
            config["title"],
            "--run-id",
            config["run_id"],
            "--worktree-root",
            "../worktrees",
        ],
        repo,
    )
    for line in result.stdout.splitlines():
        if line.startswith("workspace: "):
            rel = line.split(": ", 1)[1]
            return worktree / rel
    raise RuntimeError("featurectl new did not print workspace")


def inspect_repo(repo: Path, config: dict[str, Any]) -> dict[str, Any]:
    commit = run(["git", "rev-parse", "--short", "HEAD"], repo).stdout.strip()
    remote = run(["git", "remote", "get-url", "origin"], repo, check=False).stdout.strip() or "local"
    files = sorted(path.relative_to(repo).as_posix() for path in repo.iterdir() if path.name not in {".git", ".agents", ".ai"})
    manifests = [item for item in files if item in {"package.json", "pnpm-workspace.yaml", "go.mod", "pyproject.toml", "Cargo.toml", "Makefile", "README.md"}]
    touchpoints = []
    for rel in config.get("touchpoints", []):
        path = repo / rel
        if path.exists():
            touchpoints.append(rel)
    return {
        "commit": commit,
        "remote": remote,
        "top_level_files": files[:40],
        "manifests": manifests,
        "touchpoints": touchpoints,
    }


def write_planning_artifacts(workspace: Path, config: dict[str, Any], findings: dict[str, Any]) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    feature_key = config["feature_key"]
    title = config["title"]
    modules = findings["touchpoints"] or findings["manifests"] or findings["top_level_files"][:5]
    module_list = "\n".join(f"- `{item}`: candidate touchpoint from repository inspection." for item in modules)
    touchpoint_list = [f"{item}/**" for item in modules[:3]] or ["src/**", "tests/**"]

    (workspace / "feature.md").write_text(f"""# Feature: {title}

## Intent
{config['feature_goal']}

## Motivation
This feature adds controlled behavior for a high-value workflow in `{findings['remote']}` while keeping implementation gated by planning approval.

## Actors
- Product user
- Repository service layer
- Reviewer or administrator

## Problem
Current planning evidence does not show this feature as a complete workflow. Sensitive state changes need explicit rules, traceability, and verification before source implementation.

## Goals
- Define the feature behavior in testable requirements.
- Identify repository modules likely to be touched.
- Preserve implementation boundaries until planning gates are approved.

## Non-Goals
- No source implementation in this planning-only run.
- No production migration execution.

## Related Existing Features
{module_list}

## Functional Requirements
- FR-001: The system supports the requested workflow: {config['feature_goal']}
- FR-002: The system records durable history for state-changing actions.
- FR-003: Authorized users can inspect the result and failure state of the workflow.

## Non-Functional Requirements
- NFR-001: The design must preserve existing authorization and audit boundaries.
- NFR-002: Failures must be observable and recoverable.

## Acceptance Criteria
- AC-001: Given a valid actor, when the workflow is triggered, then the expected state transition is recorded.
- AC-002: Given an unauthorized actor, when the workflow is attempted, then the action is rejected and auditable.
- AC-003: Given a failed downstream operation, when the system retries or rolls back, then duplicate or partial side effects are prevented.

## Product Risks
- Authorization gaps could expose sensitive operations.
- State transitions may conflict with existing workflows.
- Missing audit history would make enterprise usage unsafe.

## Assumptions
- Repository touchpoints inspected: {', '.join(modules) if modules else 'root files only'}.
- This run is planning-only and source edits are intentionally excluded.

## Open Questions
- Which roles should approve or administer this workflow?
- Which existing retention, notification, or audit policies apply?
""", encoding="utf-8")

    (workspace / "architecture.md").write_text(f"""# Architecture: {title}

## Change Delta
New: workflow state handling, history/audit recording, and validation tests for `{feature_key}`.
Modified: candidate touchpoints listed below after source inspection.
Removed: none.
Unchanged: unrelated repository modules and existing public behavior until the feature is gated on.

## System Context
The feature belongs to `{config['domain']}` and is planned against commit `{findings['commit']}`. Candidate repository boundaries are: {', '.join(modules) if modules else 'not yet expanded from sparse checkout'}.

## Component Interactions
- UI/API layer -> domain service: validates actor intent and request shape.
- Domain service -> persistence layer: records state transition and history.
- Domain service -> notification/audit subsystem: emits reviewable events.

## Feature Topology
```mermaid
flowchart LR
  Actor[Product user or administrator] --> Entry[UI/API entrypoint]
  Entry --> Authz[Authorization guard]
  Authz --> Workflow[{config['domain']} workflow service]
  Workflow --> Store[(State and history store)]
  Workflow --> Audit[Audit/event stream]
  Workflow --> Notify[Notification or delivery job]
  Audit --> Knowledge[Shared feature memory]
```

## Diagrams
Sequence diagram recommended during implementation: request, authorization, state transition, audit event, notification, and rollback/failure path.

## Security Model
Authorization must be checked before any state change. Audit events must not be user-editable. Sensitive payloads must be signed, scoped, or redacted when applicable.

## Failure Modes
- Persistence write fails: no partial state transition should be visible.
- Notification or downstream delivery fails: state remains consistent and retry/audit evidence is recorded.
- Conflicting concurrent update occurs: conflict behavior must be deterministic.

## Observability
Record structured audit events, state transition logs, failure reasons, and retry or rollback outcomes.

## Rollback Strategy
Keep implementation behind a feature flag or isolated service path until slices pass. Revert by disabling the workflow and preserving audit records.

## Migration Strategy
Use additive persistence or schema changes only. Deploy read paths before write paths when existing data needs compatibility.

## Architecture Risks
- Cross-module state drift.
- Missing authorization guard.
- Incomplete replay, rollback, or retry semantics.

## Alternatives Considered
- Extend existing generic status fields only; rejected because it hides audit semantics and rollback evidence.
- Implement as a background-only workflow; rejected because user-visible state and review history must remain inspectable.

## Shared Knowledge Impact
- `.ai/knowledge/features-overview.md`: record the completed workflow as reusable feature memory after finish.
- `.ai/knowledge/architecture-overview.md`: summarize the feature topology and affected boundaries for future planning.
- `.ai/knowledge/module-map.md`: note source modules selected for the final implementation.
- `.ai/knowledge/integration-map.md`: record notification, webhook, job, or audit integration paths when used.

## Completeness Correctness Coherence
Completeness: contract, architecture, technical design, slices, readiness gates, and evidence paths cover the requested workflow.
Correctness: state transitions, authorization, audit history, and rollback behavior are tied to acceptance criteria.
Coherence: planned modules, contracts, and slices use the same workflow terms and artifact IDs.

## ADRs
- ADR-001: Use explicit event/history records for workflow state changes.
""", encoding="utf-8")
    (workspace / "adrs").mkdir(exist_ok=True)
    (workspace / "adrs/ADR-001-workflow-history.md").write_text(f"""# ADR-001: Workflow History Records

## Decision
Store explicit history records for `{title}` state changes.

## Context
The feature requires traceability, debugging, and enterprise audit review.

## Consequences
Implementation must define event shape, retention, authorization, and rollback behavior before source changes.
""", encoding="utf-8")

    (workspace / "tech-design.md").write_text(f"""# Technical Design: {title}

## Change Delta
New: domain workflow service, event/history shape, and focused tests for `{feature_key}`.
Modified: repository touchpoints that own the workflow entrypoint, persistence, and inspection UI/API.
Removed: none.
Unchanged: unrelated modules and existing behavior outside the explicit feature path.

## Implementation Summary
Implement the feature through a domain service that validates input, checks authorization, applies state transitions, and writes history events.

## Modules And Responsibilities
{module_list}

## Contracts
- Workflow request: actor, target entity, action, optional comment or metadata.
- Workflow history event: actor, target, previous state, next state, timestamp, reason, correlation ID.

## API/Event/Schema Details
Define request/response or event schema before implementation. Include idempotency or replay protection when external delivery is involved.

## Core Code Sketches
```text
validate actor permission
load target aggregate
compute next state
write state transition and history event atomically
emit notification or delivery job
return inspectable result
```

## Data Model
Add or reuse a history table/collection with actor, timestamp, old value, new value, and rollback hint fields.

## Error Handling
Reject invalid transitions, unauthorized actors, stale versions, duplicate delivery, and downstream failures with explicit error categories.

## Security Considerations
Enforce authorization server-side. Sign or scope external payloads. Avoid leaking sensitive state in notifications or logs.

## Test Strategy
Use unit tests for state transition rules, integration tests for persistence/history, and regression tests for authorization and rollback behavior.

## Migration Plan
Add additive persistence structures only after approval. Backfill is not required for this planning run unless existing records need history.

## Dependency And Ownership Plan
- Owner: feature implementation slice controller.
- Dependencies: existing auth/RBAC, persistence, notification or audit utilities, and test harness.
- File ownership: source and tests under the candidate touchpoints listed in `slices.yaml`; avoid broad refactors outside those paths.
- Conflict risk: medium until exact production modules are chosen; each slice must update downstream ownership notes when new files are touched.

## Decision Traceability
- FR-001 maps to workflow service and transition tests.
- FR-002 maps to history event schema and audit evidence.
- FR-003 maps to inspection API/UI behavior and failure visibility.
- ADR-001 justifies explicit history records rather than inferred logs.

## Rollback Plan
Disable entry points and leave history records intact. Roll back additive schema only after data retention review.

## Integration Notes
Implementation must align with existing manifests and module boundaries: {', '.join(findings['manifests']) if findings['manifests'] else 'no root manifest detected'}.
""", encoding="utf-8")

    slices = []
    for index, title_suffix in enumerate(["Model workflow state and history", "Authorize and execute workflow transition", "Expose inspection and failure handling"], start=1):
        sid = f"S-{index:03d}"
        slices.append({
            "id": sid,
            "title": title_suffix,
            "linked_requirements": ["FR-001", "FR-002"] if index < 3 else ["FR-003"],
            "linked_acceptance_criteria": [f"AC-{index:03d}"],
            "linked_adrs": ["ADR-001"] if index == 1 else [],
            "linked_contracts": ["workflow-history-event"],
            "dependencies": [] if index == 1 else [f"S-{index-1:03d}"],
            "priority": index,
            "complexity": 4 if index == 2 else 2,
            "critical_path": index <= 2,
            "parallelizable": False,
            "expected_touchpoints": touchpoint_list,
            "file_ownership": touchpoint_list,
            "conflict_risk": "medium" if index == 2 else "low",
            "dependency_notes": "Depends on prior workflow model slice." if index > 1 else "No upstream slice dependency.",
            "test_strategy": "Write a focused failing test for the slice, prove the expected red failure, then run the green and independent verification commands.",
            "scope_confidence": "medium",
            "iteration_budget": 3,
            "rollback_point": "feature branch commit before slice implementation",
            "independent_verification": "run targeted unit/integration test command for this repository",
            "failure_triage_notes": "classify failures as implementation_bug, test_bug, design_gap, scope_change, environment_failure, or flaky",
            "tdd": {
                "failing_test_file": f"tests/showcase/{slugify(title)}_{sid.lower()}.test",
                "red_command": "repo-specific test command for the target slice",
                "expected_failure": f"{title_suffix} is not implemented",
                "green_command": "repo-specific test command for the target slice",
            },
            "verification_commands": ["repo-specific full verification command after dependencies are installed"],
            "review_focus": ["authorization", "auditability", "rollback and failure behavior"],
            "evidence_status": "planning-only",
            "status": "pending",
        })
    (workspace / "slices.yaml").write_text(yaml.safe_dump({"artifact_contract_version": "0.1.0", "feature_key": feature_key, "slices": slices}, sort_keys=False), encoding="utf-8")

    with (workspace / "execution.md").open("a", encoding="utf-8") as handle:
        handle.write(f"""

## Docs Consulted: Context

- Repo root at `{findings['remote']}` commit `{findings['commit']}`.
- Top-level files: {', '.join(findings['top_level_files'][:12])}.

## Docs Consulted: Feature Contract

- Feature goal from showcase config: {config['feature_goal']}
- Acceptance criteria and risks were drafted from inspected touchpoints and expected focus areas: {', '.join(config.get('expected_focus', []))}.

## Docs Consulted: Architecture

- Candidate modules: {', '.join(modules) if modules else 'root sparse checkout only'}.

## Docs Consulted: Technical Design

- Manifests/tooling: {', '.join(findings['manifests']) if findings['manifests'] else 'none detected at root'}.

## Docs Consulted: Slicing

- Slices map FR-001 through FR-003 to workflow modeling, transition execution, and inspection/failure handling.

## Planning Evidence

- Repo: `{findings['remote']}`
- Base commit: `{findings['commit']}`
- Workspace: `{workspace}`
- Source edits: none
- Implementation allowed: no
- Basic validation: recorded in repo report
- Readiness validation: expected to block until planning gates are approved or delegated

## Implementation Boundary

Planning stopped before source implementation. No TDD red/green evidence was recorded because source changes were explicitly out of scope.
""")


def set_drafted_gates(workspace: Path) -> None:
    state_path = workspace / "state.yaml"
    state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    state["current_step"] = "readiness"
    state["gates"]["feature_contract"] = "drafted"
    state["gates"]["architecture"] = "drafted"
    state["gates"]["tech_design"] = "drafted"
    state["gates"]["slicing_readiness"] = "drafted"
    state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")


def render_report(case: str, repo: Path, workspace: Path, config: dict[str, Any], findings: dict[str, Any], validate: subprocess.CompletedProcess[str], readiness: subprocess.CompletedProcess[str]) -> str:
    return f"""# Planning Report: {case} / {config['title']}

## Repo Snapshot
- Repo path: `{repo}`
- Remote: `{findings['remote']}`
- Base commit: `{findings['commit']}`
- Pipeline workspace: `{workspace}`
- Feature key: `{config['feature_key']}`
- Run ID: `{config['run_id']}`

## Planning Scope
- Requested feature: {config['feature_goal']}
- Implementation performed: no
- Source changes performed: no
- Stop point: planning package/readiness

## Context Summary
- Primary modules inspected: {', '.join(findings['touchpoints']) if findings['touchpoints'] else 'root sparse checkout only'}
- Existing patterns reused: root manifests and candidate module names
- Test tooling detected: {', '.join(findings['manifests']) if findings['manifests'] else 'not detected from sparse root'}

## Artifact Inventory
- `feature.md`: drafted with FR/NFR/AC IDs
- `architecture.md`: drafted with security, failure, observability, rollback, and ADR reference
- `tech-design.md`: drafted with contracts, data model, tests, migration, and rollback
- `slices.yaml`: drafted with 3 loop-ready TDD slices
- `execution.md`: docs consulted, planning evidence, and implementation boundary

## Gate State
- feature_contract: drafted
- architecture: drafted
- tech_design: drafted
- slicing_readiness: drafted
- implementation: blocked

## Validation
- Basic validation command: `featurectl.py validate --workspace <workspace>`
- Basic validation result: `{validate.returncode}`
- Basic validation output:

```text
{validate.stdout.strip() or validate.stderr.strip()}
```

- Readiness validation command: `featurectl.py validate --workspace <workspace> --readiness`
- Readiness validation result: `{readiness.returncode}` (expected non-zero until gates are approved/delegated)
- Readiness validation output:

```text
{readiness.stdout.strip() or readiness.stderr.strip()}
```

## Risks And Open Questions
- Security: authorization and audit history must be verified.
- Data/model: persistence changes need migration review.
- Compatibility: existing workflows may need transition guards.
- Product ambiguity: final approver/admin roles must be confirmed.
- Operational risk: retry, rollback, and observability must be validated before code.

## Proposed Implementation Handoff
- First slice: `S-001`
- Highest-risk slice: `S-002`
- Required approval/delegation before code: feature contract, architecture, technical design, slicing readiness
"""


def load_config() -> dict[str, dict[str, Any]]:
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    return data["showcases"]


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    return result


def slugify(value: str) -> str:
    import re
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-{2,}", "-", value).strip("-")


if __name__ == "__main__":
    raise SystemExit(main())
