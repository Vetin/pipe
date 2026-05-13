"""Workspace and artifact validation helpers for featurectl."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .docsets import normalize_step_name
from .evidence import validate_evidence_manifest, validate_slice_evidence
from .formatting import read_yaml
from .promotion import infer_worktree_path, resolve_configured_worktree_path
from .shared import (
    CONTRACT_VERSION,
    DEFAULT_GATES,
    DEFAULT_STALE,
    FEATURE_REQUIRED_HEADINGS,
    INACTIVE_WORKSPACE_LIFECYCLES,
    TECH_DESIGN_REQUIRED_HEADINGS,
    VALID_GATE_STATES,
    VALID_STEPS,
    VALID_WORKSPACE_LIFECYCLES,
    FeatureCtlError,
    repo_root,
    run_git,
)

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
