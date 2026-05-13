"""Showcase scoring helpers for pipelinebench."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import BenchError, read_yaml

def load_showcase_scenarios(showcase_root: Path) -> list[dict[str, Any]]:
    scenario_dir = showcase_root / "scenarios"
    scenarios = [read_yaml(path) for path in sorted(scenario_dir.glob("*.yaml"))]
    if len(scenarios) < 10:
        raise BenchError("showcases require at least 10 scenarios")
    seen: set[str] = set()
    for scenario in scenarios:
        for field in ("id", "codebase", "feature_goal", "domain", "title", "expected_focus"):
            if field not in scenario:
                raise BenchError(f"showcase scenario missing {field}: {scenario}")
        if scenario["id"] in seen:
            raise BenchError(f"duplicate showcase scenario: {scenario['id']}")
        seen.add(scenario["id"])
    return scenarios

def score_steps(root: Path, rubric: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for step in rubric.get("steps", []):
        skill_path = root / step["skill_path"]
        if not skill_path.exists():
            raise BenchError(f"missing skill path: {step['skill_path']}")
        content = skill_path.read_text(encoding="utf-8").lower()
        checks = []
        for criterion in step.get("criteria", []):
            terms = [term.lower() for term in criterion.get("terms", [])]
            passed = all(term in content for term in terms)
            checks.append({"name": criterion["name"], "passed": passed})
        passed_count = sum(1 for item in checks if item["passed"])
        total = len(checks) or 1
        rows.append(
            {
                "step": step["step"],
                "skill": step["skill_path"],
                "score": round(passed_count / total, 3),
                "passed": passed_count,
                "total": total,
                "checks": checks,
            }
        )
    return rows

def side_by_side_rows(scenarios: list[dict[str, Any]], step_scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    score_by_step = {item["step"]: item["score"] for item in step_scores}
    for scenario in scenarios:
        focus = scenario.get("expected_focus", [])
        focus_scores = {step: score_by_step.get(step, 0.0) for step in focus}
        rows.append(
            {
                "scenario": scenario["id"],
                "codebase": scenario["codebase"],
                "feature_goal": scenario["feature_goal"],
                "focus_scores": focus_scores,
                "average_focus_score": round(sum(focus_scores.values()) / (len(focus_scores) or 1), 3),
            }
        )
    return rows

def write_showcase_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Showcase Comparison",
        "",
        f"Iterations: {summary['iterations']}",
        f"Scenarios: {summary['scenario_count']}",
        "",
        "## Step Solidity",
        "",
        "| Step | Skill | Score | Checks |",
        "| --- | --- | ---: | ---: |",
    ]
    for row in summary["step_scores"]:
        lines.append(f"| {row['step']} | `{row['skill']}` | {row['score']:.3f} | {row['passed']}/{row['total']} |")
    lines.extend(
        [
            "",
            "## Side By Side",
            "",
            "| Scenario | Codebase | Feature Goal | Avg Focus Score |",
            "| --- | --- | --- | ---: |",
        ]
    )
    for row in summary["side_by_side"]:
        lines.append(f"| {row['scenario']} | {row['codebase']} | {row['feature_goal']} | {row['average_focus_score']:.3f} |")
    lines.extend(
        [
            "",
            "## Iterations",
            "",
            "| Iteration | Scenario | Weakest Step | Score | Status |",
            "| ---: | --- | --- | ---: | --- |",
        ]
    )
    for row in summary["iterations_log"]:
        lines.append(f"| {row['iteration']} | {row['scenario']} | {row['weakest_step']} | {row['weakest_score']:.3f} | {row['status']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
