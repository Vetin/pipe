"""Review artifact validation helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..formatting import read_yaml
from ..shared import CONTRACT_VERSION


def validate_review_minimum(workspace: Path) -> list[str]:
    blockers: list[str] = []
    review_files = sorted(workspace.glob("reviews/*.yaml"))
    if not review_files:
        return ["review validation requires at least one reviews/*.yaml file"]
    for review_file in review_files:
        review = read_yaml(review_file)
        blockers.extend(validate_review_file(review_file, review, workspace))
        if review.get("blocking") is True and review.get("severity") == "critical":
            blockers.append(
                f"critical review finding blocks verification: {review_file.relative_to(workspace)}"
            )
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
