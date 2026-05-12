#!/usr/bin/env python3
"""Deterministic helper for the Native Feature Pipeline."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
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
INACTIVE_WORKSPACE_LIFECYCLES = {"promoted-readonly", "archived", "abandoned"}
VALID_WORKSPACE_LIFECYCLES = {"active", "canonical", *INACTIVE_WORKSPACE_LIFECYCLES}
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
    "## Change Delta",
    "## Implementation Summary",
    "## Modules And Responsibilities",
    "## Dependency And Ownership Plan",
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
    "## Decision Traceability",
)
PROFILE_EXAMPLE_KEYS = {
    "source_examples",
    "test_examples",
    "doc_examples",
    "contract_examples",
    "integration_examples",
}


class FeatureCtlError(RuntimeError):
    """Raised for expected command failures."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="featurectl.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="initialize pipeline directories")
    init_parser.add_argument("--profile-project", action="store_true", help="scan repository and update generated .ai/knowledge project context")
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
    complete_slice_parser.add_argument("--append-retry", action="store_true", help="record an explicit retry for an already-complete slice")
    complete_slice_parser.add_argument("--retry-reason", help="required reason when --append-retry is used")
    complete_slice_parser.set_defaults(func=cmd_complete_slice)

    worktree_status_parser = subparsers.add_parser("worktree-status", help="verify feature worktree readiness")
    worktree_status_parser.add_argument("--workspace")
    worktree_status_parser.set_defaults(func=cmd_worktree_status)

    promote_parser = subparsers.add_parser("promote", help="promote feature workspace to canonical memory")
    promote_parser.add_argument("--workspace", required=True)
    promote_parser.add_argument(
        "--conflict",
        choices=["abort", "archive-as-variant"],
        default="abort",
        help="on conflict, abort or archive the incoming workspace as a variant without modifying existing canonical memory",
    )
    promote_parser.set_defaults(func=cmd_promote)

    try:
        args = parser.parse_args(argv)
        args.func(args)
    except FeatureCtlError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_init(args: argparse.Namespace) -> None:
    root = repo_root()
    ensure_init_tree(root)
    if args.profile_project:
        profile = build_project_profile(root)
        write_project_profile(root, profile)
        print("project_profile: updated")
        print(f"project_name: {profile['project']['name']}")
        print(f"source_files: {profile['counts']['source_files']}")
        print(f"test_files: {profile['counts']['test_files']}")
        print(f"detected_feature_signals: {len(profile['feature_signals'])}")
        print(f"detected_feature_catalog_items: {len(profile['feature_catalog'])}")
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
            "lifecycle": "active",
            "read_only": False,
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
    slice_status = slice_completion_status(workspace / "slices.yaml", args.slice_id)
    if slice_status == "complete" and not args.append_retry:
        raise FeatureCtlError(f"slice {args.slice_id} is already complete; use --append-retry to record an explicit retry")
    if args.append_retry and slice_status != "complete":
        raise FeatureCtlError(f"slice {args.slice_id} retry requires an already-complete slice")
    if args.append_retry and not str(args.retry_reason or "").strip():
        raise FeatureCtlError("--append-retry requires --retry-reason")
    manifest_path = workspace / "evidence/manifest.yaml"
    if not manifest_path.exists():
        blockers = ["missing evidence/manifest.yaml"]
    else:
        manifest = read_yaml(manifest_path)
        proposed_manifest = copy.deepcopy(manifest)
        attempt = next_slice_attempt(proposed_manifest, args.slice_id) if args.append_retry else 1
        add_slice_commit_metadata(
            proposed_manifest,
            args.slice_id,
            commit=args.commit,
            diff_hash=args.diff_hash,
            retry=args.append_retry,
            retry_reason=args.retry_reason,
            attempt=attempt,
        )
        blockers = validate_slice_evidence(workspace, args.slice_id, manifest=proposed_manifest)
    if blockers:
        print("slice_evidence: fail")
        for blocker in blockers:
            print(f"- {blocker}")
        raise FeatureCtlError("slice evidence validation failed")

    write_yaml(manifest_path, proposed_manifest)
    mark_slice_complete(workspace / "slices.yaml", args.slice_id)
    append_execution_event(
        workspace,
        "Summary",
        render_slice_completion_event(args.slice_id, retry=args.append_retry, attempt=attempt, reason=args.retry_reason),
    )
    print(f"slice_complete: {args.slice_id}")


def cmd_worktree_status(args: argparse.Namespace) -> None:
    root = repo_root()
    workspace = resolve_workspace(root, args.workspace)
    feature = read_yaml(workspace / "feature.yaml")
    state = read_yaml(workspace / "state.yaml")
    worktree_path = infer_worktree_path(workspace)
    blockers = []
    blockers.extend(status_blockers(root, workspace, feature, state))
    blockers.extend(validate_implementation_minimum(state))
    blockers.extend(validate_current_directory_is_worktree(workspace))

    print("worktree_status: " + ("fail" if blockers else "pass"))
    print(f"feature_key: {feature.get('feature_key')}")
    print(f"worktree: {worktree_path}")
    print(f"current_checkout: {repo_root()}")
    try:
        print(f"branch: {run_git(worktree_path, 'rev-parse', '--abbrev-ref', 'HEAD').strip()}")
    except FeatureCtlError as exc:
        blockers.append(str(exc))
        print("branch: unknown")
    print("implementation_ready: " + ("true" if not blockers else "false"))
    print("blocking_issues:")
    if blockers:
        for blocker in blockers:
            print(f"  - {blocker}")
        raise FeatureCtlError("worktree status failed")
    print("  none")


def cmd_promote(args: argparse.Namespace) -> None:
    root = repo_root()
    workspace = resolve_workspace(root, args.workspace)
    blockers = validate_finish_state(workspace)
    if blockers:
        print("promotion: fail")
        for blocker in blockers:
            print(f"- {blocker}")
        raise FeatureCtlError("feature is not ready for promotion")

    feature = read_yaml(workspace / "feature.yaml")
    state = read_yaml(workspace / "state.yaml")
    canonical = root / feature["canonical_path"]
    archive = root / ".ai/features-archive" / feature["domain"] / feature["slug"] / feature["run_id"]

    if canonical.exists():
        if args.conflict == "abort":
            raise FeatureCtlError(f"canonical feature already exists: {feature['canonical_path']}")
        if archive.exists():
            raise FeatureCtlError(f"archive variant already exists: {archive}")
        archive.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(workspace, archive)
        update_feature_status(archive, "archived", current_step="promote", lifecycle="archived", read_only=True)
        append_execution_event(archive, "Summary", f"- {utc_now()} archived incoming variant for {feature['canonical_path']}")
        update_feature_status(workspace, "archived", current_step="promote", lifecycle="archived", read_only=True)
        regenerate_feature_index(root)
        sync_knowledge_canonical_features(root)
        print("promotion: archived-variant")
        print(f"archive_path: {archive.relative_to(root).as_posix()}")
        return

    canonical.parent.mkdir(parents=True, exist_ok=True)
    if canonical.exists():
        shutil.rmtree(canonical)
    shutil.copytree(workspace, canonical)

    promoted_feature_path = canonical / "feature.yaml"
    promoted_feature = read_yaml(promoted_feature_path)
    promoted_feature["status"] = "complete"
    promoted_feature["canonical_path"] = feature["canonical_path"]
    write_yaml(promoted_feature_path, promoted_feature)

    promoted_state_path = canonical / "state.yaml"
    promoted_state = read_yaml(promoted_state_path)
    promoted_state["current_step"] = "promote"
    promoted_state["lifecycle"] = "canonical"
    promoted_state["read_only"] = True
    promoted_state.setdefault("gates", {})["finish"] = "complete"
    promoted_state.setdefault("stale", {})["canonical_docs"] = False
    promoted_state.setdefault("stale", {})["index"] = False
    write_yaml(promoted_state_path, promoted_state)
    write_latest_status(canonical, "promote")

    update_feature_status(workspace, "promoted-readonly", current_step="promote", lifecycle="promoted-readonly", read_only=True)
    regenerate_feature_index(root)
    sync_knowledge_canonical_features(root)
    append_execution_event(canonical, "Summary", f"- {utc_now()} promoted feature memory to {feature['canonical_path']}")
    print("promotion: complete")
    print(f"canonical_path: {feature['canonical_path']}")


def ensure_init_tree(root: Path) -> None:
    dirs = [
        ".ai/feature-workspaces",
        ".ai/features",
        ".ai/features-archive",
        ".ai/knowledge",
        ".ai/pipeline-docs/global",
        ".agents/pipeline-core/references",
        ".agents/pipeline-core/references/generated-templates",
        ".agents/pipeline-core/scripts/schemas",
        ".agents/skills",
        ".agents/skill-lab/quarantine",
        ".agents/skill-lab/accepted",
        ".agents/skill-lab/rejected",
        "skills/superpowers/subagent-driven-development",
        "methodology/upstream",
        "methodology/docs-snapshots",
        "methodology/extracted",
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


def build_project_profile(root: Path) -> dict[str, Any]:
    files = git_ls_files(root)
    visible_files = [path for path in files if not generated_or_vendor_path(path)]
    source_files = [path for path in visible_files if source_path(path)]
    test_files = [path for path in visible_files if test_path(path)]
    doc_files = [path for path in visible_files if doc_path(path)]
    contract_files = [path for path in visible_files if contract_path(path)]
    integration_files = [path for path in visible_files if integration_path(path)]
    module_dirs = summarize_module_dirs(visible_files)
    package_files = [path for path in visible_files if Path(path).name in package_manifest_names()]
    scripts = collect_project_scripts(root, package_files[:20])
    feature_signals = collect_feature_signals(root, visible_files, doc_files)
    canonical_features = collect_canonical_features(root)
    feature_catalog = build_feature_catalog(canonical_features, feature_signals)

    return {
        "artifact_contract_version": CONTRACT_VERSION,
        "generated_by": "featurectl.py init --profile-project",
        "generated_at": utc_now(),
        "project": {
            "name": infer_project_name(root, package_files),
            "root": ".",
            "branch": safe_git(root, "rev-parse", "--abbrev-ref", "HEAD") or "unknown",
            "head": safe_git(root, "rev-parse", "--short", "HEAD") or "unknown",
            "remote": safe_git(root, "remote", "get-url", "origin") or "none",
        },
        "counts": {
            "tracked_files": len(files),
            "profiled_files": len(visible_files),
            "source_files": len(source_files),
            "test_files": len(test_files),
            "doc_files": len(doc_files),
            "contract_files": len(contract_files),
            "integration_files": len(integration_files),
        },
        "package_manifests": package_files[:30],
        "scripts": scripts,
        "module_dirs": module_dirs,
        "source_examples": source_files[:40],
        "test_examples": test_files[:30],
        "doc_examples": doc_files[:30],
        "contract_examples": contract_files[:30],
        "integration_examples": integration_files[:30],
        "canonical_features": canonical_features,
        "feature_signals": feature_signals[:40],
        "feature_catalog": feature_catalog,
    }


def git_ls_files(root: Path) -> list[str]:
    try:
        output = run_git(root, "ls-files")
    except FeatureCtlError:
        return []
    return [line for line in output.splitlines() if line.strip()]


def generated_or_vendor_path(path: str) -> bool:
    parts = Path(path).parts
    if not parts:
        return True
    ignored_prefixes = (
        ".git",
        ".venv",
        "node_modules",
        "dist",
        "build",
        "coverage",
        ".pytest_cache",
        "__pycache__",
        ".ai/feature-workspaces",
        ".ai/features",
        ".ai/features-archive",
        ".ai/logs",
        "skills",
        "methodology",
        "pipeline-lab/showcases",
        "pipeline-lab/runs",
        "pipeline-lab/benchmarks/scenarios",
    )
    normalized = "/".join(parts)
    return any(normalized == prefix or normalized.startswith(f"{prefix}/") for prefix in ignored_prefixes)


def source_path(path: str) -> bool:
    suffix = Path(path).suffix.lower()
    if suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".kt", ".rb", ".php", ".cs", ".swift", ".vue", ".svelte"}:
        return False
    lowered = path.lower()
    return not test_path(path) and not lowered.endswith((".config.js", ".config.ts", ".d.ts"))


def test_path(path: str) -> bool:
    lowered = path.lower()
    return lowered.startswith(("test/", "tests/")) or any(part in lowered for part in ("/test/", "/tests/", "__tests__", ".test.", ".spec.", "_test."))


def doc_path(path: str) -> bool:
    lowered = path.lower()
    return lowered.endswith((".md", ".mdx", ".rst", ".adoc")) or lowered.startswith("docs/")


def contract_path(path: str) -> bool:
    lowered = path.lower()
    return any(token in lowered for token in ("openapi", "schema", "graphql", "proto", "contract", "migration", "event"))


def integration_path(path: str) -> bool:
    lowered = path.lower()
    return lowered.startswith((".github/", ".gitlab/", "docker", "deploy", "infra", "k8s", "helm")) or any(
        token in lowered for token in ("dockerfile", "compose", "terraform", "workflow", "integration")
    )


def package_manifest_names() -> set[str]:
    return {
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "poetry.lock",
        "pnpm-workspace.yaml",
        "turbo.json",
        "go.mod",
        "Cargo.toml",
        "pom.xml",
        "build.gradle",
        "Gemfile",
        "composer.json",
        "Makefile",
    }


def infer_project_name(root: Path, package_files: list[str]) -> str:
    for path in package_files:
        if Path(path).name == "package.json":
            try:
                package = json.loads((root / path).read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if package.get("name"):
                return str(package["name"])
    remote_name = infer_project_name_from_remote(safe_git(root, "remote", "get-url", "origin"))
    if remote_name:
        return remote_name
    return root.name


def infer_project_name_from_remote(remote: str | None) -> str:
    if not remote:
        return ""
    value = remote.strip().rstrip("/")
    if not value or value == "none":
        return ""
    if value.endswith(".git"):
        value = value[:-4]
    if ":" in value and not value.startswith(("http://", "https://", "ssh://")):
        value = value.rsplit(":", 1)[1]
    return value.rsplit("/", 1)[-1].strip()


def collect_project_scripts(root: Path, package_files: list[str]) -> list[dict[str, str]]:
    scripts: list[dict[str, str]] = []
    for path in package_files:
        file_name = Path(path).name
        if file_name == "package.json":
            try:
                package = json.loads((root / path).read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            for name, command in sorted((package.get("scripts") or {}).items()):
                scripts.append({"source": path, "name": str(name), "command": str(command)})
        elif file_name == "Makefile":
            content = read_repo_file(root, path)
            if content is None:
                continue
            for line in content.splitlines():
                if re.match(r"^[A-Za-z0-9_.-]+:", line) and not line.startswith("."):
                    scripts.append({"source": path, "name": line.split(":", 1)[0], "command": "make target"})
    return scripts[:40]


def summarize_module_dirs(files: list[str]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for path in files:
        parts = Path(path).parts
        if len(parts) < 2:
            continue
        top = parts[0]
        if top.startswith(".") and top not in {".agents", ".ai", ".github"}:
            continue
        counts[top] = counts.get(top, 0) + 1
        if top in {"apps", "packages", "services", "src"} and len(parts) > 2:
            nested = f"{parts[0]}/{parts[1]}"
            counts[nested] = counts.get(nested, 0) + 1
    return [{"path": path, "tracked_files": count} for path, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:30]]


def collect_feature_signals(root: Path, files: list[str], doc_files: list[str]) -> list[dict[str, str]]:
    signals: list[dict[str, str]] = []
    heading_re = re.compile(r"^#{1,3}\s+(.+)")
    signal_doc_files = [path for path in doc_files if feature_signal_candidate_path(path)]
    for path in signal_doc_files[:80]:
        content = read_repo_file(root, path)
        if content is None:
            continue
        for line in content.splitlines()[:300]:
            match = heading_re.match(line.strip())
            if not match:
                continue
            heading = re.sub(r"\s+", " ", match.group(1)).strip()
            if feature_signal_text(heading):
                signals.append({"source": path, "signal": heading, "kind": feature_signal_kind(path)})
                break
    for path in files:
        if not feature_signal_candidate_path(path):
            continue
        if test_path(path):
            continue
        path_signal = feature_signal_from_source_path(path)
        if path_signal:
            signals.append({"source": path, "signal": path_signal, "kind": feature_signal_kind(path)})
        if len(signals) >= 60:
            break
    return dedupe_signal_list(signals)


def feature_signal_candidate_path(path: str) -> bool:
    if Path(path).name in {"AGENTS.md"}:
        return False
    if path in {"plan.md", "vision.md", "features.md"}:
        return False
    if generated_showcase_report_path(path):
        return False
    blocked_prefixes = (
        ".ai/knowledge/",
        ".ai/feature-workspaces/",
        ".ai/features/",
        ".ai/features-archive/",
        ".ai/logs/",
        ".ai/",
        ".ai/pipeline-docs/",
        ".agents/skills/",
        ".agents/pipeline-core/references/",
        ".agents/pipeline-core/references/generated-templates/",
        ".github/",
        ".gitlab/",
        "pipeline-lab/showcases/",
        "pipeline-lab/runs/",
        "pipeline-lab/benchmarks/scenarios/",
    )
    return not any(path.startswith(prefix) for prefix in blocked_prefixes)


def feature_signal_kind(path: str) -> str:
    if path.startswith("pipeline-lab/"):
        return "lab_signal"
    return "detected"


def generated_showcase_report_path(path: str) -> bool:
    if not path.startswith("pipeline-lab/showcases/"):
        return False
    name = Path(path).name
    return name.endswith("-report.md") or name in {
        "validation.md",
        "native-emulation-validation-report.md",
        "native-emulation-judge-report.md",
        "pipeline-goal-validation-report.md",
        "init-profile-report.md",
    }


def feature_signal_text(text: str) -> bool:
    lowered = text.lower()
    ignored = {
        "license",
        "contributing",
        "installation",
        "usage",
        "table of contents",
        "build",
        "check",
        "quality checks",
        "integration tests command",
        "development workflow",
        "release notes",
        "changelog",
    }
    if lowered in ignored:
        return False
    return any(token in lowered for token in ("feature", "workflow", "api", "integration", "architecture", "module", "service", "pipeline", "dashboard"))


def feature_signal_from_source_path(path: str) -> str:
    parts = Path(path).parts
    lower_parts = [part.lower() for part in parts]
    blocked_parts = {
        "components",
        "component",
        "ui",
        "icons",
        "icon",
        "styles",
        "assets",
        "fixtures",
        "mocks",
        "mock",
        "tests",
        "test",
        "__tests__",
        "scripts",
        "generated",
    }
    for marker in ("features", "feature", "domains", "domain", "modules", "module"):
        if marker in lower_parts:
            index = lower_parts.index(marker)
            for candidate in parts[index + 1 : index + 4]:
                candidate_name = path_part_signal(candidate)
                if candidate.lower() not in blocked_parts and normalize_feature_catalog_name(candidate_name):
                    return candidate_name
    for marker in ("routes", "controllers", "services", "workflows", "integrations"):
        if marker in lower_parts:
            index = lower_parts.index(marker)
            if index + 1 < len(parts):
                candidate_name = path_part_signal(parts[index + 1])
                if normalize_feature_catalog_name(candidate_name):
                    return candidate_name
    lowered = path.lower()
    if any(token in lowered for token in ("controller", "service", "workflow", "integration")):
        stem = Path(path).stem.replace("-", " ").replace("_", " ")
        if normalize_feature_catalog_name(stem):
            return stem
    return ""


def path_part_signal(part: str) -> str:
    value = part
    while Path(value).suffix:
        value = Path(value).stem
    return value.replace("-", " ").replace("_", " ").replace(".", " ")


def dedupe_signal_list(signals: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, str]] = []
    for signal in signals:
        key = (signal["source"], signal["signal"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(signal)
    return deduped


def read_repo_file(root: Path, path: str) -> str | None:
    try:
        return (root / path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def build_feature_catalog(canonical_features: list[dict[str, str]], signals: list[dict[str, str]]) -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    for feature in canonical_features:
        name = feature.get("feature_key", "").strip()
        if not name:
            continue
        seen_names.add(name.lower())
        catalog.append(
            {
                "name": name,
                "kind": "canonical",
                "confidence": "high",
                "description": "Promoted feature memory recorded by the Native Feature Pipeline.",
                "source_count": 1,
                "sources": [feature.get("path", "")],
            }
        )

    grouped: dict[str, dict[str, Any]] = {}
    for signal in signals:
        name = normalize_feature_catalog_name(signal.get("signal", ""))
        if not name or name.lower() in seen_names:
            continue
        source = signal.get("source", "")
        entry = grouped.setdefault(
            name.lower(),
            {"name": name, "sources": [], "doc_sources": 0, "source_sources": 0, "lab_sources": 0},
        )
        if source and source not in entry["sources"]:
            entry["sources"].append(source)
            if signal.get("kind") == "lab_signal" or source.startswith("pipeline-lab/"):
                entry["lab_sources"] += 1
            if doc_path(source):
                entry["doc_sources"] += 1
            elif source_path(source):
                entry["source_sources"] += 1

    for entry in sorted(grouped.values(), key=lambda item: (-len(item["sources"]), item["name"].lower())):
        source_count = len(entry["sources"])
        confidence = feature_catalog_confidence(source_count, entry["doc_sources"], entry["source_sources"])
        kind = "lab_signal" if entry["lab_sources"] and entry["lab_sources"] == source_count else "detected"
        catalog.append(
            {
                "name": entry["name"],
                "kind": kind,
                "confidence": confidence,
                "description": feature_catalog_description(
                    entry["name"],
                    source_count,
                    entry["doc_sources"],
                    entry["source_sources"],
                    lab_sources=entry["lab_sources"],
                    kind=kind,
                ),
                "source_count": source_count,
                "sources": entry["sources"][:6],
            }
        )
        if len(catalog) >= 30:
            break
    return catalog


def normalize_feature_catalog_name(text: str) -> str:
    value = re.sub(r"\s+", " ", text or "").strip(" #-:._")
    value = re.sub(r"^(feature|workflow|service|controller|route|api|module)\s*[:/-]\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^(test|tests?)\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\b(ts|tsx|js|jsx|py|go|vue|yml|yaml|md|mdx)\b$", "", value, flags=re.IGNORECASE).strip()
    value = value.strip(" #-:._")
    if not value:
        return ""
    lowered = value.lower()
    generic = {
        "index",
        "overview",
        "readme",
        "skill",
        "openai",
        "configuration",
        "config",
        "setup",
        "install",
        "usage",
        "api",
        "service",
        "controller",
        "route",
        "routes",
        "page",
        "header",
        "wrapper",
        "action",
        "actions",
        "build",
        "check",
        "quality checks",
        "integration tests command",
        "development workflow",
        "gitignore",
        "agent docs",
        "features",
        "changed files",
        "release notes",
        "changelog",
        "autofix",
        "feature requests",
        "package",
        "breaking",
        "fixtures",
        "globalsetup",
        "globalteardown",
        "global setup",
        "global teardown",
        "integration tests",
        "admin seeder",
        "admin seeder js",
        "batch job seeder",
        "batch job seeder js",
        "bootstrap app",
        "architecture package structure",
        "architecture notes",
        "run the services in the background",
        "call helpers",
        "cart seeder",
        "claim seeder",
    }
    if lowered in generic or lowered.endswith((".schema", " seeder", " helpers")):
        return ""
    words = [word for word in re.split(r"[^A-Za-z0-9]+", value) if word]
    if len(words) == 1 and len(words[0]) < 4:
        return ""
    return " ".join(word if word.isupper() else word[:1].upper() + word[1:] for word in words)


def feature_catalog_confidence(source_count: int, doc_sources: int, source_sources: int) -> str:
    if source_count >= 3 and doc_sources:
        return "high"
    if source_count >= 2 or doc_sources or source_sources >= 2:
        return "medium"
    return "low"


def feature_catalog_description(
    name: str,
    source_count: int,
    doc_sources: int,
    source_sources: int,
    *,
    lab_sources: int = 0,
    kind: str = "detected",
) -> str:
    if kind == "lab_signal":
        return (
            f"{name} appears only in {lab_sources or source_count} pipeline-lab signal"
            f"{'s' if (lab_sources or source_count) != 1 else ''}; use lab_signal only for pipeline-lab or benchmark work."
        )
    sources = []
    if doc_sources:
        sources.append(f"{doc_sources} documentation signal{'s' if doc_sources != 1 else ''}")
    if source_sources:
        sources.append(f"{source_sources} source signal{'s' if source_sources != 1 else ''}")
    if not sources:
        sources.append(f"{source_count} repository signal{'s' if source_count != 1 else ''}")
    source_summary = " and ".join(sources)
    return f"{name} appears in {source_summary}; inspect the listed files before relying on this as architecture truth."


def collect_canonical_features(root: Path) -> list[dict[str, str]]:
    index_path = root / ".ai/features/index.yaml"
    features: list[dict[str, str]] = []
    if index_path.exists():
        try:
            data = read_yaml(index_path)
        except FeatureCtlError:
            data = {}
        for item in data.get("features") or []:
            if isinstance(item, dict):
                features.append(
                    {
                        "feature_key": str(item.get("feature_key") or item.get("key") or "unknown"),
                        "path": str(item.get("path") or item.get("canonical_path") or ""),
                    }
                )
    for card in sorted((root / ".ai/features").glob("*/*/feature-card.md")):
        features.append({"feature_key": "/".join(card.parts[-3:-1]), "path": str(card.relative_to(root))})
    return dedupe_canonical_features(features)


def dedupe_canonical_features(features: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for feature in features:
        key = feature.get("feature_key", "")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(feature)
    return deduped[:40]


def write_project_profile(root: Path, profile: dict[str, Any]) -> None:
    knowledge = root / ".ai/knowledge"
    knowledge.mkdir(parents=True, exist_ok=True)
    write_yaml(knowledge / "project-index.yaml", compact_project_index_profile(profile))
    write_yaml(knowledge / "profile-examples.yaml", profile_examples(profile))
    write_generated_doc(knowledge / "project-snapshot.md", render_project_snapshot(profile))
    write_generated_doc(knowledge / "project-overview.md", render_project_overview(profile))
    write_generated_doc(knowledge / "features-overview.md", render_features_overview(profile))
    write_generated_doc(knowledge / "discovered-signals.md", render_discovered_signals(profile))
    write_generated_doc(knowledge / "module-map.md", render_module_map(profile))
    write_generated_doc(knowledge / "architecture-overview.md", render_architecture_overview(profile))
    write_generated_doc(knowledge / "testing-overview.md", render_testing_overview(profile))
    write_generated_doc(knowledge / "contracts-overview.md", render_contracts_overview(profile))
    write_generated_doc(knowledge / "integration-map.md", render_integration_map(profile))


def sync_knowledge_canonical_features(root: Path) -> None:
    """Refresh canonical feature memory after promotion without storing local paths."""
    profile = build_project_profile(root)
    profile["generated_by"] = "featurectl.py promote canonical sync"
    profile["generated_at"] = utc_now()
    profile.setdefault("project", {})["root"] = "."
    knowledge = root / ".ai/knowledge"
    knowledge.mkdir(parents=True, exist_ok=True)
    write_yaml(knowledge / "project-index.yaml", compact_project_index_profile(profile))
    write_yaml(knowledge / "profile-examples.yaml", profile_examples(profile))
    write_text(knowledge / "features-overview.md", render_features_overview(profile))
    write_text(knowledge / "discovered-signals.md", render_discovered_signals(profile))


def compact_project_index_profile(profile: dict[str, Any]) -> dict[str, Any]:
    compact = copy.deepcopy(profile)
    for key in PROFILE_EXAMPLE_KEYS:
        compact.pop(key, None)
    project = compact.get("project")
    if isinstance(project, dict):
        project.pop("branch", None)
        project.pop("head", None)
    return compact


def profile_examples(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_contract_version": CONTRACT_VERSION,
        "generated_by": profile.get("generated_by", "featurectl.py init --profile-project"),
        "generated_at": profile.get("generated_at", utc_now()),
        **{key: profile.get(key, []) for key in sorted(PROFILE_EXAMPLE_KEYS)},
    }


def write_generated_doc(path: Path, content: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    can_replace = not existing.strip() or "Status: initial" in existing or "Status: provisional" in existing or "Generated by featurectl project profile" in existing
    if can_replace:
        path.write_text(content, encoding="utf-8")
    else:
        generated = path.with_name(f"{path.stem}.generated{path.suffix}")
        generated.write_text(content, encoding="utf-8")


def render_project_snapshot(profile: dict[str, Any]) -> str:
    project = profile["project"]
    counts = profile["counts"]
    return f"""# Project Snapshot

Status: generated
Confidence: medium
Needs human review: yes
Generated by featurectl project profile: {profile['generated_at']}

## Identity

- Name: `{project['name']}`
- Branch: `{project['branch']}`
- HEAD: `{project['head']}`
- Remote: `{project['remote']}`

## Counts

- Tracked files: {counts['tracked_files']}
- Profiled files: {counts['profiled_files']}
- Source files: {counts['source_files']}
- Test files: {counts['test_files']}
- Documentation files: {counts['doc_files']}
- Contract/schema files: {counts['contract_files']}
- Integration/deployment files: {counts['integration_files']}

## Use In Feature Pipeline

Treat this as a source-backed map, not as final architecture truth. Feature
steps must still inspect the cited files before making behavior or design
claims.
"""


def render_project_overview(profile: dict[str, Any]) -> str:
    project = profile["project"]
    package_lines = bullet_list(profile["package_manifests"], empty="No package manifests detected.")
    catalog_lines = feature_catalog_lines(profile.get("feature_catalog", [])[:10], empty="No current feature catalog entries detected.")
    feature_lines = signal_lines(profile["feature_signals"][:12], empty="No feature-like signals detected from docs or paths.")
    return f"""# Project Overview

Status: generated
Confidence: medium
Needs human review: yes
Generated by featurectl project profile: {profile['generated_at']}

This repository appears to be `{project['name']}`.

## Package And Tooling Signals

{package_lines}

## Current Feature Picture

{catalog_lines}

## Detected Feature Signals

{feature_lines}

## Sources Inspected

- `git ls-files`
- `.ai/features/index.yaml`
- README/docs headings
- source, test, contract, and integration path patterns
"""


def render_features_overview(profile: dict[str, Any]) -> str:
    canonical = profile["canonical_features"]
    canonical_lines = "\n".join(f"- `{item['feature_key']}` from `{item['path']}`" for item in canonical) or "No canonical features have been promoted yet."
    return f"""# Features Overview

Status: generated
Confidence: medium
Needs human review: yes
Generated by featurectl project profile: {profile['generated_at']}

## Canonical Feature Memory

{canonical_lines}
"""


def render_discovered_signals(profile: dict[str, Any]) -> str:
    catalog = profile.get("feature_catalog", [])
    canonical = [item for item in catalog if item.get("kind") == "canonical"]
    noncanonical = [item for item in catalog if item.get("kind") != "canonical"]
    canonical_lines = signal_catalog_blocks(canonical, empty="No canonical signals detected.")
    noncanonical_lines = signal_catalog_blocks(noncanonical, empty="No noncanonical signals detected.")
    signal_text = signal_lines(profile["feature_signals"][:30], empty="No feature-like signals detected from docs or paths.")
    return f"""# Discovered Signals

Status: generated
Confidence: low
Needs human review: yes
Generated by featurectl project profile: {profile['generated_at']}

## Canonical Signals

Canonical signals are promoted feature memories. Prefer these before detected
or lab-only signals.

{canonical_lines}

## Noncanonical Signals

Noncanonical signals are source leads. They are not product or architecture truth
until the cited files are inspected. Use `lab_signal` only for pipeline-lab,
benchmark, showcase, or validation-tooling work.

{noncanonical_lines}

## Detected Feature Signals

{signal_text}
"""


def render_module_map(profile: dict[str, Any]) -> str:
    module_lines = "\n".join(f"- `{item['path']}`: {item['tracked_files']} tracked files" for item in profile["module_dirs"]) or "No module directories detected."
    source_lines = bullet_list(profile["source_examples"][:20], empty="No source examples detected.")
    return f"""# Module Map

Status: generated
Confidence: medium
Needs human review: yes
Generated by featurectl project profile: {profile['generated_at']}

## Directory Weight

{module_lines}

## Source Examples

{source_lines}
"""


def render_architecture_overview(profile: dict[str, Any]) -> str:
    packages = "\n".join(f"- `{path}`" for path in profile["package_manifests"][:15]) or "No package manifests detected."
    modules = "\n".join(f"- `{item['path']}`" for item in profile["module_dirs"][:10]) or "No module directories detected."
    return f"""# Architecture Overview

Status: generated
Confidence: medium
Needs human review: yes
Generated by featurectl project profile: {profile['generated_at']}

## Architecture Signals

{packages}

## Likely Module Boundaries

{modules}

## Feature Topology Reuse

Feature architecture artifacts must include a Mermaid feature topology and a
`Shared Knowledge Impact` section. Finish artifacts must record how completed
features update `.ai/knowledge/features-overview.md`,
`.ai/knowledge/architecture-overview.md`, `.ai/knowledge/module-map.md`, and
`.ai/knowledge/integration-map.md`.

Architecture claims for a feature must cite the exact modules and files read
during context discovery.
"""


def render_testing_overview(profile: dict[str, Any]) -> str:
    script_lines = "\n".join(f"- `{item['name']}` from `{item['source']}`: `{item['command']}`" for item in profile["scripts"] if "test" in item["name"].lower()) or "No test scripts detected."
    test_lines = bullet_list(profile["test_examples"][:20], empty="No test files detected.")
    return f"""# Testing Overview

Status: generated
Confidence: medium
Needs human review: yes
Generated by featurectl project profile: {profile['generated_at']}

## Test Commands

{script_lines}

## Test File Examples

{test_lines}
"""


def render_contracts_overview(profile: dict[str, Any]) -> str:
    return f"""# Contracts Overview

Status: generated
Confidence: medium
Needs human review: yes
Generated by featurectl project profile: {profile['generated_at']}

## Contract And Schema Examples

{bullet_list(profile['contract_examples'][:30], empty='No contract/schema files detected.')}
"""


def render_integration_map(profile: dict[str, Any]) -> str:
    return f"""# Integration Map

Status: generated
Confidence: medium
Needs human review: yes
Generated by featurectl project profile: {profile['generated_at']}

## Integration And Deployment Examples

{bullet_list(profile['integration_examples'][:30], empty='No integration/deployment files detected.')}
"""


def bullet_list(items: list[str], *, empty: str) -> str:
    return "\n".join(f"- `{item}`" for item in items) if items else empty


def signal_lines(items: list[dict[str, str]], *, empty: str) -> str:
    return "\n".join(f"- `{item['source']}` [{item.get('kind', 'detected')}]: {item['signal']}" for item in items) if items else empty


def feature_catalog_lines(items: list[dict[str, Any]], *, empty: str) -> str:
    if not items:
        return empty
    lines = []
    for item in items:
        sources = ", ".join(f"`{source}`" for source in item.get("sources", [])[:3] if source) or "`unknown`"
        kind = item.get("kind", "detected")
        reason_label = "Canonical reason" if kind == "canonical" else "Why not canonical"
        lines.extend(
            [
                f"- Signal: {item.get('name', 'unknown')}",
                f"  - Kind: {kind}",
                f"  - Confidence: {item.get('confidence', 'low')}",
                f"  - Source count: {item.get('source_count', 0)}",
                f"  - {reason_label}: {item.get('description', 'Inspect cited sources before using this feature signal.')}",
                f"  - Sources: {sources}",
            ]
        )
    return "\n".join(lines)


def signal_catalog_blocks(items: list[dict[str, Any]], *, empty: str) -> str:
    if not items:
        return empty
    blocks = []
    for item in items:
        name = item.get("name", "unknown")
        kind = item.get("kind", "detected")
        reason_label = "Canonical reason" if kind == "canonical" else "Why not canonical"
        sources = item.get("sources", [])[:6]
        source_lines = "\n".join(f"  - `{source}`" for source in sources if source) or "  - `unknown`"
        blocks.append(
            "\n".join(
                [
                    f"### {name}",
                    "",
                    f"- Kind: {kind}",
                    f"- Confidence: {item.get('confidence', 'low')}",
                    f"- Source count: {item.get('source_count', 0)}",
                    f"- {reason_label}: {item.get('description', 'Inspect cited sources before using this feature signal.')}",
                    "- Sources:",
                    source_lines,
                ]
            )
        )
    return "\n\n".join(blocks)


def safe_git(root: Path, *args: str) -> str | None:
    try:
        return run_git(root, *args).strip()
    except FeatureCtlError:
        return None


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

## Event Log

- {now} event_type=run_initialized step=context next=nfp-01-context

## History

- Initial current step: context
- Initial next step: nfp-01-context

## Current Run State

Current step: context
Next recommended skill: nfp-01-context
Blocking issues: none
Last updated: {now}
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
    if workspace_inactive_lifecycle(feature, state):
        return blockers
    try:
        workspace.relative_to(root / ".ai/features")
        is_canonical_memory = current_step == "promote"
    except ValueError:
        is_canonical_memory = False
    if is_canonical_memory:
        return blockers
    worktree_info = state.get("worktree") or {}
    worktree_value = worktree_info.get("path")
    branch_value = worktree_info.get("branch")
    if worktree_value:
        worktree_path = infer_worktree_path(workspace)
        configured_worktree_path = resolve_configured_worktree_path(root, worktree_value)
        if configured_worktree_path.exists() and configured_worktree_path != worktree_path:
            blockers.append(f"state.yaml worktree.path mismatch: expected {worktree_value}, actual {worktree_path}")
        elif not configured_worktree_path.exists() and configured_worktree_path.name != worktree_path.name:
            blockers.append(f"worktree path does not exist: {worktree_value}")
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
    blockers.extend(validate_execution_latest_status(workspace, state))
    blockers.extend(validate_repository_source_truth(root, workspace, feature, state))

    if readiness:
        blockers.extend(validate_readiness_minimum(workspace, state))
    if implementation:
        blockers.extend(validate_implementation_minimum(state))
        blockers.extend(validate_current_directory_is_worktree(workspace))
    if evidence:
        blockers.extend(validate_evidence_minimum(workspace))
    if review:
        blockers.extend(validate_review_minimum(workspace))
    if state.get("current_step") in {"verification", "finish", "promote"}:
        blockers.extend(validate_verification_if_started(workspace, state))
    if state.get("current_step") in {"finish", "promote"} or (state.get("gates") or {}).get("finish") in {"drafted", "approved", "delegated", "complete"}:
        blockers.extend(validate_finish_if_started(workspace, state))
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
    lifecycle = state.get("lifecycle")
    if lifecycle is not None and lifecycle not in VALID_WORKSPACE_LIFECYCLES:
        blockers.append(f"state.yaml invalid lifecycle: {lifecycle}")
    if state.get("read_only") is not None and not isinstance(state.get("read_only"), bool):
        blockers.append("state.yaml read_only must be boolean")
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
    blockers.extend(validate_docs_consulted(workspace, "Feature Contract"))
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
        "## Change Delta",
        "## System Context",
        "## Component Interactions",
        "## Feature Topology",
        "## Diagrams",
        "## Security Model",
        "## Failure Modes",
        "## Observability",
        "## Rollback Strategy",
        "## Migration Strategy",
        "## Architecture Risks",
        "## Alternatives Considered",
        "## Shared Knowledge Impact",
        "## Completeness Correctness Coherence",
        "## ADRs",
    )
    blockers = [f"architecture.md missing heading: {heading}" for heading in required_headings if heading not in content]
    lower = content.lower()
    if "```mermaid" not in lower or not any(token in lower for token in ("flowchart", "graph ", "sequencediagram")):
        blockers.append("architecture.md requires mermaid feature topology diagram")
    if "-->" not in content and "->>" not in content:
        blockers.append("architecture.md mermaid topology must show communication arrows")
    if ".ai/knowledge/" not in content:
        blockers.append("architecture.md must describe shared knowledge impact using .ai/knowledge paths")
    blockers.extend(validate_docs_consulted(workspace, "Architecture"))
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
    blockers.extend(validate_docs_consulted(workspace, "Technical Design"))
    return blockers


def validate_slices_if_started(workspace: Path, state: dict[str, Any]) -> list[str]:
    gate = (state.get("gates") or {}).get("slicing_readiness")
    if gate not in {"drafted", "approved", "delegated", "complete"}:
        return []
    slices_path = workspace / "slices.yaml"
    if not slices_path.exists():
        return ["slicing_readiness gate requires slices.yaml"]
    blockers = validate_slices_file(slices_path, workspace=workspace)
    blockers.extend(validate_docs_consulted(workspace, "Slicing"))
    return blockers


def validate_docs_consulted(workspace: Path, step_label: str) -> list[str]:
    execution_path = workspace / "execution.md"
    execution = execution_path.read_text(encoding="utf-8") if execution_path.exists() else ""
    marker = f"Docs Consulted: {step_label}"
    if marker not in execution:
        return [f"execution.md missing {marker}"]
    return []


def validate_execution_latest_status(workspace: Path, state: dict[str, Any]) -> list[str]:
    current_step = state.get("current_step")
    gates = state.get("gates") or {}
    if current_step not in {"finish", "promote"} and gates.get("finish") != "complete":
        return []
    execution_path = workspace / "execution.md"
    if not execution_path.exists():
        return ["execution.md missing"]
    execution = execution_path.read_text(encoding="utf-8")
    blockers: list[str] = []
    current_matches = list(re.finditer(r"^## Current Run State\s*$", execution, flags=re.MULTILINE))
    if len(current_matches) != 1:
        blockers.append("execution.md must contain exactly one active ## Current Run State section")
    if re.search(r"^## Latest Status\s*$", execution, flags=re.MULTILINE):
        blockers.append("execution.md must not contain deprecated ## Latest Status section")
    if not re.search(r"^## Event Log\s*$", execution, flags=re.MULTILINE):
        blockers.append("execution.md missing ## Event Log")
    if not re.search(r"^## History\s*$", execution, flags=re.MULTILINE):
        blockers.append("execution.md missing ## History")
    event_match = re.search(r"^## Event Log\s*$", execution, flags=re.MULTILINE)
    history_match = re.search(r"^## History\s*$", execution, flags=re.MULTILINE)
    if current_matches and event_match and event_match.start() > current_matches[0].start():
        blockers.append("execution.md Current Run State must appear after ## Event Log")
    if current_matches and history_match and history_match.start() > current_matches[0].start():
        blockers.append("execution.md Current Run State must appear after ## History")
    blockers.extend(validate_no_active_legacy_execution_sections(execution))
    blockers.extend(validate_events_are_in_event_log(execution))
    blockers.extend(validate_execution_completion_events(execution))
    if not current_matches:
        return blockers
    current_state = execution[current_matches[0].end() :]
    next_heading = re.search(r"\n##\s+", current_state)
    if next_heading:
        current_state = current_state[: next_heading.start()]
    fields = {
        "Current step": None,
        "Next recommended skill": None,
        "Blocking issues": None,
        "Last updated": None,
    }
    for line in current_state.splitlines():
        for field in fields:
            prefix = f"{field}:"
            if line.startswith(prefix):
                fields[field] = line[len(prefix) :].strip()
    for field, value in fields.items():
        if not value:
            blockers.append(f"execution.md Current Run State missing {field}")
    current_state_step = fields.get("Current step")
    if current_state_step and current_state_step != current_step:
        blockers.append(
            f"execution.md Current Run State current step {current_state_step} does not match state.yaml current_step {current_step}"
        )
    return blockers


def validate_no_active_legacy_execution_sections(execution: str) -> list[str]:
    blockers: list[str] = []
    for heading in ("Current Step", "Next Step"):
        if re.search(rf"^## {re.escape(heading)}\s*$", execution, flags=re.MULTILINE):
            blockers.append(f"execution.md contains active legacy ## {heading} section outside History")
    return blockers


def validate_events_are_in_event_log(execution: str) -> list[str]:
    blockers: list[str] = []
    event_log = extract_markdown_section(execution, "Event Log")
    if event_log is None:
        return blockers
    outside = execution.replace(event_log, "")
    for line in outside.splitlines():
        if re.match(r"^-\s+\d{4}-.*(?:gate=|event_type=|completed slice)", line):
            blockers.append("execution.md contains event entry outside ## Event Log")
            break
    return blockers


def extract_markdown_section(markdown: str, heading: str) -> str | None:
    match = re.search(rf"^## {re.escape(heading)}\s*$", markdown, flags=re.MULTILINE)
    if not match:
        return None
    rest = markdown[match.start() :]
    next_heading = re.search(r"\n##\s+", rest[1:])
    if next_heading:
        return rest[: next_heading.start() + 1]
    return rest


def validate_execution_completion_events(execution: str) -> list[str]:
    blockers: list[str] = []
    seen: set[str] = set()
    event_log = extract_markdown_section(execution, "Event Log") or execution
    for line in event_log.splitlines():
        structured = re.search(r"\bevent_type=(slice_completed|slice_retry_completed)\b.*\bslice=(S-[0-9]{3})\b", line)
        if structured:
            event_type = structured.group(1)
            slice_id = structured.group(2)
            if event_type == "slice_completed":
                attempt_match = re.search(r"\battempt=([0-9]+)\b", line)
                reason_match = re.search(r"\breason=initial\b", line)
                if slice_id in seen:
                    blockers.append(f"execution.md duplicate completed slice event for {slice_id}")
                if not attempt_match or int(attempt_match.group(1)) != 1:
                    blockers.append(f"execution.md completed slice event for {slice_id} missing attempt=1")
                if not reason_match:
                    blockers.append(f"execution.md completed slice event for {slice_id} missing reason=initial")
                seen.add(slice_id)
            else:
                attempt_match = re.search(r"\battempt=([0-9]+)\b", line)
                reason_match = re.search(r"\breason=([^\s]+)\b", line)
                supersedes_match = re.search(r"\bsupersedes=attempt-[0-9]+\b", line)
                if not attempt_match or int(attempt_match.group(1)) < 2:
                    blockers.append(f"execution.md retry completed slice event for {slice_id} missing attempt>=2")
                if not reason_match:
                    blockers.append(f"execution.md retry completed slice event for {slice_id} missing reason")
                if not supersedes_match:
                    blockers.append(f"execution.md retry completed slice event for {slice_id} missing supersedes")
            continue
        match = re.search(r"\bcompleted slice (S-[0-9]{3})\b", line)
        if match:
            blockers.append(f"execution.md unstructured completed slice event for {match.group(1)}; use event_type=slice_completed")
    return blockers


def validate_repository_source_truth(root: Path, workspace: Path, feature: dict[str, Any], state: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    index_path = root / ".ai/features/index.yaml"
    if not index_path.exists():
        return blockers
    try:
        index = read_yaml(index_path)
    except FeatureCtlError as exc:
        return [str(exc)]
    features = index.get("features") or []
    if not isinstance(features, list):
        return ["features index features must be a list"]

    overview_path = root / ".ai/features/overview.md"
    overview = overview_path.read_text(encoding="utf-8") if overview_path.exists() else ""
    complete_keys: set[str] = set()
    for item in features:
        if not isinstance(item, dict):
            blockers.append("features index entries must be mappings")
            continue
        feature_key = str(item.get("feature_key") or "")
        status = item.get("status")
        path = str(item.get("path") or "")
        if not feature_key:
            blockers.append("features index entry missing feature_key")
            continue
        if status == "complete":
            complete_keys.add(feature_key)
            if feature_key not in overview:
                blockers.append(f".ai/features/overview.md missing canonical feature {feature_key}")
            canonical_dir = root / path if path else root / ".ai/features" / feature_key
            canonical_feature_path = canonical_dir / "feature.yaml"
            if not canonical_feature_path.exists():
                blockers.append(f"canonical feature {feature_key} missing feature.yaml")
                continue
            canonical_feature = read_yaml(canonical_feature_path)
            if canonical_feature.get("status") == "draft":
                blockers.append(f"canonical feature {feature_key} is indexed complete but feature.yaml status is draft")

    if complete_keys:
        knowledge_overview_path = root / ".ai/knowledge/features-overview.md"
        if not knowledge_overview_path.exists():
            blockers.append(".ai/knowledge/features-overview.md missing canonical feature memory")
        else:
            knowledge_overview = knowledge_overview_path.read_text(encoding="utf-8")
            for feature_key in sorted(complete_keys):
                if feature_key not in knowledge_overview:
                    blockers.append(f".ai/knowledge/features-overview.md missing canonical feature {feature_key}")

        project_index_path = root / ".ai/knowledge/project-index.yaml"
        if not project_index_path.exists():
            blockers.append(".ai/knowledge/project-index.yaml missing canonical feature memory")
        else:
            project_index = read_yaml(project_index_path)
            project_root = str((project_index.get("project") or {}).get("root") or "")
            if project_root and Path(project_root).is_absolute():
                blockers.append(".ai/knowledge/project-index.yaml project.root must be repository-relative")
            canonical_items = project_index.get("canonical_features") or []
            canonical_keys = {str(item.get("feature_key") or "") for item in canonical_items if isinstance(item, dict)}
            for feature_key in sorted(complete_keys):
                if feature_key not in canonical_keys:
                    blockers.append(f".ai/knowledge/project-index.yaml missing canonical feature {feature_key}")

    active_workspaces = sorted((root / ".ai/feature-workspaces").glob("*/*/feature.yaml"))
    if is_active_workspace(root, workspace):
        active_workspaces.append(workspace / "feature.yaml")
    seen_active_paths: set[Path] = set()
    for active_feature_path in active_workspaces:
        active_feature_path = active_feature_path.resolve()
        if active_feature_path in seen_active_paths or not active_feature_path.exists():
            continue
        seen_active_paths.add(active_feature_path)
        active_workspace = active_feature_path.parent
        active_feature = read_yaml(active_feature_path)
        active_key = active_feature.get("feature_key")
        if active_key not in complete_keys:
            continue
        active_state_path = active_workspace / "state.yaml"
        active_state = read_yaml(active_state_path) if active_state_path.exists() else {}
        if not workspace_inactive_lifecycle(active_feature, active_state):
            blockers.append(f"active workspace {active_key} duplicates complete canonical feature without inactive lifecycle")
    return blockers


def workspace_inactive_lifecycle(feature: dict[str, Any], state: dict[str, Any]) -> bool:
    status = str(feature.get("status") or "")
    lifecycle = str(state.get("lifecycle") or "")
    return status in INACTIVE_WORKSPACE_LIFECYCLES and lifecycle in INACTIVE_WORKSPACE_LIFECYCLES and state.get("read_only") is True


def is_active_workspace(root: Path, workspace: Path) -> bool:
    resolved = workspace.resolve()
    for inactive_root in (root / ".ai/features", root / ".ai/features-archive"):
        try:
            resolved.relative_to(inactive_root.resolve())
            return False
        except ValueError:
            pass
    try:
        resolved.relative_to((root / ".ai/feature-workspaces").resolve())
    except ValueError:
        return (workspace / "feature.yaml").exists() and (workspace / "state.yaml").exists()
    return True


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
            "complexity",
            "critical_path",
            "parallelizable",
            "file_ownership",
            "conflict_risk",
            "dependency_notes",
            "expected_touchpoints",
            "scope_confidence",
            "test_strategy",
            "verification_commands",
            "review_focus",
            "evidence_status",
            "status",
            "iteration_budget",
            "rollback_point",
            "independent_verification",
            "failure_triage_notes",
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
        if not isinstance(item.get("complexity"), int) or not 1 <= item.get("complexity", 0) <= 10:
            blockers.append(f"{prefix} complexity must be an integer from 1 to 10")
        if not isinstance(item.get("critical_path"), bool):
            blockers.append(f"{prefix} critical_path must be true or false")
        if not isinstance(item.get("parallelizable"), bool):
            blockers.append(f"{prefix} parallelizable must be true or false")
        if item.get("conflict_risk") not in {"low", "medium", "high"}:
            blockers.append(f"{prefix} conflict_risk must be low, medium, or high")
        file_ownership = item.get("file_ownership")
        if not isinstance(file_ownership, list) or not file_ownership:
            blockers.append(f"{prefix} file_ownership must be a non-empty list")
        for field in ("dependency_notes", "test_strategy"):
            if field in item and not str(item.get(field) or "").strip():
                blockers.append(f"{prefix} {field} must not be empty")
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
        if not isinstance(item.get("iteration_budget"), int) or item.get("iteration_budget", 0) < 1:
            blockers.append(f"{prefix} iteration_budget must be a positive integer")
        for field in ("rollback_point", "independent_verification", "failure_triage_notes"):
            if field in item and not str(item.get(field) or "").strip():
                blockers.append(f"{prefix} {field} must not be empty")
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


def validate_current_directory_is_worktree(workspace: Path) -> list[str]:
    worktree_path = infer_worktree_path(workspace)
    current_checkout = repo_root()
    if current_checkout != worktree_path:
        return [f"current checkout is not configured feature worktree: {worktree_path}"]
    return []


def validate_evidence_minimum(workspace: Path) -> list[str]:
    manifest = workspace / "evidence/manifest.yaml"
    if not manifest.exists():
        return ["evidence validation requires evidence/manifest.yaml"]
    return validate_evidence_manifest(workspace)


def validate_review_minimum(workspace: Path) -> list[str]:
    blockers: list[str] = []
    review_files = sorted(workspace.glob("reviews/*.yaml"))
    if not review_files:
        return ["review validation requires at least one reviews/*.yaml file"]
    for review_file in review_files:
        review = read_yaml(review_file)
        blockers.extend(validate_review_file(review_file, review, workspace))
        if review.get("blocking") is True and review.get("severity") == "critical":
            blockers.append(f"critical review finding blocks verification: {review_file.relative_to(workspace)}")
    return blockers


def validate_review_file(path: Path, review: dict[str, Any], workspace: Path) -> list[str]:
    blockers = []
    required = (
        "artifact_contract_version",
        "review_id",
        "tier",
        "severity",
        "finding",
        "artifact",
        "evidence",
        "recommendation",
        "blocking",
        "linked_requirement_ids",
        "linked_slice_ids",
        "file_refs",
        "reproduction_or_reasoning",
        "fix_verification_command",
        "re_review_required",
    )
    for field in required:
        if field not in review:
            blockers.append(f"{path.relative_to(workspace)} missing {field}")
    if review.get("artifact_contract_version") != CONTRACT_VERSION:
        blockers.append(f"{path.relative_to(workspace)} artifact_contract_version mismatch")
    if review.get("severity") not in {"critical", "major", "minor", "note"}:
        blockers.append(f"{path.relative_to(workspace)} invalid severity")
    if not isinstance(review.get("blocking"), bool):
        blockers.append(f"{path.relative_to(workspace)} blocking must be boolean")
    if review.get("severity") == "critical" and review.get("blocking") is not True:
        blockers.append(f"{path.relative_to(workspace)} critical severity must be blocking")
    for field in ("linked_requirement_ids", "linked_slice_ids", "file_refs"):
        if field in review and not isinstance(review.get(field), list):
            blockers.append(f"{path.relative_to(workspace)} {field} must be a list")
    for field in ("reproduction_or_reasoning", "fix_verification_command"):
        if field in review and not str(review.get(field) or "").strip():
            blockers.append(f"{path.relative_to(workspace)} {field} must not be empty")
    if "re_review_required" in review and not isinstance(review.get("re_review_required"), bool):
        blockers.append(f"{path.relative_to(workspace)} re_review_required must be boolean")
    return blockers


def validate_verification_if_started(workspace: Path, state: dict[str, Any]) -> list[str]:
    gate = (state.get("gates") or {}).get("verification")
    if gate not in {"drafted", "approved", "delegated", "complete"}:
        return []
    blockers = []
    verification_review = workspace / "reviews/verification-review.md"
    if not verification_review.exists():
        blockers.append("verification gate requires reviews/verification-review.md")
    else:
        content = verification_review.read_text(encoding="utf-8")
        for heading in ("## Manual Validation", "## Verification Debt"):
            if heading not in content:
                blockers.append(f"verification review missing heading: {heading}")
    final_output = workspace / "evidence/final-verification-output.log"
    if not final_output.exists():
        blockers.append("verification gate requires evidence/final-verification-output.log")
    elif not final_output.read_text(encoding="utf-8").strip():
        blockers.append("verification gate requires non-empty final verification output")
    blockers.extend(validate_review_minimum(workspace))
    return blockers


def validate_finish_if_started(workspace: Path, state: dict[str, Any]) -> list[str]:
    gate = (state.get("gates") or {}).get("finish")
    if gate not in {"drafted", "approved", "delegated", "complete"} and state.get("current_step") not in {"finish", "promote"}:
        return []
    blockers = []
    feature_card = workspace / "feature-card.md"
    if not feature_card.exists():
        blockers.append("finish requires feature-card.md")
    else:
        content = feature_card.read_text(encoding="utf-8")
        for heading in ("## Manual Validation", "## Verification Debt", "## Claim Provenance", "## Rollback Guidance", "## Shared Knowledge Updates"):
            if heading not in content:
                blockers.append(f"feature-card.md missing heading: {heading}")
        if ".ai/knowledge/" not in content:
            blockers.append("feature-card.md must describe shared knowledge updates using .ai/knowledge paths")
    stale = state.get("stale") or {}
    if stale.get("feature_card"):
        blockers.append("finish blocked by stale feature_card")
    if stale.get("canonical_docs"):
        blockers.append("finish blocked by stale canonical_docs")
    if (state.get("gates") or {}).get("verification") != "complete":
        blockers.append("finish requires verification gate complete")
    blockers.extend(validate_all_slices_complete(workspace))
    blockers.extend(validate_evidence_minimum(workspace))
    blockers.extend(validate_review_minimum(workspace))
    verification_review = workspace / "reviews/verification-review.md"
    if not verification_review.exists():
        blockers.append("finish requires reviews/verification-review.md")
    return blockers


def validate_all_slices_complete(workspace: Path) -> list[str]:
    slices_path = workspace / "slices.yaml"
    if not slices_path.exists():
        return ["finish requires slices.yaml"]
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
        if item.get("status") != "complete":
            blockers.append(f"finish requires slice complete: {item.get('id')}")
    return blockers


def validate_finish_state(workspace: Path) -> list[str]:
    blockers: list[str] = []
    state = read_yaml(workspace / "state.yaml")
    blockers.extend(validate_finish_if_started(workspace, state))
    if (state.get("gates") or {}).get("finish") != "complete":
        blockers.append("promotion requires finish gate complete")
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
        yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=False, default_flow_style=False, width=100)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        write_text(path, content)


def append_execution_event(workspace: Path, section: str, line: str) -> None:
    path = workspace / "execution.md"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    event_line = normalize_execution_event_line(section, line)
    if "## Event Log" not in existing:
        insert_at = existing.find("\n## History")
        event_section = "\n\n## Event Log\n\n"
        if insert_at == -1:
            existing = existing.rstrip() + event_section
        else:
            existing = existing[:insert_at].rstrip() + event_section + existing[insert_at:]
    event_match = re.search(r"^## Event Log\s*$", existing, flags=re.MULTILINE)
    if not event_match:
        write_text(path, existing.rstrip() + "\n" + event_line + "\n")
        return
    after_heading = existing[event_match.end() :]
    next_heading = re.search(r"\n##\s+", after_heading)
    if next_heading:
        insert_at = event_match.end() + next_heading.start()
        updated = existing[:insert_at].rstrip() + "\n" + event_line + "\n" + existing[insert_at:]
    else:
        updated = existing.rstrip() + "\n" + event_line + "\n"
    path.write_text(updated, encoding="utf-8")


def normalize_execution_event_line(section: str, line: str) -> str:
    stripped = line.strip()
    if stripped.startswith("- "):
        return stripped
    return f"- {utc_now()} event_type={slugify_event_value(section)} detail={slugify_event_value(stripped)}"


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


def validate_slice_evidence(workspace: Path, slice_id: str, manifest: dict[str, Any] | None = None) -> list[str]:
    manifest_path = workspace / "evidence/manifest.yaml"
    if manifest is None and not manifest_path.exists():
        return ["missing evidence/manifest.yaml"]
    if manifest is None:
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
    if "commit" not in slice_entry and "diff_hash" not in slice_entry and "change_label" not in slice_entry:
        blockers.append(f"{slice_id} missing commit, diff_hash, or change_label")
    if "diff_hash" in slice_entry and not is_hex_hash(str(slice_entry["diff_hash"])):
        blockers.append(f"{slice_id} diff_hash must be a hexadecimal hash; use change_label for semantic labels")
    for retry in slice_entry.get("retries") or []:
        if isinstance(retry, dict) and "diff_hash" in retry and not is_hex_hash(str(retry["diff_hash"])):
            blockers.append(f"{slice_id} retry diff_hash must be a hexadecimal hash; use change_label for semantic labels")
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


def slice_completion_status(path: Path, slice_id: str) -> str | None:
    data = read_yaml(path)
    slices = data.get("slices")
    if isinstance(slices, dict):
        items = slices.values()
    else:
        items = slices or []
    for item in items:
        if isinstance(item, dict) and item.get("id") == slice_id:
            return item.get("status")
    raise FeatureCtlError(f"slices.yaml has no slice {slice_id}")


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


def next_slice_attempt(manifest: dict[str, Any], slice_id: str) -> int:
    entry = manifest.setdefault("slices", {}).setdefault(slice_id, {})
    return 2 + len(entry.get("retries") or [])


def add_slice_commit_metadata(
    manifest: dict[str, Any],
    slice_id: str,
    *,
    commit: str | None,
    diff_hash: str | None,
    retry: bool = False,
    retry_reason: str | None = None,
    attempt: int = 1,
) -> None:
    entry = manifest.setdefault("slices", {}).setdefault(slice_id, {})
    metadata = slice_completion_metadata(commit=commit, diff_hash=diff_hash)
    if not retry:
        entry.update(metadata)
    if retry:
        retries = entry.setdefault("retries", [])
        retry_entry = {
            "timestamp": utc_now(),
            "attempt": attempt,
            "reason": retry_reason,
        }
        retry_entry.update(metadata)
        retries.append(retry_entry)


def slice_completion_metadata(*, commit: str | None, diff_hash: str | None) -> dict[str, str]:
    metadata: dict[str, str] = {}
    if commit:
        metadata["commit"] = commit
    if diff_hash:
        if is_hex_hash(diff_hash):
            metadata["diff_hash"] = diff_hash
        else:
            metadata["change_label"] = diff_hash
    return metadata


def is_hex_hash(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{6,64}", value.strip()))


def render_slice_completion_event(slice_id: str, *, retry: bool, attempt: int, reason: str | None) -> str:
    timestamp = utc_now()
    if retry:
        reason_value = slugify_event_value(reason or "unspecified")
        supersedes = max(1, attempt - 1)
        return (
            f"- {timestamp} event_type=slice_retry_completed slice={slice_id} "
            f"attempt={attempt} reason={reason_value} supersedes=attempt-{supersedes}"
        )
    return f"- {timestamp} event_type=slice_completed slice={slice_id} attempt=1 reason=initial"


def slugify_event_value(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-") or "unspecified"


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


def infer_worktree_path(workspace: Path) -> Path:
    resolved = workspace.resolve()
    parts = resolved.parts
    for index in range(len(parts) - 1, -1, -1):
        if parts[index] == ".ai":
            return Path(*parts[:index]).resolve()
    raise FeatureCtlError(f"workspace is not inside a .ai directory: {workspace}")


def resolve_configured_worktree_path(root: Path, worktree_value: str) -> Path:
    configured = Path(worktree_value)
    if configured.is_absolute():
        return configured.resolve()
    return (root / configured).resolve()


def regenerate_feature_index(root: Path) -> None:
    features: list[dict[str, Any]] = []
    features_root = root / ".ai/features"
    for feature_yaml in sorted(features_root.glob("*/*/feature.yaml")):
        feature = read_yaml(feature_yaml)
        rel_path = feature_yaml.parent.relative_to(root).as_posix()
        features.append(
            {
                "feature_key": feature.get("feature_key"),
                "title": feature.get("title"),
                "status": feature.get("status"),
                "path": rel_path,
                "run_id": feature.get("run_id"),
            }
        )
    write_yaml(
        root / ".ai/features/index.yaml",
        {
            "artifact_contract_version": CONTRACT_VERSION,
            "features": features,
        },
    )
    write_text(root / ".ai/features/overview.md", render_feature_memory_overview(features))


def render_feature_memory_overview(features: list[dict[str, Any]]) -> str:
    lines = [
        "# Feature Overview",
        "",
        "Status: generated",
        f"Generated at: {utc_now()}",
        "",
        "## Canonical Features",
        "",
    ]
    if not features:
        lines.append("No canonical features have been promoted yet.")
    else:
        for feature in features:
            lines.append(
                f"- `{feature.get('feature_key')}` ({feature.get('status') or 'unknown'}) from `{feature.get('path')}`; run `{feature.get('run_id')}`"
            )
    lines.append("")
    return "\n".join(lines)


def update_feature_status(
    workspace: Path,
    status: str,
    *,
    current_step: str | None = None,
    lifecycle: str | None = None,
    read_only: bool | None = None,
) -> None:
    feature_path = workspace / "feature.yaml"
    state_path = workspace / "state.yaml"
    if feature_path.exists():
        feature = read_yaml(feature_path)
        feature["status"] = status
        feature["updated_at"] = utc_now()
        write_yaml(feature_path, feature)
    if state_path.exists() and current_step:
        state = read_yaml(state_path)
        state["current_step"] = current_step
        if lifecycle is not None:
            state["lifecycle"] = lifecycle
        if read_only is not None:
            state["read_only"] = read_only
        state.setdefault("stale", {})["index"] = False
        if current_step == "promote":
            state.setdefault("stale", {})["canonical_docs"] = False
        write_yaml(state_path, state)
        write_latest_status(workspace, current_step)


def write_latest_status(workspace: Path, current_step: str) -> None:
    execution_path = workspace / "execution.md"
    if not execution_path.exists():
        return
    execution = execution_path.read_text(encoding="utf-8")
    current_state = (
        "## Current Run State\n\n"
        f"Current step: {current_step}\n"
        f"Next recommended skill: {next_skill_for_step(current_step)}\n"
        "Blocking issues: none\n"
        f"Last updated: {utc_now()}\n"
    )
    execution = remove_markdown_section_by_heading(execution, "Current Run State")
    execution = remove_markdown_section_by_heading(execution, "Latest Status")
    write_text(execution_path, execution.rstrip() + "\n\n" + current_state)


def remove_markdown_section_by_heading(markdown: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$", markdown, flags=re.MULTILINE)
    if not match:
        return markdown
    rest = markdown[match.end() :]
    next_heading = re.search(r"\n##\s+", rest)
    suffix = rest[next_heading.start() :] if next_heading else ""
    return (markdown[: match.start()].rstrip() + "\n\n" + suffix.lstrip()).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
