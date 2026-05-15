"""Artifact-level validation helpers."""

from __future__ import annotations

from pathlib import Path


SCAFFOLD_ONLY_MARKERS = (
    "Status: scaffold-only",
    "artifact_state: scaffold-only",
    "artifact_state: scaffold",
)


def scaffold_only_blocker(workspace: Path, artifact: str) -> list[str]:
    path = workspace / artifact
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8")
    if any(marker in content for marker in SCAFFOLD_ONLY_MARKERS):
        return [f"{artifact} is scaffold-only and cannot satisfy planning-package validation"]
    return []
