"""Workspace and artifact validation helpers for featurectl."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .docsets import normalize_step_name
from .evidence import validate_evidence_manifest, validate_slice_evidence
from .formatting import read_yaml
from .promotion import infer_worktree_path, resolve_configured_worktree_path
from .shared import (
    FEATURE_REQUIRED_HEADINGS,
    TECH_DESIGN_REQUIRED_HEADINGS,
    VALID_STEPS,
    FeatureCtlError,
    run_git,
)
from .validators.canonical_memory import validate_repository_source_truth, workspace_inactive_lifecycle
from .validators.events import validate_events_sidecar
from .validators.execution_log import validate_execution_latest_status
from .validators.gates import validate_state_shape
from .validators.review import validate_review_minimum
from .validators.slices import validate_slices_file
from .validators.worktree import validate_current_directory_is_worktree

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
    planning_package: bool = False,
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
    blockers.extend(validate_events_sidecar(workspace, feature))
    blockers.extend(validate_repository_source_truth(root, workspace, feature, state))

    if planning_package:
        blockers.extend(validate_planning_package(workspace, state))
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


def validate_planning_package(workspace: Path, state: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    for artifact in ("feature.md", "architecture.md", "tech-design.md", "slices.yaml"):
        if not (workspace / artifact).exists():
            blockers.append(f"planning-package requires {artifact}")

    planning_state = dict(state)
    planning_state["gates"] = {
        "feature_contract": "drafted",
        "architecture": "drafted",
        "tech_design": "drafted",
        "slicing_readiness": "drafted",
    }
    if (workspace / "feature.md").exists():
        blockers.extend(validate_feature_contract_if_started(workspace, planning_state))
    if (workspace / "architecture.md").exists():
        blockers.extend(validate_architecture_if_started(workspace, planning_state))
    if (workspace / "tech-design.md").exists():
        blockers.extend(validate_tech_design_if_started(workspace, planning_state))
    if (workspace / "slices.yaml").exists():
        blockers.extend(validate_slices_if_started(workspace, planning_state))

    for artifact in ("feature", "architecture", "tech_design", "slices"):
        if (state.get("stale") or {}).get(artifact):
            blockers.append(f"planning-package blocked by stale {artifact}")
    return blockers


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
