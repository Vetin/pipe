#!/usr/bin/env python3
"""Deterministic helper for the Native Feature Pipeline."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import random
import re
import shutil
import string
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised only on missing deps.
    raise SystemExit("featurectl.py requires PyYAML to read and write pipeline YAML.") from exc


CONTRACT_VERSION = "0.1.0"
VALID_STEPS = {
    "intake",
    "context",
    "feature_contract",
    "architecture",
    "tech_design",
    "slicing",
    "readiness",
    "worktree",
    "tdd_implementation",
    "review",
    "verification",
    "finish",
    "promote",
}
DEFAULT_GATES = {
    "feature_contract": "pending",
    "architecture": "pending",
    "tech_design": "pending",
    "slicing_readiness": "pending",
    "implementation": "blocked",
    "review": "pending",
    "verification": "pending",
    "finish": "pending",
}
DEFAULT_STALE = {
    "feature": False,
    "architecture": False,
    "tech_design": False,
    "slices": False,
    "evidence": False,
    "review": False,
    "feature_card": True,
    "canonical_docs": True,
    "index": False,
}
VALID_GATE_STATES = {
    "pending",
    "drafted",
    "approved",
    "delegated",
    "blocked",
    "reopened",
    "stale",
    "complete",
}
FEATURE_REQUIRED_HEADINGS = (
    "## Intent",
    "## Motivation",
    "## Actors",
    "## Goals",
    "## Non-Goals",
    "## Functional Requirements",
    "## Non-Functional Requirements",
    "## Acceptance Criteria",
    "## Assumptions",
    "## Open Questions",
)
TECH_DESIGN_REQUIRED_HEADINGS = (
    "## Implementation Summary",
    "## Modules And Responsibilities",
    "## Contracts",
    "## API/Event/Schema Details",
    "## Core Code Sketches",
    "## Data Model",
    "## Error Handling",
    "## Security Considerations",
    "## Test Strategy",
    "## Migration Plan",
    "## Rollback Plan",
    "## Integration Notes",
)


class FeatureCtlError(RuntimeError):
    """Raised for expected command failures."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="featurectl.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="initialize pipeline directories")
    init_parser.set_defaults(func=cmd_init)

    new_parser = subparsers.add_parser("new", help="create a feature worktree and workspace")
    new_parser.add_argument("--domain", required=True)
    new_parser.add_argument("--title", required=True)
    new_parser.add_argument("--slug")
    new_parser.add_argument("--run-id")
    new_parser.add_argument("--worktree-root", default="../worktrees")
    new_parser.add_argument("--base-ref", default="HEAD")
    new_parser.add_argument("--stop-point", default="feature_contract")
    new_parser.set_defaults(func=cmd_new)

    status_parser = subparsers.add_parser("status", help="print workspace status")
    status_parser.add_argument("--workspace")
    status_parser.set_defaults(func=cmd_status)

    validate_parser = subparsers.add_parser("validate", help="validate pipeline workspace")
    validate_parser.add_argument("--workspace", required=True)
    validate_parser.add_argument("--readiness", action="store_true")
    validate_parser.add_argument("--implementation", action="store_true")
    validate_parser.add_argument("--evidence", action="store_true")
    validate_parser.add_argument("--review", action="store_true")
    validate_parser.set_defaults(func=cmd_validate)

    load_docset_parser = subparsers.add_parser("load-docset", help="list docs for a pipeline step")
    load_docset_parser.add_argument("--workspace", required=True)
    load_docset_parser.add_argument("--step", required=True)
    load_docset_parser.set_defaults(func=cmd_load_docset)

    gate_parser = subparsers.add_parser("gate", help="manage gate state")
    gate_subparsers = gate_parser.add_subparsers(dest="gate_command", required=True)
    gate_set_parser = gate_subparsers.add_parser("set", help="set a gate status")
    gate_set_parser.add_argument("--workspace", required=True)
    gate_set_parser.add_argument("--gate", required=True)
    gate_set_parser.add_argument("--status", required=True)
    gate_set_parser.add_argument("--by", dest="actor", required=True)
    gate_set_parser.add_argument("--note", default="")
    gate_set_parser.set_defaults(func=cmd_gate_set)

    mark_stale_parser = subparsers.add_parser("mark-stale", help="mark downstream artifacts stale")
    mark_stale_parser.add_argument("--workspace", required=True)
    mark_stale_parser.add_argument("--artifact", required=True)
    mark_stale_parser.add_argument("--reason", default="")
    mark_stale_parser.set_defaults(func=cmd_mark_stale)

    record_evidence_parser = subparsers.add_parser("record-evidence", help="record raw slice evidence")
    record_evidence_parser.add_argument("--workspace", required=True)
    record_evidence_parser.add_argument("--slice", dest="slice_id", required=True)
    record_evidence_parser.add_argument("--phase", required=True, choices=["red", "green", "verification", "review"])
    record_evidence_parser.add_argument("--command", default="")
    record_evidence_parser.add_argument("--output", required=True)
    record_evidence_parser.add_argument("--git-state")
    record_evidence_parser.add_argument("--timestamp")
    record_evidence_parser.set_defaults(func=cmd_record_evidence)

    complete_slice_parser = subparsers.add_parser("complete-slice", help="mark a slice complete after evidence validation")
    complete_slice_parser.add_argument("--workspace", required=True)
    complete_slice_parser.add_argument("--slice", dest="slice_id", required=True)
    complete_slice_parser.add_argument("--commit")
    complete_slice_parser.add_argument("--diff-hash")
    complete_slice_parser.set_defaults(func=cmd_complete_slice)

    try:
        args = parser.parse_args(argv)
        args.func(args)
    except FeatureCtlError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_init(_args: argparse.Namespace) -> None:
    root = repo_root()
    ensure_init_tree(root)
    print("initialized Native Feature Pipeline directories")


def cmd_new(args: argparse.Namespace) -> None:
    root = repo_root()
    ensure_init_tree(root)

    domain = normalize_domain(args.domain)
    slug = slugify(args.slug or args.title)
    run_id = args.run_id or generate_run_id()
    feature_key = f"{domain}/{slug}"
    branch = f"feature/{domain}-{slug}-{run_id}"
    worktree_root = (root / args.worktree_root).resolve()
    worktree_path = worktree_root / f"{domain}-{slug}-{run_id}"
    workspace_rel = Path(".ai") / "feature-workspaces" / domain / f"{slug}--{run_id}"
    workspace_path = worktree_path / workspace_rel

    if worktree_path.exists():
        raise FeatureCtlError(f"worktree path already exists: {worktree_path}")
    if git_branch_exists(root, branch):
        raise FeatureCtlError(f"branch already exists: {branch}")

    worktree_root.mkdir(parents=True, exist_ok=True)
    run_git(root, "worktree", "add", "-b", branch, str(worktree_path), args.base_ref)

    workspace_path.mkdir(parents=True, exist_ok=False)
    for subdir in ("adrs", "diagrams", "contracts", "reviews", "evidence"):
        (workspace_path / subdir).mkdir(parents=True, exist_ok=True)

    created_at = utc_now()
    worktree_value = os.path.relpath(worktree_path, root)
    workspace_value = workspace_rel.as_posix()
    canonical_path = f".ai/features/{domain}/{slug}"

    write_yaml(
        workspace_path / "feature.yaml",
        {
            "artifact_contract_version": CONTRACT_VERSION,
            "feature_key": feature_key,
            "domain": domain,
            "slug": slug,
            "title": args.title,
            "status": "draft",
            "run_id": run_id,
            "branch": branch,
            "worktree": worktree_value,
            "canonical_path": canonical_path,
            "workspace_path": workspace_value,
            "aliases": [],
            "keywords": [domain, slug],
            "created_at": created_at,
            "updated_at": created_at,
        },
    )
    write_yaml(
        workspace_path / "state.yaml",
        {
            "artifact_contract_version": CONTRACT_VERSION,
            "feature_key": feature_key,
            "run_id": run_id,
            "current_step": "context",
            "worktree": {
                "branch": branch,
                "path": worktree_value,
            },
            "gates": dict(DEFAULT_GATES),
            "stale": dict(DEFAULT_STALE),
            "active_slice": None,
            "locks": {
                "owner": None,
                "acquired_at": None,
            },
        },
    )
    write_text(workspace_path / "apex.md", render_apex(feature_key))
    write_text(workspace_path / "execution.md", render_execution(args.title, feature_key, args.stop_point))

    print(f"feature_key: {feature_key}")
    print(f"branch: {branch}")
    print(f"worktree: {worktree_value}")
    print(f"workspace: {workspace_value}")
    print("next_step: nfp-01-context")


def cmd_status(args: argparse.Namespace) -> None:
    root = repo_root()
    workspace = resolve_workspace(root, args.workspace)
    feature = read_yaml(workspace / "feature.yaml")
    state = read_yaml(workspace / "state.yaml")
    blockers = status_blockers(root, workspace, feature, state)

    print(f"feature_key: {feature.get('feature_key')}")
    print(f"worktree: {state.get('worktree', {}).get('path')}")
    print(f"current_step: {state.get('current_step')}")
    print("gates:")
    for gate, status in state.get("gates", {}).items():
        print(f"  {gate}: {status}")
    print("stale:")
    for artifact, stale in state.get("stale", {}).items():
        print(f"  {artifact}: {str(stale).lower()}")
    print("blocking_issues:")
    if blockers:
        for blocker in blockers:
            print(f"  - {blocker}")
    else:
        print("  none")
    print(f"next_step: {next_skill_for_step(state.get('current_step'))}")


def cmd_validate(args: argparse.Namespace) -> None:
    root = repo_root()
    workspace = resolve_workspace(root, args.workspace)
    blockers = validate_workspace(
        root,
        workspace,
        readiness=args.readiness,
        implementation=args.implementation,
        evidence=args.evidence,
        review=args.review,
    )
    if blockers:
        print("validation: fail")
        for blocker in blockers:
            print(f"- {blocker}")
        raise FeatureCtlError("workspace validation failed")
    print("validation: pass")


def cmd_load_docset(args: argparse.Namespace) -> None:
    root = repo_root()
    workspace = resolve_workspace(root, args.workspace)
    if not workspace.exists():
        raise FeatureCtlError(f"workspace does not exist: {workspace}")
    step = normalize_step_name(args.step)
    docset = load_docset(root, step)
    print(f"step: {step}")
    print_docs("required_docs", root, docset.get("required_docs", []))
    print_docs("optional_docs", root, docset.get("optional_docs", []))
    print_docs("missing_docs", root, missing_docs(root, docset))
    print("selected_alternatives:")
    alternatives = docset.get("selected_alternatives") or []
    if alternatives:
        for item in alternatives:
            print(f"  - {item}")
    else:
        print("  none")
    print_docs("suggested_related_files", root, docset.get("suggested_related_files", []), check_exists=False)


def cmd_gate_set(args: argparse.Namespace) -> None:
    root = repo_root()
    workspace = resolve_workspace(root, args.workspace)
    if args.gate not in DEFAULT_GATES:
        raise FeatureCtlError(f"unknown gate: {args.gate}")
    if args.status not in VALID_GATE_STATES:
        raise FeatureCtlError(f"invalid gate status: {args.status}")
    state_path = workspace / "state.yaml"
    state = read_yaml(state_path)
    old_status = state.setdefault("gates", {}).get(args.gate)
    state["gates"][args.gate] = args.status
    write_yaml(state_path, state)
    append_execution_event(
        workspace,
        "Gate Events",
        f"- {utc_now()} gate={args.gate} old_status={old_status} new_status={args.status} by={args.actor} note={args.note or 'none'}",
    )
    print(f"gate: {args.gate}")
    print(f"status: {args.status}")


def cmd_mark_stale(args: argparse.Namespace) -> None:
    root = repo_root()
    workspace = resolve_workspace(root, args.workspace)
    state_path = workspace / "state.yaml"
    state = read_yaml(state_path)
    stale = state.setdefault("stale", {})
    affected = staleness_targets(args.artifact)
    if not affected:
        raise FeatureCtlError(f"unknown artifact for staleness: {args.artifact}")
    for artifact in affected:
        stale[artifact] = True
    write_yaml(state_path, state)
    append_execution_event(
        workspace,
        "Scope Changes",
        f"- {utc_now()} artifact={args.artifact} marked_stale={', '.join(affected)} reason={args.reason or 'none'}",
    )
    print("marked_stale:")
    for artifact in affected:
        print(f"  - {artifact}")


def cmd_record_evidence(args: argparse.Namespace) -> None:
    root = repo_root()
    workspace = resolve_workspace(root, args.workspace)
    feature = read_yaml(workspace / "feature.yaml")
    state = read_yaml(workspace / "state.yaml")
    ensure_known_slice(workspace, args.slice_id)
    timestamp = args.timestamp or utc_now()
    validate_timestamp(timestamp)
    manifest_path = workspace / "evidence/manifest.yaml"
    manifest = read_manifest_or_default(manifest_path, feature.get("feature_key"))
    slice_dir = workspace / "evidence" / args.slice_id
    slice_dir.mkdir(parents=True, exist_ok=True)
    rels = evidence_phase_files(args.slice_id, args.phase)

    entry: dict[str, Any] = {"timestamp": timestamp}
    if args.phase in {"red", "green", "verification"}:
        if not args.command:
            raise FeatureCtlError(f"{args.phase} evidence requires --command")
        write_text(workspace / "evidence" / rels["command_file"], args.command + "\n")
        write_text(workspace / "evidence" / rels["output_file"], args.output)
        entry["command_file"] = rels["command_file"]
        entry["output_file"] = rels["output_file"]
    if args.phase in {"red", "green"}:
        git_state = args.git_state if args.git_state is not None else current_git_state(root, state)
        write_text(workspace / "evidence" / rels["git_state_file"], git_state)
        entry["git_state_file"] = rels["git_state_file"]
    if args.phase == "review":
        write_text(workspace / "evidence" / rels["summary_file"], args.output)
        entry["summary_file"] = rels["summary_file"]

    manifest.setdefault("slices", {}).setdefault(args.slice_id, {})[args.phase] = entry
    write_yaml(manifest_path, manifest)
    print(f"recorded: {args.slice_id} {args.phase}")


def cmd_complete_slice(args: argparse.Namespace) -> None:
    root = repo_root()
    workspace = resolve_workspace(root, args.workspace)
    ensure_known_slice(workspace, args.slice_id)
    if not args.commit and not args.diff_hash:
        raise FeatureCtlError("complete-slice requires --commit or --diff-hash")
    add_slice_commit_metadata(workspace, args.slice_id, commit=args.commit, diff_hash=args.diff_hash)
    blockers = validate_slice_evidence(workspace, args.slice_id)
    if blockers:
        print("slice_evidence: fail")
        for blocker in blockers:
            print(f"- {blocker}")
        raise FeatureCtlError("slice evidence validation failed")

    manifest_path = workspace / "evidence/manifest.yaml"
    manifest = read_yaml(manifest_path)
    write_yaml(manifest_path, manifest)
    mark_slice_complete(workspace / "slices.yaml", args.slice_id)
    append_execution_event(
        workspace,
        "Summary",
        f"- {utc_now()} completed slice {args.slice_id} with evidence",
    )
    print(f"slice_complete: {args.slice_id}")


def ensure_init_tree(root: Path) -> None:
    dirs = [
        ".ai/feature-workspaces",
        ".ai/features",
        ".ai/features-archive",
        ".ai/knowledge",
        ".ai/pipeline-docs/global",
        ".agents/pipeline-core/references",
        ".agents/pipeline-core/scripts/schemas",
        ".agents/skills",
        ".agents/skill-lab/quarantine",
        ".agents/skill-lab/accepted",
        ".agents/skill-lab/rejected",
        "pipeline-lab/benchmarks/scenarios",
        "pipeline-lab/benchmarks/suites",
        "pipeline-lab/envs/toy-monolith",
        "pipeline-lab/envs/modular-api",
        "pipeline-lab/scorecards",
        "tests/feature_pipeline",
    ]
    for dirname in dirs:
        (root / dirname).mkdir(parents=True, exist_ok=True)

    write_if_missing(
        root / ".ai/features/index.yaml",
        "artifact_contract_version: '0.1.0'\nfeatures: []\n",
    )
    write_if_missing(root / ".ai/features/overview.md", "# Feature Overview\n\nNo canonical features have been promoted yet.\n")
    write_if_missing(
        root / ".gitignore",
        "pipeline-lab/runs/\n.ai/logs/\n*.tmp\n__pycache__/\n.pytest_cache/\n",
    )


def render_apex(feature_key: str) -> str:
    return f"""# Apex: {feature_key}

## Read Order

1. `feature.yaml` - identity and paths
2. `state.yaml` - machine state
3. `execution.md` - run plan, approvals, docs consulted, next step
4. `feature.md` - product contract
5. `architecture.md` - system design
6. `tech-design.md` - implementation design
7. `slices.yaml` - TDD execution plan
8. `evidence/manifest.yaml` - evidence index
9. `reviews/` - review results

## Main Artifacts

- Feature contract: `feature.md`
- Architecture: `architecture.md`
- Technical design: `tech-design.md`
- Implementation plan: `slices.yaml`
- ADRs: `adrs/`
- Contracts: `contracts/`
- Evidence: `evidence/`
- Reviews: `reviews/`
- Execution log: `execution.md`

## Current Status

See `state.yaml`.

## Next Action

See `execution.md`.
"""


def render_execution(title: str, feature_key: str, stop_point: str) -> str:
    now = utc_now()
    return f"""# Execution Log: {feature_key}

## User Request

{title}

## Run Plan

Mode: planning autorun
Stop point: {stop_point}
Implementation allowed: no

Planned steps:

1. Context discovery
2. Feature contract
3. Architecture
4. Technical design
5. Slicing
6. Readiness summary

## Non-Delegable Checkpoints

Stop and ask user before:

- destructive command
- production data migration
- new production dependency
- public API breaking change
- security model change
- credential/secret handling
- paid external service
- license-impacting dependency

## Clarifying Questions

None currently recorded.

## Assumptions

None currently recorded.

## Docs Consulted

None yet.

## Gate Events

None yet.

## Scope Changes

None.

## Current Step

context

## Next Step

nfp-01-context

## Summary

Feature run initialized at {now}. The next step is context discovery.
"""


def repo_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        raise FeatureCtlError("must be run inside a git repository") from exc
    return Path(result.stdout.strip()).resolve()


def resolve_workspace(root: Path, workspace: str | None) -> Path:
    if workspace:
        path = Path(workspace)
        if not path.is_absolute():
            path = root / path
        return path.resolve()

    cwd = Path.cwd().resolve()
    for candidate in [cwd, *cwd.parents]:
        if (candidate / "feature.yaml").exists() and (candidate / "state.yaml").exists():
            return candidate

    workspaces = sorted((root / ".ai/feature-workspaces").glob("*/*--run-*"))
    if len(workspaces) == 1:
        return workspaces[0].resolve()
    raise FeatureCtlError("workspace is required when it cannot be inferred")


def status_blockers(root: Path, workspace: Path, feature: dict[str, Any], state: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    for name in ("apex.md", "feature.yaml", "state.yaml", "execution.md"):
        if not (workspace / name).exists():
            blockers.append(f"missing {name}")
    if feature.get("feature_key") != state.get("feature_key"):
        blockers.append("feature.yaml and state.yaml feature_key mismatch")
    if feature.get("run_id") != state.get("run_id"):
        blockers.append("feature.yaml and state.yaml run_id mismatch")
    current_step = state.get("current_step")
    if current_step not in VALID_STEPS:
        blockers.append(f"invalid current_step: {current_step}")
    worktree_info = state.get("worktree") or {}
    worktree_value = worktree_info.get("path")
    branch_value = worktree_info.get("branch")
    if worktree_value:
        worktree_path = (root / worktree_value).resolve()
        if not worktree_path.exists():
            blockers.append(f"worktree path does not exist: {worktree_value}")
        else:
            try:
                workspace.relative_to(worktree_path)
            except ValueError:
                blockers.append("workspace is not inside configured worktree")
            try:
                actual_branch = run_git(worktree_path, "rev-parse", "--abbrev-ref", "HEAD").strip()
            except FeatureCtlError as exc:
                blockers.append(str(exc))
            else:
                if branch_value and actual_branch != branch_value:
                    blockers.append(f"worktree branch mismatch: expected {branch_value}, got {actual_branch}")
    else:
        blockers.append("state.yaml missing worktree.path")
    return blockers


def validate_workspace(
    root: Path,
    workspace: Path,
    *,
    readiness: bool = False,
    implementation: bool = False,
    evidence: bool = False,
    review: bool = False,
) -> list[str]:
    blockers: list[str] = []
    try:
        feature = read_yaml(workspace / "feature.yaml")
        state = read_yaml(workspace / "state.yaml")
    except FeatureCtlError as exc:
        return [str(exc)]

    blockers.extend(status_blockers(root, workspace, feature, state))
    blockers.extend(forbidden_file_blockers(workspace))
    blockers.extend(validate_state_shape(state))
    blockers.extend(validate_feature_contract_if_started(workspace, state))
    blockers.extend(validate_architecture_if_started(workspace, state))
    blockers.extend(validate_tech_design_if_started(workspace, state))
    blockers.extend(validate_slices_if_started(workspace, state))

    if readiness:
        blockers.extend(validate_readiness_minimum(workspace, state))
    if implementation:
        blockers.extend(validate_implementation_minimum(state))
    if evidence:
        blockers.extend(validate_evidence_minimum(workspace))
    if review:
        blockers.extend(validate_review_minimum(workspace))
    return blockers


def forbidden_file_blockers(workspace: Path) -> list[str]:
    blockers = []
    for forbidden in ("approvals.yaml", "handoff.md"):
        matches = [path for path in workspace.rglob(forbidden) if path.is_file()]
        for match in matches:
            blockers.append(f"forbidden file exists: {match.relative_to(workspace)}")
    return blockers


def validate_state_shape(state: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if state.get("artifact_contract_version") != CONTRACT_VERSION:
        blockers.append("state.yaml artifact_contract_version mismatch")
    if "next_skill" in state:
        blockers.append("state.yaml must not contain next_skill")
    gates = state.get("gates")
    if not isinstance(gates, dict):
        blockers.append("state.yaml gates must be a mapping")
    else:
        for gate in DEFAULT_GATES:
            if gate not in gates:
                blockers.append(f"state.yaml missing gate: {gate}")
            elif gates[gate] not in VALID_GATE_STATES:
                blockers.append(f"invalid gate status for {gate}: {gates[gate]}")
    stale = state.get("stale")
    if not isinstance(stale, dict):
        blockers.append("state.yaml stale must be a mapping")
    return blockers


def validate_feature_contract_if_started(workspace: Path, state: dict[str, Any]) -> list[str]:
    gate = (state.get("gates") or {}).get("feature_contract")
    if gate not in {"drafted", "approved", "delegated", "complete"}:
        return []
    feature_path = workspace / "feature.md"
    if not feature_path.exists():
        return ["feature_contract gate requires feature.md"]
    content = feature_path.read_text(encoding="utf-8")
    blockers = [f"feature.md missing heading: {heading}" for heading in FEATURE_REQUIRED_HEADINGS if heading not in content]
    if "FR-" not in content:
        blockers.append("feature.md must include functional requirement IDs")
    if "AC-" not in content:
        blockers.append("feature.md must include acceptance criteria IDs")
    return blockers


def validate_architecture_if_started(workspace: Path, state: dict[str, Any]) -> list[str]:
    gate = (state.get("gates") or {}).get("architecture")
    if gate not in {"drafted", "approved", "delegated", "complete"}:
        return []
    architecture_path = workspace / "architecture.md"
    if not architecture_path.exists():
        return ["architecture gate requires architecture.md"]
    content = architecture_path.read_text(encoding="utf-8")
    required_headings = (
        "## System Context",
        "## Component Interactions",
        "## Security Model",
        "## Failure Modes",
        "## Observability",
        "## Rollback Strategy",
        "## Architecture Risks",
        "## ADRs",
    )
    blockers = [f"architecture.md missing heading: {heading}" for heading in required_headings if heading not in content]
    execution = (workspace / "execution.md").read_text(encoding="utf-8") if (workspace / "execution.md").exists() else ""
    if "Docs Consulted: Architecture" not in execution:
        blockers.append("execution.md missing Docs Consulted: Architecture")
    return blockers


def validate_tech_design_if_started(workspace: Path, state: dict[str, Any]) -> list[str]:
    gate = (state.get("gates") or {}).get("tech_design")
    if gate not in {"drafted", "approved", "delegated", "complete"}:
        return []
    tech_design_path = workspace / "tech-design.md"
    if not tech_design_path.exists():
        return ["tech_design gate requires tech-design.md"]
    content = tech_design_path.read_text(encoding="utf-8")
    blockers = [f"tech-design.md missing heading: {heading}" for heading in TECH_DESIGN_REQUIRED_HEADINGS if heading not in content]
    execution = (workspace / "execution.md").read_text(encoding="utf-8") if (workspace / "execution.md").exists() else ""
    if "Docs Consulted: Technical Design" not in execution:
        blockers.append("execution.md missing Docs Consulted: Technical Design")
    return blockers


def validate_slices_if_started(workspace: Path, state: dict[str, Any]) -> list[str]:
    gate = (state.get("gates") or {}).get("slicing_readiness")
    if gate not in {"drafted", "approved", "delegated", "complete"}:
        return []
    slices_path = workspace / "slices.yaml"
    if not slices_path.exists():
        return ["slicing_readiness gate requires slices.yaml"]
    return validate_slices_file(slices_path, workspace=workspace)


def validate_slices_file(path: Path, workspace: Path | None = None) -> list[str]:
    blockers: list[str] = []
    try:
        data = read_yaml(path)
    except FeatureCtlError as exc:
        return [str(exc)]
    if data.get("artifact_contract_version") != CONTRACT_VERSION:
        blockers.append("slices.yaml artifact_contract_version mismatch")
    slices = data.get("slices")
    if isinstance(slices, dict):
        slice_items = list(slices.values())
    elif isinstance(slices, list):
        slice_items = slices
    else:
        return blockers + ["slices.yaml slices must be a list or mapping"]
    if not slice_items:
        blockers.append("slices.yaml must include at least one slice")
    feature_ids = extract_feature_ids(workspace / "feature.md") if workspace else {"FR": set(), "AC": set()}
    seen_ids: set[str] = set()
    all_ids = {item.get("id") for item in slice_items if isinstance(item, dict)}
    for index, item in enumerate(slice_items, start=1):
        prefix = f"slice {item.get('id', index) if isinstance(item, dict) else index}"
        if not isinstance(item, dict):
            blockers.append(f"{prefix} must be a mapping")
            continue
        slice_id = item.get("id")
        if not isinstance(slice_id, str) or not re.match(r"^S-[0-9]{3}$", slice_id):
            blockers.append(f"{prefix} id must match S-###")
        elif slice_id in seen_ids:
            blockers.append(f"{prefix} id is duplicated")
        else:
            seen_ids.add(slice_id)
        for forbidden in ("allowed_files", "forbidden_files"):
            if forbidden in item:
                blockers.append(f"{prefix} must not use {forbidden} in v1")
        for field in (
            "id",
            "title",
            "linked_requirements",
            "linked_acceptance_criteria",
            "linked_adrs",
            "linked_contracts",
            "dependencies",
            "priority",
            "expected_touchpoints",
            "scope_confidence",
            "verification_commands",
            "review_focus",
            "evidence_status",
            "status",
        ):
            if field not in item:
                blockers.append(f"{prefix} missing {field}")
        if not item.get("linked_requirements"):
            blockers.append(f"{prefix} must link requirements")
        else:
            for requirement in item.get("linked_requirements") or []:
                if feature_ids["FR"] and requirement not in feature_ids["FR"]:
                    blockers.append(f"{prefix} links unknown requirement {requirement}")
        if not item.get("linked_acceptance_criteria"):
            blockers.append(f"{prefix} must link acceptance criteria")
        else:
            for criterion in item.get("linked_acceptance_criteria") or []:
                if feature_ids["AC"] and criterion not in feature_ids["AC"]:
                    blockers.append(f"{prefix} links unknown acceptance criterion {criterion}")
        if item.get("scope_confidence") not in {"low", "medium", "high"}:
            blockers.append(f"{prefix} scope_confidence must be low, medium, or high")
        for dependency in item.get("dependencies") or []:
            if dependency not in all_ids:
                blockers.append(f"{prefix} depends on unknown slice {dependency}")
        tdd = item.get("tdd")
        if not isinstance(tdd, dict):
            blockers.append(f"{prefix} missing tdd mapping")
        else:
            for field in ("failing_test_file", "red_command", "expected_failure", "green_command"):
                if not tdd.get(field):
                    blockers.append(f"{prefix} tdd missing {field}")
        if not item.get("verification_commands"):
            blockers.append(f"{prefix} must include verification_commands")
    return blockers


def extract_feature_ids(feature_path: Path) -> dict[str, set[str]]:
    if not feature_path.exists():
        return {"FR": set(), "AC": set()}
    content = feature_path.read_text(encoding="utf-8")
    return {
        "FR": set(re.findall(r"\bFR-[0-9]{3}\b", content)),
        "AC": set(re.findall(r"\bAC-[0-9]{3}\b", content)),
    }


def validate_readiness_minimum(workspace: Path, state: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    for artifact in ("feature.md", "architecture.md", "tech-design.md", "slices.yaml"):
        if not (workspace / artifact).exists():
            blockers.append(f"readiness requires {artifact}")
    blockers.extend(validate_slices_file(workspace / "slices.yaml", workspace=workspace) if (workspace / "slices.yaml").exists() else [])
    gates = state.get("gates") or {}
    for gate in ("feature_contract", "architecture", "tech_design", "slicing_readiness"):
        if gates.get(gate) not in {"approved", "delegated"}:
            blockers.append(f"readiness requires {gate} gate approved or delegated")
    for artifact in ("feature", "architecture", "tech_design", "slices"):
        if (state.get("stale") or {}).get(artifact):
            blockers.append(f"readiness blocked by stale {artifact}")
    return blockers


def validate_implementation_minimum(state: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    gates = state.get("gates") or {}
    for gate in ("feature_contract", "architecture", "tech_design", "slicing_readiness"):
        if gates.get(gate) not in {"approved", "delegated"}:
            blockers.append(f"implementation requires {gate} gate approved or delegated")
    return blockers


def validate_evidence_minimum(workspace: Path) -> list[str]:
    manifest = workspace / "evidence/manifest.yaml"
    if not manifest.exists():
        return ["evidence validation requires evidence/manifest.yaml"]
    return validate_evidence_manifest(workspace)


def validate_review_minimum(workspace: Path) -> list[str]:
    blockers: list[str] = []
    for review_file in workspace.glob("reviews/*.yaml"):
        review = read_yaml(review_file)
        if review.get("blocking") is True and review.get("severity") == "critical":
            blockers.append(f"critical review finding blocks verification: {review_file.relative_to(workspace)}")
    return blockers


def next_skill_for_step(step: str | None) -> str:
    mapping = {
        "context": "nfp-01-context",
        "feature_contract": "nfp-02-feature-contract",
        "architecture": "nfp-03-architecture",
        "tech_design": "nfp-04-tech-design",
        "slicing": "nfp-05-slicing",
        "readiness": "nfp-06-readiness",
        "worktree": "nfp-07-worktree",
        "tdd_implementation": "nfp-08-tdd-implementation",
        "review": "nfp-09-review",
        "verification": "nfp-10-verification",
        "finish": "nfp-11-finish",
        "promote": "nfp-12-promote",
    }
    return mapping.get(step or "", "unknown")


def normalize_step_name(step: str) -> str:
    normalized = step.strip().lower().replace("_", "-")
    valid_steps = {
        "intake",
        "context",
        "feature-contract",
        "architecture",
        "tech-design",
        "slicing",
        "readiness",
        "worktree",
        "tdd-implementation",
        "review",
        "verification",
        "finish",
        "promote",
    }
    if normalized not in valid_steps:
        raise FeatureCtlError(f"unknown docset step: {step}")
    return normalized


def load_docset(root: Path, step: str) -> dict[str, Any]:
    index_path = root / ".ai/pipeline-docs/docset-index.yaml"
    if not index_path.exists():
        raise FeatureCtlError("missing .ai/pipeline-docs/docset-index.yaml")
    index = read_yaml(index_path)
    rel = (index.get("steps") or {}).get(step)
    if not rel:
        raise FeatureCtlError(f"docset index has no entry for step: {step}")
    docset_path = root / ".ai/pipeline-docs" / rel
    docset = read_yaml(docset_path)
    if docset.get("artifact_contract_version") != CONTRACT_VERSION:
        raise FeatureCtlError(f"docset artifact_contract_version mismatch in {docset_path}")
    if docset.get("step") != step:
        raise FeatureCtlError(f"docset step mismatch in {docset_path}")
    return docset


def missing_docs(root: Path, docset: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for key in ("required_docs", "optional_docs"):
        for rel in docset.get(key, []) or []:
            if not (root / rel).exists():
                missing.append(rel)
    return missing


def print_docs(label: str, root: Path, docs: list[str], *, check_exists: bool = True) -> None:
    print(f"{label}:")
    if not docs:
        print("  none")
        return
    for rel in docs:
        suffix = ""
        if check_exists and not (root / rel).exists():
            suffix = " (missing)"
        print(f"  - {rel}{suffix}")


def normalize_domain(domain: str) -> str:
    normalized = slugify(domain)
    if not normalized:
        raise FeatureCtlError("domain cannot be empty")
    return normalized


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    if not value:
        raise FeatureCtlError("slug cannot be empty")
    return value


def generate_run_id() -> str:
    date = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    suffix = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(4))
    return f"run-{date}-{suffix}"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_branch_exists(root: Path, branch: str) -> bool:
    result = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
        cwd=root,
    )
    return result.returncode == 0


def run_git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() or exc.stdout.strip()
        raise FeatureCtlError(f"git {' '.join(args)} failed: {stderr}") from exc
    return result.stdout


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FeatureCtlError(f"missing YAML file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise FeatureCtlError(f"YAML file must contain a mapping: {path}")
    return loaded


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=False)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        write_text(path, content)


def append_execution_event(workspace: Path, section: str, line: str) -> None:
    path = workspace / "execution.md"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    heading = f"## {section}"
    if heading not in existing:
        existing = existing.rstrip() + f"\n\n{heading}\n\n"
    existing = existing.rstrip() + "\n" + line + "\n"
    path.write_text(existing, encoding="utf-8")


def staleness_targets(artifact: str) -> list[str]:
    rules = {
        "feature": ["architecture", "tech_design", "slices", "evidence", "feature_card", "canonical_docs"],
        "feature.md": ["architecture", "tech_design", "slices", "evidence", "feature_card", "canonical_docs"],
        "architecture": ["tech_design", "slices", "evidence", "feature_card", "canonical_docs"],
        "architecture.md": ["tech_design", "slices", "evidence", "feature_card", "canonical_docs"],
        "adrs": ["tech_design", "slices", "evidence", "feature_card", "canonical_docs"],
        "diagrams": ["tech_design", "slices", "evidence", "feature_card", "canonical_docs"],
        "tech_design": ["slices", "evidence", "feature_card", "canonical_docs"],
        "tech-design.md": ["slices", "evidence", "feature_card", "canonical_docs"],
        "contracts": ["slices", "evidence", "feature_card", "canonical_docs"],
        "slices": ["evidence", "review", "feature_card", "canonical_docs"],
        "slices.yaml": ["evidence", "review", "feature_card", "canonical_docs"],
        "feature_yaml": ["index"],
        "feature.yaml": ["index"],
    }
    return rules.get(artifact, [])


def read_manifest_or_default(path: Path, feature_key: str | None) -> dict[str, Any]:
    if path.exists():
        manifest = read_yaml(path)
    else:
        manifest = {
            "artifact_contract_version": CONTRACT_VERSION,
            "feature_key": feature_key,
            "slices": {},
        }
    manifest.setdefault("artifact_contract_version", CONTRACT_VERSION)
    manifest.setdefault("feature_key", feature_key)
    manifest.setdefault("slices", {})
    return manifest


def evidence_phase_files(slice_id: str, phase: str) -> dict[str, str]:
    base = f"{slice_id}/"
    mapping = {
        "red": {
            "git_state_file": base + "00-pre-red-git-state.txt",
            "command_file": base + "01-red-command.txt",
            "output_file": base + "01-red-output.log",
        },
        "green": {
            "git_state_file": base + "02-pre-green-git-state.txt",
            "command_file": base + "03-green-command.txt",
            "output_file": base + "03-green-output.log",
        },
        "verification": {
            "command_file": base + "04-verification-command.txt",
            "output_file": base + "04-verification-output.log",
        },
        "review": {
            "summary_file": base + "05-review-summary.md",
        },
    }
    return mapping[phase]


def current_git_state(root: Path, state: dict[str, Any]) -> str:
    worktree_value = (state.get("worktree") or {}).get("path")
    if not worktree_value:
        return "git state unavailable: state.yaml missing worktree.path\n"
    worktree_path = (root / worktree_value).resolve()
    try:
        return run_git(worktree_path, "status", "--short", "--branch")
    except FeatureCtlError as exc:
        return f"git state unavailable: {exc}\n"


def validate_timestamp(value: str) -> None:
    parse_timestamp(value)


def parse_timestamp(value: str) -> dt.datetime:
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FeatureCtlError(f"invalid timestamp: {value}") from exc


def validate_evidence_manifest(workspace: Path) -> list[str]:
    blockers: list[str] = []
    manifest_path = workspace / "evidence/manifest.yaml"
    try:
        manifest = read_yaml(manifest_path)
    except FeatureCtlError as exc:
        return [str(exc)]
    if manifest.get("artifact_contract_version") != CONTRACT_VERSION:
        blockers.append("evidence manifest artifact_contract_version mismatch")
    feature = read_yaml(workspace / "feature.yaml") if (workspace / "feature.yaml").exists() else {}
    if feature.get("feature_key") and manifest.get("feature_key") != feature.get("feature_key"):
        blockers.append("evidence manifest feature_key mismatch")
    slices = manifest.get("slices")
    if not isinstance(slices, dict):
        return blockers + ["evidence manifest slices must be a mapping"]
    known_slices = known_slice_ids(workspace)
    for slice_id in slices:
        if known_slices and slice_id not in known_slices:
            blockers.append(f"evidence manifest references unknown slice: {slice_id}")
        blockers.extend(validate_slice_evidence(workspace, slice_id))
    blockers.extend(validate_completed_slices_have_manifest(workspace, slices))
    return blockers


def validate_completed_slices_have_manifest(workspace: Path, manifest_slices: dict[str, Any]) -> list[str]:
    slices_path = workspace / "slices.yaml"
    if not slices_path.exists():
        return []
    data = read_yaml(slices_path)
    slices = data.get("slices") or []
    if isinstance(slices, dict):
        items = slices.values()
    else:
        items = slices
    blockers = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("status") == "complete" and item.get("id") not in manifest_slices:
            blockers.append(f"completed slice missing evidence manifest entry: {item.get('id')}")
    return blockers


def validate_slice_evidence(workspace: Path, slice_id: str) -> list[str]:
    manifest_path = workspace / "evidence/manifest.yaml"
    if not manifest_path.exists():
        return ["missing evidence/manifest.yaml"]
    manifest = read_yaml(manifest_path)
    slice_entry = (manifest.get("slices") or {}).get(slice_id)
    if not isinstance(slice_entry, dict):
        return [f"missing evidence for slice {slice_id}"]
    blockers: list[str] = []
    for phase in ("red", "green", "verification", "review"):
        if phase not in slice_entry:
            blockers.append(f"{slice_id} missing {phase} evidence")
            continue
        blockers.extend(validate_phase_entry(workspace, slice_id, phase, slice_entry[phase]))
    if all(phase in slice_entry for phase in ("red", "green")):
        red_ts = parse_timestamp(slice_entry["red"]["timestamp"])
        green_ts = parse_timestamp(slice_entry["green"]["timestamp"])
        if red_ts >= green_ts:
            blockers.append(f"{slice_id} red evidence timestamp must be before green evidence timestamp")
    if "commit" not in slice_entry and "diff_hash" not in slice_entry:
        blockers.append(f"{slice_id} missing commit or diff_hash")
    return blockers


def validate_phase_entry(workspace: Path, slice_id: str, phase: str, entry: Any) -> list[str]:
    if not isinstance(entry, dict):
        return [f"{slice_id} {phase} evidence must be a mapping"]
    blockers: list[str] = []
    if "timestamp" not in entry:
        blockers.append(f"{slice_id} {phase} evidence missing timestamp")
    else:
        try:
            parse_timestamp(entry["timestamp"])
        except FeatureCtlError as exc:
            blockers.append(str(exc))
    file_fields = ["command_file", "output_file"] if phase in {"red", "green", "verification"} else ["summary_file"]
    if phase in {"red", "green"}:
        file_fields.append("git_state_file")
    for field in file_fields:
        rel = entry.get(field)
        if not rel:
            blockers.append(f"{slice_id} {phase} evidence missing {field}")
        elif evidence_path_blocker(workspace, rel):
            blockers.append(f"{slice_id} {phase} evidence path invalid: {rel}")
        elif not (workspace / "evidence" / rel).exists():
            blockers.append(f"{slice_id} {phase} evidence file missing: {rel}")
    return blockers


def mark_slice_complete(path: Path, slice_id: str) -> None:
    data = read_yaml(path)
    slices = data.get("slices")
    if isinstance(slices, dict):
        items = slices.values()
    else:
        items = slices or []
    found = False
    for item in items:
        if isinstance(item, dict) and item.get("id") == slice_id:
            item["status"] = "complete"
            item["evidence_status"] = "complete"
            found = True
    if not found:
        raise FeatureCtlError(f"slices.yaml has no slice {slice_id}")
    write_yaml(path, data)


def known_slice_ids(workspace: Path) -> set[str]:
    slices_path = workspace / "slices.yaml"
    if not slices_path.exists():
        return set()
    data = read_yaml(slices_path)
    slices = data.get("slices") or []
    if isinstance(slices, dict):
        items = slices.values()
    else:
        items = slices
    return {item.get("id") for item in items if isinstance(item, dict) and item.get("id")}


def ensure_known_slice(workspace: Path, slice_id: str) -> None:
    if not re.match(r"^S-[0-9]{3}$", slice_id):
        raise FeatureCtlError(f"invalid slice id: {slice_id}")
    known = known_slice_ids(workspace)
    if known and slice_id not in known:
        raise FeatureCtlError(f"unknown slice id: {slice_id}")


def add_slice_commit_metadata(workspace: Path, slice_id: str, *, commit: str | None, diff_hash: str | None) -> None:
    manifest_path = workspace / "evidence/manifest.yaml"
    manifest = read_yaml(manifest_path)
    entry = manifest.setdefault("slices", {}).setdefault(slice_id, {})
    if commit:
        entry["commit"] = commit
    if diff_hash:
        entry["diff_hash"] = diff_hash
    write_yaml(manifest_path, manifest)


def evidence_path_blocker(workspace: Path, rel: str) -> bool:
    path = Path(rel)
    if path.is_absolute() or ".." in path.parts:
        return True
    evidence_root = (workspace / "evidence").resolve()
    target = (evidence_root / path).resolve()
    try:
        target.relative_to(evidence_root)
    except ValueError:
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
