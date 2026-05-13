"""Canonical promotion and feature index helpers for featurectl."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .docsets import next_skill_for_step
from .formatting import read_yaml, write_text, write_yaml
from .shared import CONTRACT_VERSION, FeatureCtlError, utc_now

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
        if current_step == "promote" and state.setdefault("gates", {}).get("finish") == "complete":
            state["gates"]["implementation"] = "complete"
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
