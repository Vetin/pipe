"""Evidence manifest and slice completion helpers for featurectl."""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Any

from .formatting import read_yaml, write_yaml
from .promotion import infer_worktree_path, resolve_configured_worktree_path
from .shared import CONTRACT_VERSION, FeatureCtlError, run_git, utc_now

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
            "completion_identity_policy": completion_identity_policy(),
            "slices": {},
        }
    manifest.setdefault("artifact_contract_version", CONTRACT_VERSION)
    manifest.setdefault("feature_key", feature_key)
    manifest.setdefault("completion_identity_policy", completion_identity_policy())
    manifest.setdefault("slices", {})
    return manifest


def completion_identity_policy() -> dict[str, str]:
    return {
        "diff_hash": "hexadecimal git diff or commit-derived hash when available",
        "change_label": "semantic completion label when a real diff hash is unavailable",
    }


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
    if manifest_has_change_label_without_diff_hash(slices):
        if "completion_identity_policy" not in manifest:
            blockers.append("evidence manifest change_label entries require completion_identity_policy")
    known_slices = known_slice_ids(workspace)
    for slice_id in slices:
        if known_slices and slice_id not in known_slices:
            blockers.append(f"evidence manifest references unknown slice: {slice_id}")
        blockers.extend(validate_slice_evidence(workspace, slice_id))
    blockers.extend(validate_completed_slices_have_manifest(workspace, slices))
    return blockers


def manifest_has_change_label_without_diff_hash(slices: dict[str, Any]) -> bool:
    for entry in slices.values():
        if isinstance(entry, dict) and "change_label" in entry and "diff_hash" not in entry:
            return True
        for retry in (entry or {}).get("retries") or [] if isinstance(entry, dict) else []:
            if isinstance(retry, dict) and "change_label" in retry and "diff_hash" not in retry:
                return True
    return False


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
