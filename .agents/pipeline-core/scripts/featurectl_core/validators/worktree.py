"""Worktree validation helpers."""

from __future__ import annotations

from pathlib import Path

from ..promotion import infer_worktree_path
from ..shared import repo_root


def validate_current_directory_is_worktree(workspace: Path) -> list[str]:
    worktree_path = infer_worktree_path(workspace)
    current_checkout = repo_root()
    if current_checkout != worktree_path:
        return [f"current checkout is not configured feature worktree: {worktree_path}"]
    return []
