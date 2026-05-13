"""Execution log validators for featurectl workspaces."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


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
