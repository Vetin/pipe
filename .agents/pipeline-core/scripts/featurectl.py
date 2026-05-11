#!/usr/bin/env python3
"""Deterministic helper for the Native Feature Pipeline."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import random
import re
import shutil
import string
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised only on missing deps.
    raise SystemExit("featurectl.py requires PyYAML to read and write pipeline YAML.") from exc


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


class FeatureCtlError(RuntimeError):
    """Raised for expected command failures."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="featurectl.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="initialize pipeline directories")
    init_parser.set_defaults(func=cmd_init)

    new_parser = subparsers.add_parser("new", help="create a feature worktree and workspace")
    new_parser.add_argument("--domain", required=True)
    new_parser.add_argument("--title", required=True)
    new_parser.add_argument("--slug")
    new_parser.add_argument("--run-id")
    new_parser.add_argument("--worktree-root", default="../worktrees")
    new_parser.add_argument("--base-ref", default="HEAD")
    new_parser.add_argument("--stop-point", default="feature_contract")
    new_parser.set_defaults(func=cmd_new)

    status_parser = subparsers.add_parser("status", help="print workspace status")
    status_parser.add_argument("--workspace")
    status_parser.set_defaults(func=cmd_status)

    try:
        args = parser.parse_args(argv)
        args.func(args)
    except FeatureCtlError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_init(_args: argparse.Namespace) -> None:
    root = repo_root()
    ensure_init_tree(root)
    print("initialized Native Feature Pipeline directories")


def cmd_new(args: argparse.Namespace) -> None:
    root = repo_root()
    ensure_init_tree(root)

    domain = normalize_domain(args.domain)
    slug = slugify(args.slug or args.title)
    run_id = args.run_id or generate_run_id()
    feature_key = f"{domain}/{slug}"
    branch = f"feature/{domain}-{slug}-{run_id}"
    worktree_root = (root / args.worktree_root).resolve()
    worktree_path = worktree_root / f"{domain}-{slug}-{run_id}"
    workspace_rel = Path(".ai") / "feature-workspaces" / domain / f"{slug}--{run_id}"
    workspace_path = worktree_path / workspace_rel

    if worktree_path.exists():
        raise FeatureCtlError(f"worktree path already exists: {worktree_path}")
    if git_branch_exists(root, branch):
        raise FeatureCtlError(f"branch already exists: {branch}")

    worktree_root.mkdir(parents=True, exist_ok=True)
    run_git(root, "worktree", "add", "-b", branch, str(worktree_path), args.base_ref)

    workspace_path.mkdir(parents=True, exist_ok=False)
    for subdir in ("adrs", "diagrams", "contracts", "reviews", "evidence"):
        (workspace_path / subdir).mkdir(parents=True, exist_ok=True)

    created_at = utc_now()
    worktree_value = os.path.relpath(worktree_path, root)
    workspace_value = workspace_rel.as_posix()
    canonical_path = f".ai/features/{domain}/{slug}"

    write_yaml(
        workspace_path / "feature.yaml",
        {
            "artifact_contract_version": CONTRACT_VERSION,
            "feature_key": feature_key,
            "domain": domain,
            "slug": slug,
            "title": args.title,
            "status": "draft",
            "run_id": run_id,
            "branch": branch,
            "worktree": worktree_value,
            "canonical_path": canonical_path,
            "workspace_path": workspace_value,
            "aliases": [],
            "keywords": [domain, slug],
            "created_at": created_at,
            "updated_at": created_at,
        },
    )
    write_yaml(
        workspace_path / "state.yaml",
        {
            "artifact_contract_version": CONTRACT_VERSION,
            "feature_key": feature_key,
            "run_id": run_id,
            "current_step": "context",
            "worktree": {
                "branch": branch,
                "path": worktree_value,
            },
            "gates": dict(DEFAULT_GATES),
            "stale": dict(DEFAULT_STALE),
            "active_slice": None,
            "locks": {
                "owner": None,
                "acquired_at": None,
            },
        },
    )
    write_text(workspace_path / "apex.md", render_apex(feature_key))
    write_text(workspace_path / "execution.md", render_execution(args.title, feature_key, args.stop_point))

    print(f"feature_key: {feature_key}")
    print(f"branch: {branch}")
    print(f"worktree: {worktree_value}")
    print(f"workspace: {workspace_value}")
    print("next_step: nfp-01-context")


def cmd_status(args: argparse.Namespace) -> None:
    root = repo_root()
    workspace = resolve_workspace(root, args.workspace)
    feature = read_yaml(workspace / "feature.yaml")
    state = read_yaml(workspace / "state.yaml")
    blockers = status_blockers(root, workspace, feature, state)

    print(f"feature_key: {feature.get('feature_key')}")
    print(f"worktree: {state.get('worktree', {}).get('path')}")
    print(f"current_step: {state.get('current_step')}")
    print("gates:")
    for gate, status in state.get("gates", {}).items():
        print(f"  {gate}: {status}")
    print("stale:")
    for artifact, stale in state.get("stale", {}).items():
        print(f"  {artifact}: {str(stale).lower()}")
    print("blocking_issues:")
    if blockers:
        for blocker in blockers:
            print(f"  - {blocker}")
    else:
        print("  none")
    print(f"next_step: {next_skill_for_step(state.get('current_step'))}")


def ensure_init_tree(root: Path) -> None:
    dirs = [
        ".ai/feature-workspaces",
        ".ai/features",
        ".ai/features-archive",
        ".ai/knowledge",
        ".ai/pipeline-docs/global",
        ".agents/pipeline-core/references",
        ".agents/pipeline-core/scripts/schemas",
        ".agents/skills",
        ".agents/skill-lab/quarantine",
        ".agents/skill-lab/accepted",
        ".agents/skill-lab/rejected",
        "pipeline-lab/benchmarks/scenarios",
        "pipeline-lab/benchmarks/suites",
        "pipeline-lab/envs/toy-monolith",
        "pipeline-lab/envs/modular-api",
        "pipeline-lab/scorecards",
        "tests/feature_pipeline",
    ]
    for dirname in dirs:
        (root / dirname).mkdir(parents=True, exist_ok=True)

    write_if_missing(
        root / ".ai/features/index.yaml",
        "artifact_contract_version: '0.1.0'\nfeatures: []\n",
    )
    write_if_missing(root / ".ai/features/overview.md", "# Feature Overview\n\nNo canonical features have been promoted yet.\n")
    write_if_missing(
        root / ".gitignore",
        "pipeline-lab/runs/\n.ai/logs/\n*.tmp\n__pycache__/\n.pytest_cache/\n",
    )


def render_apex(feature_key: str) -> str:
    return f"""# Apex: {feature_key}

## Read Order

1. `feature.yaml` - identity and paths
2. `state.yaml` - machine state
3. `execution.md` - run plan, approvals, docs consulted, next step
4. `feature.md` - product contract
5. `architecture.md` - system design
6. `tech-design.md` - implementation design
7. `slices.yaml` - TDD execution plan
8. `evidence/manifest.yaml` - evidence index
9. `reviews/` - review results

## Main Artifacts

- Feature contract: `feature.md`
- Architecture: `architecture.md`
- Technical design: `tech-design.md`
- Implementation plan: `slices.yaml`
- ADRs: `adrs/`
- Contracts: `contracts/`
- Evidence: `evidence/`
- Reviews: `reviews/`
- Execution log: `execution.md`

## Current Status

See `state.yaml`.

## Next Action

See `execution.md`.
"""


def render_execution(title: str, feature_key: str, stop_point: str) -> str:
    now = utc_now()
    return f"""# Execution Log: {feature_key}

## User Request

{title}

## Run Plan

Mode: planning autorun
Stop point: {stop_point}
Implementation allowed: no

Planned steps:

1. Context discovery
2. Feature contract
3. Architecture
4. Technical design
5. Slicing
6. Readiness summary

## Non-Delegable Checkpoints

Stop and ask user before:

- destructive command
- production data migration
- new production dependency
- public API breaking change
- security model change
- credential/secret handling
- paid external service
- license-impacting dependency

## Clarifying Questions

None currently recorded.

## Assumptions

None currently recorded.

## Docs Consulted

None yet.

## Gate Events

None yet.

## Scope Changes

None.

## Current Step

context

## Next Step

nfp-01-context

## Summary

Feature run initialized at {now}. The next step is context discovery.
"""


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


def status_blockers(root: Path, workspace: Path, feature: dict[str, Any], state: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    for name in ("apex.md", "feature.yaml", "state.yaml", "execution.md"):
        if not (workspace / name).exists():
            blockers.append(f"missing {name}")
    if feature.get("feature_key") != state.get("feature_key"):
        blockers.append("feature.yaml and state.yaml feature_key mismatch")
    if feature.get("run_id") != state.get("run_id"):
        blockers.append("feature.yaml and state.yaml run_id mismatch")
    current_step = state.get("current_step")
    if current_step not in VALID_STEPS:
        blockers.append(f"invalid current_step: {current_step}")
    worktree_info = state.get("worktree") or {}
    worktree_value = worktree_info.get("path")
    branch_value = worktree_info.get("branch")
    if worktree_value:
        worktree_path = (root / worktree_value).resolve()
        if not worktree_path.exists():
            blockers.append(f"worktree path does not exist: {worktree_value}")
        else:
            try:
                workspace.relative_to(worktree_path)
            except ValueError:
                blockers.append("workspace is not inside configured worktree")
            try:
                actual_branch = run_git(worktree_path, "rev-parse", "--abbrev-ref", "HEAD").strip()
            except FeatureCtlError as exc:
                blockers.append(str(exc))
            else:
                if branch_value and actual_branch != branch_value:
                    blockers.append(f"worktree branch mismatch: expected {branch_value}, got {actual_branch}")
    else:
        blockers.append("state.yaml missing worktree.path")
    return blockers


def next_skill_for_step(step: str | None) -> str:
    mapping = {
        "context": "nfp-01-context",
        "feature_contract": "nfp-02-feature-contract",
        "architecture": "nfp-03-architecture",
        "tech_design": "nfp-04-tech-design",
        "slicing": "nfp-05-slicing",
        "readiness": "nfp-06-readiness",
        "worktree": "nfp-07-worktree",
        "tdd_implementation": "nfp-08-tdd-implementation",
        "review": "nfp-09-review",
        "verification": "nfp-10-verification",
        "finish": "nfp-11-finish",
        "promote": "nfp-12-promote",
    }
    return mapping.get(step or "", "unknown")


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


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FeatureCtlError(f"missing YAML file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise FeatureCtlError(f"YAML file must contain a mapping: {path}")
    return loaded


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=False)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        write_text(path, content)


if __name__ == "__main__":
    raise SystemExit(main())
