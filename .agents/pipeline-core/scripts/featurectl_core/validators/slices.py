"""Slice-plan validators."""

from __future__ import annotations

import re
from pathlib import Path

from ..formatting import read_yaml
from ..shared import CONTRACT_VERSION, FeatureCtlError


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
        validate_slice_identity(blockers, item, prefix, seen_ids)
        validate_slice_required_fields(blockers, item, prefix)
        validate_slice_links(blockers, item, prefix, feature_ids)
        validate_slice_types(blockers, item, prefix)
        validate_slice_dependencies(blockers, item, prefix, all_ids)
        validate_slice_tdd(blockers, item, prefix)
    return blockers


def validate_slice_identity(blockers: list[str], item: dict, prefix: str, seen_ids: set[str]) -> None:
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


def validate_slice_required_fields(blockers: list[str], item: dict, prefix: str) -> None:
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


def validate_slice_links(blockers: list[str], item: dict, prefix: str, feature_ids: dict[str, set[str]]) -> None:
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


def validate_slice_types(blockers: list[str], item: dict, prefix: str) -> None:
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
    if not item.get("verification_commands"):
        blockers.append(f"{prefix} must include verification_commands")
    if not isinstance(item.get("iteration_budget"), int) or item.get("iteration_budget", 0) < 1:
        blockers.append(f"{prefix} iteration_budget must be a positive integer")
    for field in ("rollback_point", "independent_verification", "failure_triage_notes"):
        if field in item and not str(item.get(field) or "").strip():
            blockers.append(f"{prefix} {field} must not be empty")


def validate_slice_dependencies(blockers: list[str], item: dict, prefix: str, all_ids: set) -> None:
    for dependency in item.get("dependencies") or []:
        if dependency not in all_ids:
            blockers.append(f"{prefix} depends on unknown slice {dependency}")


def validate_slice_tdd(blockers: list[str], item: dict, prefix: str) -> None:
    tdd = item.get("tdd")
    if not isinstance(tdd, dict):
        blockers.append(f"{prefix} missing tdd mapping")
    else:
        for field in ("failing_test_file", "red_command", "expected_failure", "green_command"):
            if not tdd.get(field):
                blockers.append(f"{prefix} tdd missing {field}")


def extract_feature_ids(feature_path: Path) -> dict[str, set[str]]:
    if not feature_path.exists():
        return {"FR": set(), "AC": set()}
    content = feature_path.read_text(encoding="utf-8")
    return {
        "FR": set(re.findall(r"\bFR-[0-9]{3}\b", content)),
        "AC": set(re.findall(r"\bAC-[0-9]{3}\b", content)),
    }
