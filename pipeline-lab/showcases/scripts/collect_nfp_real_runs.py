#!/usr/bin/env python3
"""Collect results from fresh NFP-driven real-repo implementation runs."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "pipeline-lab/showcases/real-showcases.yaml"
OUT_DIR = ROOT / "pipeline-lab/showcases/nfp-real-runs"


def run(cmd: list[str], cwd: Path, check: bool = False) -> subprocess.CompletedProcess[str]:
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


def default_ref(repo: Path) -> str:
    head = run(["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], repo).stdout.strip()
    return head or "origin/main"


def list_relative_files(root: Path, pattern: str) -> list[str]:
    base = root / pattern
    if not base.exists():
        return []
    return sorted(path.relative_to(root).as_posix() for path in base.rglob("*") if path.is_file())


def collect_case(case: str, meta: dict[str, Any]) -> dict[str, Any]:
    repo = ROOT / meta["repo_path"]
    base = default_ref(repo)
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo, check=True).stdout.strip()
    commit = run(["git", "rev-parse", "HEAD"], repo, check=True).stdout.strip()
    short_commit = run(["git", "rev-parse", "--short", "HEAD"], repo, check=True).stdout.strip()
    status = run(["git", "status", "--short"], repo).stdout.strip()
    changed_files = run(["git", "diff", "--name-only", f"{base}..HEAD"], repo).stdout.splitlines()
    changed_code_files = [
        path
        for path in changed_files
        if not path.startswith(".ai/")
        and not path.startswith(".agents/")
        and path != ".codex-nfp-final.txt"
    ]
    full_diff_check = run(["git", "diff", "--check", f"{base}..HEAD"], repo)
    code_diff_check = run(
        [
            "git",
            "diff",
            "--check",
            f"{base}..HEAD",
            "--",
            ".",
            ":(exclude).ai/**",
            ":(exclude).agents/**",
            ":(exclude).codex-nfp-final.txt",
        ],
        repo,
    )
    features = list_relative_files(repo, ".ai/features")
    workspaces = list_relative_files(repo, ".ai/feature-workspaces")
    final_path = repo / ".codex-nfp-final.txt"
    final_text = final_path.read_text(errors="replace") if final_path.exists() else ""
    return {
        "case": case,
        "repo": meta["repo_path"],
        "feature_goal": meta["feature_goal"],
        "branch": branch,
        "commit": commit,
        "short_commit": short_commit,
        "default_ref": base,
        "status": status or "clean",
        "changed_file_count": len(changed_files),
        "changed_code_files": changed_code_files,
        "feature_artifact_file_count": len(features),
        "workspace_artifact_file_count": len(workspaces),
        "codex_final_present": final_path.exists(),
        "code_diff_check": {
            "returncode": code_diff_check.returncode,
            "output": code_diff_check.stdout.strip(),
        },
        "full_diff_check": {
            "returncode": full_diff_check.returncode,
            "output": full_diff_check.stdout.strip(),
        },
        "codex_final": final_text,
    }


def render_markdown(results: list[dict[str, Any]]) -> str:
    lines = [
        "# Fresh NFP Real-Repo Implementation Runs",
        "",
        "Each repository was reset to its upstream default branch, then a supervisor subagent invoked `codex exec` inside that repository to run the native feature pipeline from `nfp-00` through `nfp-12`.",
        "",
        "Conversation exports are available in [`conversations/index.md`](conversations/index.md) and [`conversations/index.html`](conversations/index.html).",
        "",
        "## Summary",
        "",
        "| Repo | Branch | Commit | Code diff check | Status | Code files |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for row in results:
        code_check = "pass" if row["code_diff_check"]["returncode"] == 0 else "fail"
        status = row["status"].replace("\n", "<br>")
        lines.append(
            f"| `{row['case']}` | `{row['branch']}` | `{row['short_commit']}` | "
            f"`{code_check}` | {status} | {len(row['changed_code_files'])} |"
        )

    lines.extend(["", "## Details", ""])
    for row in results:
        code_check = row["code_diff_check"]
        full_check = row["full_diff_check"]
        lines.extend(
            [
                f"### {row['case']}",
                "",
                f"- Repo path: `{row['repo']}`",
                f"- Feature: {row['feature_goal']}",
                f"- Branch: `{row['branch']}`",
                f"- Commit: `{row['commit']}`",
                f"- Working tree status: `{row['status']}`",
                f"- NFP feature artifact files: `{row['feature_artifact_file_count']}`",
                f"- NFP workspace artifact files: `{row['workspace_artifact_file_count']}`",
                f"- `.codex-nfp-final.txt` present: `{str(row['codex_final_present']).lower()}`",
                "",
                "Changed production/test files:",
            ]
        )
        if row["changed_code_files"]:
            lines.extend(f"- `{path}`" for path in row["changed_code_files"])
        else:
            lines.append("- none detected outside `.ai`, `.agents`, and `.codex-nfp-final.txt`")
        lines.extend(
            [
                "",
                "Code diff check:",
                "",
                "```text",
                code_check["output"] or f"returncode={code_check['returncode']}",
                "```",
                "",
                "Full diff check:",
                "",
                "```text",
                full_check["output"] or f"returncode={full_check['returncode']}",
                "```",
                "",
                "Nested Codex final summary:",
                "",
                "```text",
                row["codex_final"].strip()[:8000] or "missing",
                "```",
                "",
            ]
        )
    markdown = "\n".join(lines)
    return "\n".join(line.rstrip() for line in markdown.splitlines())


def main() -> int:
    config = load_config()
    results = [collect_case(case, meta) for case, meta in config.items()]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "summary.yaml").write_text(yaml.safe_dump({"results": results}, sort_keys=False))
    (OUT_DIR / "summary.md").write_text(render_markdown(results) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
