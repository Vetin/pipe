#!/usr/bin/env python3
"""Aggregate real showcase planning reports."""

from __future__ import annotations

from pathlib import Path
import re
import yaml


ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "pipeline-lab/showcases/real-showcases.yaml"
RUNS = ROOT / "pipeline-lab/showcases/real-runs"
OUT = ROOT / "pipeline-lab/showcases/real-runs-summary.md"
OUT_YAML = ROOT / "pipeline-lab/showcases/real-runs-summary.yaml"


def main() -> int:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))["showcases"]
    rows = []
    for name, case in config.items():
        report = RUNS / name / "report.md"
        text = report.read_text(encoding="utf-8") if report.exists() else ""
        basic = extract_result(text, "Basic validation result")
        readiness = extract_result(text, "Readiness validation result")
        rows.append(
            {
                "case": name,
                "feature_key": case["feature_key"],
                "repo_path": case["repo_path"],
                "basic_validation": basic,
                "readiness_validation": readiness,
                "report": str(report.relative_to(ROOT)),
            }
        )
    write_markdown(rows)
    OUT_YAML.write_text(yaml.safe_dump({"artifact_contract_version": "0.1.0", "runs": rows}, sort_keys=False), encoding="utf-8")
    print(f"summary: {OUT}")
    print(f"summary_yaml: {OUT_YAML}")
    return 0


def extract_result(text: str, label: str) -> str:
    match = re.search(rf"{re.escape(label)}: `([^`]+)`", text)
    return match.group(1) if match else "missing"


def write_markdown(rows: list[dict[str, str]]) -> None:
    lines = [
        "# Real Showcase Runs",
        "",
        "Planning-only runs against locally cloned upstream repositories.",
        "",
        "| Case | Feature Key | Basic Validation | Readiness Validation | Report |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['case']} | `{row['feature_key']}` | {row['basic_validation']} | {row['readiness_validation']} | `{row['report']}` |"
        )
    lines.extend(
        [
            "",
            "Expected readiness result is `1` because planning gates remain drafted until a user approves or delegates implementation.",
            "Source implementation was intentionally not performed in these runs.",
        ]
    )
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
