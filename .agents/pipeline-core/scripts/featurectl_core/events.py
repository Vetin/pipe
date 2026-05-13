"""Execution event rendering and sidecar synchronization for featurectl."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .formatting import read_yaml, write_text, write_yaml
from .shared import CONTRACT_VERSION, utc_now

def append_execution_event(workspace: Path, section: str, line: str) -> None:
    path = workspace / "execution.md"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    event_line = normalize_execution_event_line(section, line)
    event = parse_execution_event_line(event_line)
    if event:
        append_events_sidecar_record(workspace, event)
    summary_line = summarize_event_record(event) if event else event_line
    if "## Event Log" not in existing:
        insert_at = existing.find("\n## History")
        event_section = "\n\n## Event Log\n\n"
        if insert_at == -1:
            existing = existing.rstrip() + event_section
        else:
            existing = existing[:insert_at].rstrip() + event_section + existing[insert_at:]
    event_match = re.search(r"^## Event Log\s*$", existing, flags=re.MULTILINE)
    if not event_match:
        write_text(path, existing.rstrip() + "\n" + summary_line + "\n")
        return
    after_heading = existing[event_match.end() :]
    next_heading = re.search(r"\n##\s+", after_heading)
    if next_heading:
        insert_at = event_match.end() + next_heading.start()
        updated = existing[:insert_at].rstrip() + "\n" + summary_line + "\n" + existing[insert_at:]
    else:
        updated = existing.rstrip() + "\n" + summary_line + "\n"
    path.write_text(updated, encoding="utf-8")


def initialize_events_sidecar(workspace: Path) -> None:
    execution_path = workspace / "execution.md"
    if not execution_path.exists():
        write_events_sidecar(workspace, [])
        return
    feature_key = feature_key_for_workspace(workspace)
    events = []
    for line in execution_path.read_text(encoding="utf-8").splitlines():
        event = parse_execution_event_line(line)
        if event:
            event.setdefault("feature_key", feature_key)
            events.append(event)
    if not events:
        events.append(
            {
                "timestamp": utc_now(),
                "event_type": "run_initialized",
                "feature_key": feature_key,
                "step": "context",
                "next": "nfp-01-context",
            }
        )
    write_events_sidecar(workspace, events)


def normalize_execution_event_line(section: str, line: str) -> str:
    stripped = line.strip()
    if stripped.startswith("- "):
        return stripped
    return f"- {utc_now()} event_type={slugify_event_value(section)} detail={slugify_event_value(stripped)}"


def slugify_event_value(value: Any) -> str:
    return format_event_value(value)


def render_execution_event(event_type: str, **fields: Any) -> str:
    parts = [f"- {utc_now()}", f"event_type={format_event_value(event_type)}"]
    for key, value in fields.items():
        parts.append(f"{key}={format_event_value(value)}")
    return " ".join(parts)


def append_events_sidecar(workspace: Path, line: str) -> None:
    event = parse_execution_event_line(line)
    if not event:
        return
    append_events_sidecar_record(workspace, event)


def append_events_sidecar_record(workspace: Path, event: dict[str, Any]) -> None:
    data = read_events_sidecar(workspace)
    event.setdefault("feature_key", data["feature_key"])
    data.setdefault("events", []).append(event)
    write_yaml(workspace / "events.yaml", data)


def read_events_sidecar(workspace: Path) -> dict[str, Any]:
    path = workspace / "events.yaml"
    if path.exists():
        data = read_yaml(path)
    else:
        data = {}
    data.setdefault("artifact_contract_version", CONTRACT_VERSION)
    data.setdefault("feature_key", feature_key_for_workspace(workspace))
    data.setdefault("events", [])
    return data


def write_events_sidecar(workspace: Path, events: list[dict[str, Any]]) -> None:
    write_yaml(
        workspace / "events.yaml",
        {
            "artifact_contract_version": CONTRACT_VERSION,
            "feature_key": feature_key_for_workspace(workspace),
            "events": events,
        },
    )


def feature_key_for_workspace(workspace: Path) -> str:
    feature_path = workspace / "feature.yaml"
    if feature_path.exists():
        return str(read_yaml(feature_path).get("feature_key") or "unknown")
    return "unknown"


def parse_execution_event_line(line: str) -> dict[str, Any] | None:
    stripped = line.strip()
    if not stripped.startswith("- "):
        return None
    tokens = stripped[2:].split()
    if len(tokens) < 2 or not tokens[0].endswith("Z"):
        return None
    record: dict[str, Any] = {"timestamp": tokens[0]}
    for token in tokens[1:]:
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        record[key] = parse_event_value(value)
    if "event_type" not in record:
        return None
    return record


def parse_event_value(value: str) -> Any:
    if value == "none":
        return None
    if value.isdigit():
        return int(value)
    if "," in value:
        return [parse_event_value(item) for item in value.split(",") if item]
    return value


def format_event_value(value: Any) -> str:
    if value is None:
        return "none"
    if isinstance(value, (list, tuple, set)):
        return ",".join(format_event_value(item) for item in value)
    text = str(value).strip() or "none"
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^A-Za-z0-9_./,:=-]+", "-", text)
    return text.strip("-") or "none"


def summarize_event_record(event: dict[str, Any] | None) -> str:
    if not event:
        return f"- Recorded pipeline event at {utc_now()}."
    event_type = event.get("event_type")
    if event_type == "run_initialized":
        return f"- Initialized the run; next step `{event.get('next')}`."
    if event_type == "gate_status_changed":
        status = str(event.get("new_status") or "updated")
        verb = {
            "approved": "Approved",
            "complete": "Completed",
            "delegated": "Delegated",
            "drafted": "Drafted",
            "blocked": "Blocked",
            "reopened": "Reopened",
            "stale": "Marked stale",
        }.get(status, "Updated")
        return f"- {verb} `{event.get('gate')}` gate."
    if event_type == "artifact_marked_stale":
        return f"- Marked `{event.get('artifact')}` stale."
    if event_type == "slice_completed":
        return f"- Completed slice `{event.get('slice')}`."
    if event_type == "slice_retry_completed":
        return f"- Completed retry for slice `{event.get('slice')}`."
    if event_type == "feature_promoted":
        return f"- Promoted feature memory to `{event.get('canonical_path')}`."
    if event_type == "incoming_variant_archived":
        return f"- Archived incoming variant for `{event.get('canonical_path')}`."
    if event_type == "public_raw_verified":
        return f"- Verified public raw artifacts; index lines: {event.get('index_lines')}."
    if event_type == "verification_completed":
        return f"- Verification completed with result `{event.get('result')}`."
    if event_type == "review_completed":
        return f"- Review `{event.get('review_id')}` completed with result `{event.get('result')}`."
    return f"- Recorded `{event_type}` event in `events.yaml`."


def append_run_plan_update(
    workspace: Path,
    *,
    gate: str,
    old_status: Any,
    new_status: Any,
    reason: str | None,
) -> None:
    if gate != "implementation" or new_status not in {"approved", "delegated", "complete"}:
        return
    path = workspace / "execution.md"
    if not path.exists():
        return
    execution = path.read_text(encoding="utf-8")
    if new_status in {"approved", "delegated"}:
        update = "- Implementation became allowed after planning gates were approved."
    elif new_status == "complete":
        update = "- Implementation completed after all slices finished."
    else:
        update = f"- Implementation status changed to `{new_status}`."
    if update in execution:
        return
    if "## Run Plan Updates" not in execution:
        insert_at = execution.find("\n## Non-Delegable Checkpoints")
        section = "\n\n## Run Plan Updates\n\n"
        if insert_at == -1:
            execution = execution.rstrip() + section
        else:
            execution = execution[:insert_at].rstrip() + section + execution[insert_at:]
    execution = execution.replace("## Run Plan Updates\n\nNone currently recorded.\n", "## Run Plan Updates\n\n")
    match = re.search(r"^## Run Plan Updates\s*$", execution, flags=re.MULTILINE)
    if not match:
        write_text(path, execution.rstrip() + "\n" + update + "\n")
        return
    after_heading = execution[match.end() :]
    next_heading = re.search(r"\n##\s+", after_heading)
    if next_heading:
        insert_at = match.end() + next_heading.start()
        execution = execution[:insert_at].rstrip() + "\n" + update + "\n" + execution[insert_at:]
    else:
        execution = execution.rstrip() + "\n" + update + "\n"
    write_text(path, execution)
