"""Candidate skill isolation helpers for pipelinebench."""

from __future__ import annotations

from pathlib import Path

from .common import BenchError

def validate_candidate_path(root: Path, candidate: Path) -> None:
    candidate = candidate.resolve()
    quarantine = (root / ".agents/skill-lab/quarantine").resolve()
    try:
        candidate.relative_to(quarantine)
    except ValueError as exc:
        raise BenchError("candidate must be under .agents/skill-lab/quarantine") from exc
    if candidate.name != "SKILL.candidate.md":
        raise BenchError("candidate file must be named SKILL.candidate.md")
    if not candidate.exists():
        raise BenchError(f"candidate file does not exist: {candidate}")

def normalize_candidate_path(root: Path, candidate: Path) -> str:
    candidate = candidate.resolve()
    try:
        return candidate.relative_to(root).as_posix()
    except ValueError:
        return str(candidate)
