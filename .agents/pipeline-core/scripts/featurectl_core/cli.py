#!/usr/bin/env python3
"""Command parser and dispatch for the Native Feature Pipeline control plane."""

from __future__ import annotations

import argparse
import copy
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from .docsets import load_docset, missing_docs, next_skill_for_step, normalize_step_name, print_docs
from .events import (
    append_execution_event,
    append_run_plan_update,
    initialize_events_sidecar,
    render_execution_event,
    rewrite_execution_event_summary,
)
from .evidence import (
    add_slice_commit_metadata,
    current_git_state,
    ensure_known_slice,
    evidence_phase_files,
    next_slice_attempt,
    read_manifest_or_default,
    render_slice_completion_event,
    mark_slice_complete,
    slice_completion_status,
    staleness_targets,
    validate_slice_evidence,
    validate_timestamp,
)
from .formatting import read_yaml, write_text, write_yaml, write_if_missing
from .profile import (
    build_project_profile,
    ensure_init_tree,
    render_apex,
    render_execution,
    sync_knowledge_canonical_features,
    write_project_profile,
)
from .promotion import infer_worktree_path, regenerate_feature_index, update_feature_status, write_latest_status
from .shared import (
    CONTRACT_VERSION,
    DEFAULT_GATES,
    DEFAULT_STALE,
    FeatureCtlError,
    VALID_GATE_STATES,
    VALID_STEPS,
    generate_run_id,
    git_branch_exists,
    normalize_domain,
    repo_root,
    resolve_workspace,
    run_git,
    slugify,
    utc_now,
)
from .validation import (
    status_blockers,
    validate_all_slices_complete,
    validate_architecture_if_started,
    validate_current_directory_is_worktree,
    validate_evidence_minimum,
    validate_feature_contract_if_started,
    validate_finish_if_started,
    validate_finish_state,
    validate_implementation_minimum,
    validate_planning_package,
    validate_slices_if_started,
    validate_tech_design_if_started,
    validate_verification_if_started,
    validate_workspace,
)
from .validators.review import validate_review_minimum

SATISFIED_GATE_STATES = {"approved", "delegated", "complete"}
PLANNING_GATES = ("feature_contract", "architecture", "tech_design", "slicing_readiness")
DELIVERY_GATES = ("implementation", "review", "verification", "finish")
DELIVERY_GATES_REQUIRING_COMPLETION = {"review", "verification", "finish"}

STEP_TRANSITIONS = {
    "intake": {"context"},
    "context": {"feature_contract"},
    "feature_contract": {"architecture"},
    "architecture": {"tech_design"},
    "tech_design": {"slicing"},
    "slicing": {"readiness"},
    "readiness": {"worktree"},
    "worktree": {"tdd_implementation"},
    "tdd_implementation": {"review"},
    "review": {"verification", "tdd_implementation"},
    "verification": {"finish", "tdd_implementation"},
    "finish": set(),
}

GATE_DEPENDENCIES = {
    "architecture": ("feature_contract",),
    "tech_design": ("architecture",),
    "slicing_readiness": ("tech_design",),
    "implementation": ("slicing_readiness",),
    "review": ("implementation",),
    "verification": ("review",),
    "finish": ("verification",),
}

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
    new_parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="allow creating a feature worktree from a dirty base checkout after inspection",
    )
    new_parser.add_argument(
        "--allow-bootstrap-dirty",
        action="store_true",
        help="allow only first-install generated pipeline files in an otherwise dirty base checkout",
    )
    new_parser.set_defaults(func=cmd_new)

    status_parser = subparsers.add_parser("status", help="print workspace status")
    status_parser.add_argument("--workspace")
    status_parser.set_defaults(func=cmd_status)

    validate_parser = subparsers.add_parser("validate", help="validate pipeline workspace")
    validate_parser.add_argument("--workspace", required=True)
    validate_parser.add_argument("--planning-package", action="store_true")
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

    step_parser = subparsers.add_parser("step", help="manage current pipeline step")
    step_subparsers = step_parser.add_subparsers(dest="step_command", required=True)
    step_set_parser = step_subparsers.add_parser("set", help="set the current pipeline step")
    step_set_parser.add_argument("--workspace", required=True)
    step_set_parser.add_argument("--step", required=True)
    step_set_parser.add_argument("--by", dest="actor", required=True)
    step_set_parser.add_argument("--note", default="")
    step_set_parser.set_defaults(func=cmd_step_set)

    scope_change_parser = subparsers.add_parser("scope-change", help="record a scope change and return to an earlier step")
    scope_change_parser.add_argument("--workspace", required=True)
    scope_change_parser.add_argument("--reason", required=True)
    scope_change_parser.add_argument("--return-step", required=True)
    scope_change_parser.add_argument("--stale", action="append", default=[])
    scope_change_parser.add_argument("--by", dest="actor", required=True)
    scope_change_parser.set_defaults(func=cmd_scope_change)

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

    worktree_status_parser = subparsers.add_parser(
        "worktree-status",
        help="verify workspace core files and feature worktree isolation",
    )
    worktree_status_parser.add_argument("--workspace")
    worktree_status_parser.set_defaults(func=cmd_worktree_status)

    implementation_ready_parser = subparsers.add_parser(
        "implementation-ready",
        help="verify implementation may start from the configured feature worktree",
    )
    implementation_ready_parser.add_argument("--workspace")
    implementation_ready_parser.set_defaults(func=cmd_implementation_ready)

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
    if not args.allow_dirty:
        require_clean_base_checkout(root, allow_bootstrap_dirty=args.allow_bootstrap_dirty)

    ensure_init_tree(root)

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
    initialize_events_sidecar(workspace_path)

    print(f"feature_key: {feature_key}")
    print(f"branch: {branch}")
    print(f"worktree: {worktree_value}")
    print(f"workspace: {workspace_value}")
    print("next_step: nfp-01-context")


def require_clean_base_checkout(root: Path, *, allow_bootstrap_dirty: bool = False) -> None:
    status = run_git(root, "status", "--short", "--untracked-files=normal").strip()
    pipeline_committed = pipeline_already_committed(root)
    blockers = [
        line
        for line in status.splitlines()
        if not (
            allow_bootstrap_dirty
            and generated_pipeline_bootstrap_dirty(line, allow_broad_bootstrap=not pipeline_committed)
        )
    ]
    if blockers:
        suggested_flag = (
            "--allow-bootstrap-dirty"
            if not pipeline_committed and all(generated_pipeline_bootstrap_dirty(line, allow_broad_bootstrap=True) for line in blockers)
            else "--allow-dirty"
        )
        raise FeatureCtlError(
            "base checkout has uncommitted changes; inspect them before creating "
            f"a feature worktree or rerun with {suggested_flag}"
        )


def pipeline_already_committed(root: Path) -> bool:
    tracked = run_git(
        root,
        "ls-files",
        "AGENTS.md",
        ".agents",
        "skills",
    ).strip()
    return bool(tracked)


def generated_pipeline_bootstrap_dirty(status_line: str, *, allow_broad_bootstrap: bool = True) -> bool:
    if not status_line:
        return True
    status_code = status_line[:2]
    path = status_line[3:]
    if " -> " in path:
        path = path.rsplit(" -> ", 1)[-1]
    if status_code == "??" and path in {".agents/", ".ai/", "skills/", "methodology/"}:
        return allow_broad_bootstrap
    if status_code == "??" and path == ".gitignore":
        return True
    if status_code == "??" and path.startswith((".agents/", ".ai/", "skills/", "methodology/")):
        return allow_broad_bootstrap
    if path.startswith(".ai/knowledge/"):
        return True
    if path in {".ai/features/index.yaml", ".ai/features/overview.md"}:
        return True
    return False


def cmd_status(args: argparse.Namespace) -> None:
    root = repo_root()
    workspace = resolve_workspace(root, args.workspace)
    feature = read_yaml(workspace / "feature.yaml")
    state = read_yaml(workspace / "state.yaml")
    blockers = status_blockers(root, workspace, feature, state)

    print(f"feature_key: {feature.get('feature_key')}")
    print(f"worktree: {state.get('worktree', {}).get('path')}")
    print(f"current_step: {state.get('current_step')}")
    gates = state.get("gates", {})
    print("planning_gates:")
    for gate in PLANNING_GATES:
        status = gates.get(gate, "missing")
        print(f"  {gate}: {status}")
    print("delivery_gates:")
    for gate in DELIVERY_GATES:
        status = gates.get(gate, "missing")
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
        planning_package=args.planning_package,
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


def normalize_state_step(step: str) -> str:
    normalized = step.strip().lower().replace("-", "_")
    if normalized not in VALID_STEPS:
        raise FeatureCtlError(f"invalid step: {step}")
    if normalized == "promote":
        raise FeatureCtlError("promote step is managed by featurectl.py promote")
    return normalized


def validate_step_transition(old_step: str | None, new_step: str) -> None:
    if not old_step or old_step == new_step:
        return
    allowed = STEP_TRANSITIONS.get(old_step, set())
    if new_step not in allowed:
        raise FeatureCtlError(
            f"illegal step transition: {old_step} -> {new_step}; "
            "use scope-change for backward replanning"
        )


def cmd_step_set(args: argparse.Namespace) -> None:
    root = repo_root()
    workspace = resolve_workspace(root, args.workspace)
    state_path = workspace / "state.yaml"
    state = read_yaml(state_path)
    old_step = state.get("current_step")
    new_step = normalize_state_step(args.step)
    validate_step_transition(old_step, new_step)
    state["current_step"] = new_step
    write_yaml(state_path, state)
    append_execution_event(
        workspace,
        "Step Events",
        render_execution_event(
            "step_changed",
            old_step=old_step or "none",
            new_step=new_step,
            by=args.actor,
            note=args.note or "none",
        ),
    )
    write_latest_status(workspace, new_step)
    print(f"current_step: {new_step}")
    print(f"next_step: {next_skill_for_step(new_step)}")


def cmd_scope_change(args: argparse.Namespace) -> None:
    root = repo_root()
    workspace = resolve_workspace(root, args.workspace)
    state_path = workspace / "state.yaml"
    state = read_yaml(state_path)
    return_step = normalize_state_step(args.return_step)
    stale = state.setdefault("stale", {})
    stale_artifacts = resolve_scope_stale_artifacts(args.stale, stale)
    for artifact in stale_artifacts:
        stale[artifact] = True
    old_step = state.get("current_step")
    state["current_step"] = return_step
    write_yaml(state_path, state)
    append_scope_change(workspace, args.reason, return_step, stale_artifacts, args.actor)
    append_execution_event(
        workspace,
        "Scope Changes",
        render_execution_event(
            "scope_changed",
            old_step=old_step or "none",
            return_step=return_step,
            stale=stale_artifacts,
            by=args.actor,
            reason=args.reason,
        ),
    )
    write_latest_status(workspace, return_step)
    print("scope_change: recorded")
    print(f"return_step: {return_step}")
    print("stale:")
    for artifact in stale_artifacts:
        print(f"  - {artifact}")


def resolve_scope_stale_artifacts(requested: list[str], stale: dict[str, Any]) -> list[str]:
    if not requested:
        raise FeatureCtlError("scope-change requires at least one --stale artifact")
    resolved: list[str] = []
    for artifact in requested:
        normalized = artifact.strip().replace("-", "_")
        if normalized in stale:
            targets = [normalized]
        else:
            targets = staleness_targets(artifact)
        if not targets:
            raise FeatureCtlError(f"unknown artifact for scope-change staleness: {artifact}")
        for target in targets:
            if target not in resolved:
                resolved.append(target)
    return resolved


def append_scope_change(
    workspace: Path,
    reason: str,
    return_step: str,
    stale_artifacts: list[str],
    actor: str,
) -> None:
    path = workspace / "scope-change.md"
    entry = (
        f"## Scope Change: {utc_now()}\n\n"
        f"- Actor: {actor}\n"
        f"- Return step: {return_step}\n"
        f"- Reason: {reason}\n"
        "- Stale artifacts:\n"
        + "\n".join(f"  - {artifact}" for artifact in stale_artifacts)
        + "\n"
    )
    if path.exists():
        write_text(path, path.read_text(encoding="utf-8").rstrip() + "\n\n" + entry)
    else:
        write_text(path, "# Scope Change Log\n\n" + entry)


def cmd_gate_set(args: argparse.Namespace) -> None:
    root = repo_root()
    workspace = resolve_workspace(root, args.workspace)
    if args.gate not in DEFAULT_GATES:
        raise FeatureCtlError(f"unknown gate: {args.gate}")
    if args.status not in VALID_GATE_STATES:
        raise FeatureCtlError(f"invalid gate status: {args.status}")
    state_path = workspace / "state.yaml"
    state = read_yaml(state_path)
    gate_blockers = gate_dependency_blockers(workspace, state, args.gate, args.status)
    gate_blockers.extend(gate_content_blockers(workspace, state, args.gate, args.status))
    if gate_blockers:
        for blocker in gate_blockers:
            print(f"- {blocker}")
        raise FeatureCtlError("gate validation failed")
    old_status = state.setdefault("gates", {}).get(args.gate)
    state["gates"][args.gate] = args.status
    write_yaml(state_path, state)
    append_execution_event(
        workspace,
        "Gate Events",
        render_execution_event(
            "gate_status_changed",
            gate=args.gate,
            old_status=old_status,
            new_status=args.status,
            by=args.actor,
            note=args.note or "none",
        ),
    )
    append_run_plan_update(
        workspace,
        gate=args.gate,
        old_status=old_status,
        new_status=args.status,
        reason=args.note,
    )
    print(f"gate: {args.gate}")
    print(f"status: {args.status}")


def gate_dependency_blockers(workspace: Path, state: dict[str, Any], gate: str, status: str) -> list[str]:
    if status not in SATISFIED_GATE_STATES:
        return []
    gates = state.get("gates") or {}
    blockers: list[str] = []
    for dependency in GATE_DEPENDENCIES.get(gate, ()):
        required_states = required_dependency_states(gate, status)
        dependency_status = gates.get(dependency)
        if dependency_status not in required_states:
            blockers.append(f"{gate} requires {dependency} gate {required_dependency_label(required_states)}")
    return blockers


def required_dependency_states(gate: str, status: str) -> set[str]:
    if gate in DELIVERY_GATES_REQUIRING_COMPLETION and status in SATISFIED_GATE_STATES:
        return {"complete"}
    return set(SATISFIED_GATE_STATES)


def required_dependency_label(states: set[str]) -> str:
    if states == {"complete"}:
        return "complete"
    return "approved or delegated"


def gate_content_blockers(workspace: Path, state: dict[str, Any], gate: str, status: str) -> list[str]:
    if status not in SATISFIED_GATE_STATES:
        return []
    draft_state = copy.deepcopy(state)
    draft_state.setdefault("gates", {})[gate] = "drafted"
    if gate == "feature_contract":
        return validate_feature_contract_if_started(workspace, draft_state)
    if gate == "architecture":
        return validate_architecture_if_started(workspace, draft_state)
    if gate == "tech_design":
        return validate_tech_design_if_started(workspace, draft_state)
    if gate == "slicing_readiness":
        return validate_slices_if_started(workspace, draft_state)
    if gate == "implementation" and status == "complete":
        return validate_all_slices_complete(workspace, reason="implementation") + validate_evidence_minimum(workspace)
    if gate == "review" and status == "complete":
        return validate_review_minimum(workspace)
    if gate == "verification" and status == "complete":
        return validate_verification_if_started(workspace, draft_state)
    if gate == "finish" and status == "complete":
        return validate_finish_if_started(workspace, draft_state)
    return []


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
        render_execution_event(
            "artifact_marked_stale",
            artifact=args.artifact,
            marked_stale=affected,
            reason=args.reason or "none",
        ),
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
    print("implementation_ready: not_checked")
    print("blocking_issues:")
    if blockers:
        for blocker in blockers:
            print(f"  - {blocker}")
        raise FeatureCtlError("worktree status failed")
    print("  none")


def cmd_implementation_ready(args: argparse.Namespace) -> None:
    root = repo_root()
    workspace = resolve_workspace(root, args.workspace)
    feature = read_yaml(workspace / "feature.yaml")
    state = read_yaml(workspace / "state.yaml")
    worktree_path = infer_worktree_path(workspace)
    blockers = []
    blockers.extend(status_blockers(root, workspace, feature, state))
    blockers.extend(validate_planning_package(workspace, state))
    blockers.extend(validate_implementation_minimum(state))
    blockers.extend(validate_current_directory_is_worktree(workspace))

    print("implementation_ready: " + ("false" if blockers else "true"))
    print(f"feature_key: {feature.get('feature_key')}")
    print(f"worktree: {worktree_path}")
    print(f"current_checkout: {repo_root()}")
    try:
        print(f"branch: {run_git(worktree_path, 'rev-parse', '--abbrev-ref', 'HEAD').strip()}")
    except FeatureCtlError as exc:
        blockers.append(str(exc))
        print("branch: unknown")
    print("blocking_issues:")
    if blockers:
        for blocker in blockers:
            print(f"  - {blocker}")
        raise FeatureCtlError("implementation readiness failed")
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
        append_execution_event(
            archive,
            "Summary",
            render_execution_event("incoming_variant_archived", canonical_path=feature["canonical_path"]),
        )
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
    promoted_state.setdefault("gates", {})["implementation"] = "complete"
    promoted_state.setdefault("stale", {})["canonical_docs"] = False
    promoted_state.setdefault("stale", {})["index"] = False
    write_yaml(promoted_state_path, promoted_state)
    write_latest_status(canonical, "promote")

    update_feature_status(workspace, "promoted-readonly", current_step="promote", lifecycle="promoted-readonly", read_only=True)
    regenerate_feature_index(root)
    sync_knowledge_canonical_features(root)
    append_execution_event(
        canonical,
        "Summary",
        render_execution_event("feature_promoted", canonical_path=feature["canonical_path"]),
    )
    rewrite_execution_event_summary(canonical)
    print("promotion: complete")
    print(f"canonical_path: {feature['canonical_path']}")
