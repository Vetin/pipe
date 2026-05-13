"""Shared constants and process helpers for featurectl."""

from __future__ import annotations

import datetime as dt
import random
import re
import string
import subprocess
from pathlib import Path
from typing import Any

CONTRACT_VERSION = "0.1.0"
VALID_STEPS = {
    "intake",
    "context",
    "feature_contract",
    "architecture",
    "tech_design",
    "slicing",
    "readiness",
    "worktree",
    "tdd_implementation",
    "review",
    "verification",
    "finish",
    "promote",
}
DEFAULT_GATES = {
    "feature_contract": "pending",
    "architecture": "pending",
    "tech_design": "pending",
    "slicing_readiness": "pending",
    "implementation": "blocked",
    "review": "pending",
    "verification": "pending",
    "finish": "pending",
}
DEFAULT_STALE = {
    "feature": False,
    "architecture": False,
    "tech_design": False,
    "slices": False,
    "evidence": False,
    "review": False,
    "feature_card": True,
    "canonical_docs": True,
    "index": False,
}
VALID_GATE_STATES = {
    "pending",
    "drafted",
    "approved",
    "delegated",
    "blocked",
    "reopened",
    "stale",
    "complete",
}
INACTIVE_WORKSPACE_LIFECYCLES = {"promoted-readonly", "archived", "abandoned"}
VALID_WORKSPACE_LIFECYCLES = {"active", "canonical", *INACTIVE_WORKSPACE_LIFECYCLES}
FEATURE_REQUIRED_HEADINGS = (
    "## Intent",
    "## Motivation",
    "## Actors",
    "## Goals",
    "## Non-Goals",
    "## Functional Requirements",
    "## Non-Functional Requirements",
    "## Acceptance Criteria",
    "## Assumptions",
    "## Open Questions",
)
TECH_DESIGN_REQUIRED_HEADINGS = (
    "## Change Delta",
    "## Implementation Summary",
    "## Modules And Responsibilities",
    "## Dependency And Ownership Plan",
    "## Contracts",
    "## API/Event/Schema Details",
    "## Core Code Sketches",
    "## Data Model",
    "## Error Handling",
    "## Security Considerations",
    "## Test Strategy",
    "## Migration Plan",
    "## Rollback Plan",
    "## Integration Notes",
    "## Decision Traceability",
)
PROFILE_EXAMPLE_KEYS = {
    "source_examples",
    "test_examples",
    "doc_examples",
    "contract_examples",
    "integration_examples",
}


class FeatureCtlError(RuntimeError):
    """Raised for expected command failures."""

def repo_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        raise FeatureCtlError("must be run inside a git repository") from exc
    return Path(result.stdout.strip()).resolve()


def resolve_workspace(root: Path, workspace: str | None) -> Path:
    if workspace:
        path = Path(workspace)
        if not path.is_absolute():
            path = root / path
        return path.resolve()

    cwd = Path.cwd().resolve()
    for candidate in [cwd, *cwd.parents]:
        if (candidate / "feature.yaml").exists() and (candidate / "state.yaml").exists():
            return candidate

    workspaces = sorted((root / ".ai/feature-workspaces").glob("*/*--run-*"))
    if len(workspaces) == 1:
        return workspaces[0].resolve()
    raise FeatureCtlError("workspace is required when it cannot be inferred")

def normalize_domain(domain: str) -> str:
    normalized = slugify(domain)
    if not normalized:
        raise FeatureCtlError("domain cannot be empty")
    return normalized


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    if not value:
        raise FeatureCtlError("slug cannot be empty")
    return value


def generate_run_id() -> str:
    date = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    suffix = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(4))
    return f"run-{date}-{suffix}"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_branch_exists(root: Path, branch: str) -> bool:
    result = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
        cwd=root,
    )
    return result.returncode == 0


def run_git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() or exc.stdout.strip()
        raise FeatureCtlError(f"git {' '.join(args)} failed: {stderr}") from exc
    return result.stdout
