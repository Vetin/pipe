#!/usr/bin/env python3
"""Copy completed showcase implementations into the base cloned repositories."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[3]
SHOWCASE_DIR = ROOT / "pipeline-lab/showcases"
CONFIG_PATH = SHOWCASE_DIR / "real-showcases.yaml"
RUNS_DIR = SHOWCASE_DIR / "implementation-runs"
OUT_DIR = SHOWCASE_DIR / "materialized-runs"


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed in {cwd}\n{result.stdout}")
    return result


def load_config() -> dict[str, dict[str, Any]]:
    return yaml.safe_load(CONFIG_PATH.read_text())["showcases"]


def copy_tree(src: Path, dest: Path, *, force: bool) -> None:
    if not src.exists():
        raise RuntimeError(f"source path missing: {src}")
    if dest.exists():
        if not force:
            raise RuntimeError(f"destination exists; rerun with --force: {dest}")
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest)


def copy_file(src: Path, dest: Path, *, force: bool) -> None:
    if not src.exists():
        raise RuntimeError(f"source path missing: {src}")
    if dest.exists() and not force:
        raise RuntimeError(f"destination exists; rerun with --force: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def test_command(summary: dict[str, Any]) -> str:
    slug = Path(summary["source_files"][0]).parts[1]
    if summary["language"] == "go":
        return f"go test ./showcase/{slug}"
    tests = sorted(path for path in summary["source_files"] if path.endswith(".test.js"))
    return " && ".join(f"node {path}" for path in tests)


def materialize_case(case: str, config: dict[str, Any], *, force: bool, commit: bool) -> dict[str, Any]:
    summary_path = RUNS_DIR / case / "implementation-summary.yaml"
    summary = yaml.safe_load(summary_path.read_text())
    repo = ROOT / config["repo_path"]
    worktree = Path(summary["worktree"])
    workspace = Path(summary["workspace"])
    slug = Path(summary["source_files"][0]).parts[1]

    repo_feature_dir = repo / "showcase" / slug
    worktree_feature_dir = worktree / "showcase" / slug
    copy_tree(worktree_feature_dir, repo_feature_dir, force=force)

    workspace_rel = workspace.relative_to(worktree)
    copy_tree(workspace, repo / workspace_rel, force=force)

    feature = yaml.safe_load((workspace / "feature.yaml").read_text())
    canonical_rel = Path(feature["canonical_path"])
    canonical_src = worktree / canonical_rel
    canonical_copied = False
    if canonical_src.exists():
        copy_tree(canonical_src, repo / canonical_rel, force=force)
        canonical_copied = True

    copy_file(RUNS_DIR / case / "implementation.patch", repo / ".ai" / "showcase-patches" / f"{case}.patch", force=force)
    copy_file(RUNS_DIR / case / "report.md", repo / ".ai" / "showcase-reports" / f"{case}.md", force=force)

    command = test_command(summary)
    test = run(command.split() if "&&" not in command else ["/bin/zsh", "-lc", command], repo, check=False)
    if test.returncode != 0:
        raise RuntimeError(f"{case} materialized test failed\n{test.stdout}")

    run(["git", "config", "user.email", "showcase@example.com"], repo, check=False)
    run(["git", "config", "user.name", "Showcase Runner"], repo, check=False)
    branch = f"showcase/{case}-pipeline-materialized"
    run(["git", "switch", "-C", branch], repo)

    staged_paths = [
        f"showcase/{slug}",
        workspace_rel.as_posix(),
        f".ai/showcase-patches/{case}.patch",
        f".ai/showcase-reports/{case}.md",
    ]
    if canonical_copied:
        staged_paths.append(canonical_rel.as_posix())
    run(["git", "add", "--sparse", "--", *staged_paths], repo)

    commit_hash = ""
    if commit:
        diff_check = run(["git", "diff", "--cached", "--check"], repo, check=False)
        if diff_check.returncode != 0:
            raise RuntimeError(f"{case} staged diff check failed\n{diff_check.stdout}")
        has_changes = run(["git", "diff", "--cached", "--quiet"], repo, check=False).returncode != 0
        if has_changes:
            run(["git", "commit", "-m", f"Materialize pipeline showcase: {summary['feature']}"], repo)
        commit_hash = run(["git", "rev-parse", "--short", "HEAD"], repo).stdout.strip()

    status = run(["git", "status", "--short", "--", *staged_paths], repo).stdout.strip()
    return {
        "case": case,
        "repo": str(repo),
        "branch": branch,
        "commit": commit_hash,
        "feature_dir": f"showcase/{slug}",
        "workspace": workspace_rel.as_posix(),
        "canonical": canonical_rel.as_posix() if canonical_copied else "",
        "patch": f".ai/showcase-patches/{case}.patch",
        "report": f".ai/showcase-reports/{case}.md",
        "test_command": command,
        "test_output": test.stdout.strip() or "passed",
        "status": status,
    }


def write_report(results: list[dict[str, Any]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "summary.yaml").write_text(yaml.safe_dump({"results": results}, sort_keys=False))
    lines = [
        "# Materialized Showcase Runs",
        "",
        "These outputs were copied from feature worktrees into the base cloned repositories under `pipeline-lab/showcases/repos/<repo>`.",
        "",
        "| Case | Branch | Commit | Feature Dir | Workspace |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in results:
        lines.append(
            f"| `{row['case']}` | `{row['branch']}` | `{row['commit'] or 'not committed'}` | "
            f"`{row['feature_dir']}` | `{row['workspace']}` |"
        )
    lines.append("")
    lines.append("Each materialized repo also contains `.ai/showcase-patches/<case>.patch` and `.ai/showcase-reports/<case>.md`.")
    (OUT_DIR / "summary.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", action="append", help="case name to materialize; defaults to all")
    parser.add_argument("--force", action="store_true", help="replace generated materialized paths if they already exist")
    parser.add_argument("--no-commit", action="store_true", help="do not commit inside cloned repositories")
    args = parser.parse_args()

    config = load_config()
    cases = args.case or list(config)
    results = [
        materialize_case(case, config[case], force=args.force, commit=not args.no_commit)
        for case in cases
    ]
    write_report(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
