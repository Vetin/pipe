#!/usr/bin/env python3
"""Aggregate code-backed showcase implementation reports."""

from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
RUNS_DIR = ROOT / "pipeline-lab/showcases/implementation-runs"


def load_cases() -> list[dict]:
    cases = []
    for path in sorted(RUNS_DIR.glob("*/implementation-summary.yaml")):
        cases.append(yaml.safe_load(path.read_text()))
    return cases


def bullet(items: list[str]) -> str:
    return "\n".join(f"- `{item}`" for item in items)


def slice_lines(observations: list[dict]) -> str:
    return "\n".join(
        f"- `{row['slice']}`: red `{row['red_returncode']}`, green `{row['green_returncode']}`, "
        f"verification `{row['verification_returncode']}`, test `{row['test']}`"
        for row in observations
    )


def render(cases: list[dict]) -> str:
    lines = [
        "# Full Showcase Implementation Report",
        "",
        "This report summarizes the code-backed validation run across the ten cloned repositories.",
        "Each case used the Native Feature Pipeline from feature description through artifacts, gate approval, TDD slice evidence, review, verification, finish, and promotion.",
        "",
        "Important scope note: the code changes are bounded showcase implementations under each feature worktree's `showcase/<feature>` directory. They validate integration mechanics and feature behavior without patching upstream production modules outside that directory.",
        "",
        "## Overall Result",
        "",
        "| Repository | Feature | Validation | Readiness | Patch |",
        "| --- | --- | --- | --- | --- |",
    ]
    for case in cases:
        name = case["case"]
        validation = case["validation"].replace("\n", " ")
        readiness = case["readiness"].replace("\n", " ")
        lines.append(
            f"| `{case['repository']}` | {case['feature']} | `{validation}` | `{readiness}` | "
            f"[patch]({name}/implementation.patch) |"
        )

    for case in cases:
        name = case["case"]
        lines.extend(
            [
                "",
                f"## {case['repository']}: {case['feature']}",
                "",
                f"- Worktree: `{case['worktree']}`",
                f"- Workspace: `{case['workspace']}`",
                f"- Report: [{name}/report.md]({name}/report.md)",
                f"- Patch: [{name}/implementation.patch]({name}/implementation.patch)",
                "",
                "Generated artifacts:",
                bullet(case["artifact_inventory"]),
                "",
                "Code changes:",
                bullet(case["source_files"]),
                "",
                "Diff stat:",
                "",
                "```text",
                case["diff_stat"] or "no diff",
                "```",
                "",
                "Slice validation:",
                slice_lines(case["observations"]),
                "",
                "Pipeline checks:",
                "",
                "```text",
                f"{case['validation']}\n{case['readiness']}",
                "```",
                "",
                "Implementation status: full bounded showcase implementation. Production-module integration remains a separate upstreaming step because this run intentionally constrained writes to a reviewable `showcase/` surface inside each cloned repository.",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    cases = load_cases()
    (RUNS_DIR / "full-report.md").write_text(render(cases))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
