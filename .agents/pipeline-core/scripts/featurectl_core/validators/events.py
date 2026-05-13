"""events.yaml sidecar validators."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..formatting import read_yaml
from ..shared import CONTRACT_VERSION, FeatureCtlError

TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
BASE_EVENT_FIELDS = {"timestamp", "event_type", "feature_key"}
EVENT_FIELDS = {
    "run_initialized": {"step", "next"},
    "gate_status_changed": {"gate", "old_status", "new_status", "by", "note"},
    "slice_completed": {"slice", "attempt", "reason"},
    "slice_retry_completed": {"slice", "attempt", "reason", "supersedes"},
    "feature_promoted": {"canonical_path"},
    "incoming_variant_archived": {"canonical_path"},
    "artifact_marked_stale": {"artifact", "marked_stale", "reason"},
    "public_raw_verified": {"wrappers", "gitignore", "index_lines", "clone_formatting_tests"},
    "verification_completed": {"result", "command"},
    "review_completed": {"review_id", "result"},
}
REQUIRED_BY_TYPE = {
    "run_initialized": ("step", "next"),
    "gate_status_changed": ("gate", "old_status", "new_status"),
    "slice_completed": ("slice", "attempt", "reason"),
    "slice_retry_completed": ("slice", "attempt", "reason", "supersedes"),
    "feature_promoted": ("canonical_path",),
    "incoming_variant_archived": ("canonical_path",),
    "artifact_marked_stale": ("artifact", "marked_stale"),
    "public_raw_verified": ("wrappers", "gitignore", "index_lines", "clone_formatting_tests"),
    "verification_completed": ("result",),
    "review_completed": ("review_id", "result"),
}


def validate_events_sidecar(workspace: Path, feature: dict[str, Any]) -> list[str]:
    events_path = workspace / "events.yaml"
    if not events_path.exists():
        return []
    try:
        data = read_yaml(events_path)
    except FeatureCtlError as exc:
        return [str(exc)]

    blockers: list[str] = []
    expected_feature_key = str(feature.get("feature_key") or "")
    if data.get("artifact_contract_version") != CONTRACT_VERSION:
        blockers.append("events.yaml artifact_contract_version mismatch")
    if data.get("feature_key") != expected_feature_key:
        blockers.append("events.yaml feature_key mismatch")
    events = data.get("events")
    if not isinstance(events, list):
        return [*blockers, "events.yaml events must be a list"]
    for index, event in enumerate(events, start=1):
        blockers.extend(validate_event_record(index, event, expected_feature_key))
    return blockers


def validate_event_record(index: int, event: Any, expected_feature_key: str) -> list[str]:
    prefix = f"events.yaml event {index}"
    if not isinstance(event, dict):
        return [f"{prefix} must be a mapping"]
    blockers: list[str] = []
    for field in ("timestamp", "event_type", "feature_key"):
        if field not in event:
            blockers.append(f"{prefix} missing {field}")
    timestamp = event.get("timestamp")
    if "timestamp" in event and (not isinstance(timestamp, str) or not TIMESTAMP_PATTERN.match(timestamp)):
        blockers.append(f"{prefix} timestamp must be an RFC3339 UTC timestamp ending in Z")
    if event.get("feature_key") != expected_feature_key:
        blockers.append(f"{prefix} feature_key mismatch")
    event_type = event.get("event_type")
    if event_type not in EVENT_FIELDS:
        blockers.append(f"{prefix} has unknown event_type {event_type}")
        return blockers
    allowed_fields = BASE_EVENT_FIELDS | EVENT_FIELDS[str(event_type)]
    for field in event:
        if field not in allowed_fields:
            blockers.append(f"{prefix} has unexpected field {field}")
    for field in REQUIRED_BY_TYPE.get(str(event_type), ()):
        if field not in event:
            blockers.append(f"{prefix} {event_type} missing {field}")
    if event_type in {"slice_completed", "slice_retry_completed"}:
        slice_id = event.get("slice")
        if not isinstance(slice_id, str) or not re.match(r"^S-[0-9]{3}$", slice_id):
            blockers.append(f"{prefix} {event_type} slice must match S-000")
        attempt = event.get("attempt")
        if not isinstance(attempt, int) or attempt < (2 if event_type == "slice_retry_completed" else 1):
            blockers.append(f"{prefix} {event_type} attempt is invalid")
    if event_type == "artifact_marked_stale" and "marked_stale" in event and not isinstance(event.get("marked_stale"), list):
        blockers.append(f"{prefix} artifact_marked_stale marked_stale must be a list")
    return blockers
