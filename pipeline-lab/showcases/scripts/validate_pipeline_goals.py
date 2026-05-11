#!/usr/bin/env python3
"""Validate pipeline goals against vision, plan, skills, and showcase outputs."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_NATIVE_RUN = ROOT / "pipeline-lab/showcases/native-emulation-runs/20260512-native-debug"
DEFAULT_REPORT = ROOT / "pipeline-lab/showcases/pipeline-goal-validation-report.md"
REQUIRED_WEB_SOURCES = (
    "https://academy.openai.com/public/resources/skills",
    "https://github.com/github/spec-kit",
    "https://openspec.dev/",
    "https://www.bmadcode.com/bmad-method/",
    "https://arxiv.org/abs/2604.05278",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(read_text(path)) or {}


def validate_once(native_run: Path) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    checks.extend(validate_vision_and_plan())
    checks.extend(validate_best_three(native_run))
    checks.extend(validate_project_profile())
    checks.extend(validate_skill_matrix())
    checks.extend(validate_web_best_practices())
    return checks


def check(name: str, passed: bool, detail: str) -> dict[str, str]:
    return {"name": name, "status": "pass" if passed else "fail", "detail": detail}


def validate_vision_and_plan() -> list[dict[str, str]]:
    vision = read_text(ROOT / "vision.md")
    plain_vision = vision.replace("**", "")
    plan = read_text(ROOT / "plan.md")
    return [
        check("vision_user_flow", "Describe the feature" in vision and "Approve or request changes at gates" in vision, "user only describes, answers, and approves gates"),
        check("vision_native_workflow", "The user does not manually call those phases" in plain_vision, "native workflow hides internal phase commands"),
        check("plan_artifact_graph", "one shared artifact graph" in plan and "one deterministic validation layer" in plan, "plan requires artifact graph and validation layer"),
        check("plan_project_context", ".ai/knowledge/" in plan and "bootstrap provisional knowledge" in plan, "plan requires living knowledge and brownfield bootstrap"),
        check("plan_validation_lab", "repeatable validation practice" in plan and "three scorecards" in plan, "plan requires repeatable skill validation"),
    ]


def validate_best_three(native_run: Path) -> list[dict[str, str]]:
    summary = read_yaml(native_run / "summary.yaml")
    cards = summary.get("scorecards") or []
    checks = [
        check("native_prompt_style", summary.get("prompt_style") == "native-user-request", "showcase prompts are native user requests"),
        check("no_direct_skill_invocations", summary.get("direct_skill_invocations") is False, "showcase prompts avoid direct skill invocation list"),
        check("best_three_count", len({card.get("case") for card in cards}) == 3, "three best showcase cases are present"),
    ]
    by_case: dict[str, list[dict[str, Any]]] = {}
    for card in cards:
        by_case.setdefault(str(card.get("case")), []).append(card)
    for case, case_cards in sorted(by_case.items()):
        rounds = {int(card["round"]): card for card in case_cards}
        scores = [float(rounds[index]["overall"]) for index in (1, 2, 3)] if set(rounds) == {1, 2, 3} else []
        checks.append(check(f"{case}_three_rounds", set(rounds) == {1, 2, 3}, "rounds 1, 2, 3 are present"))
        checks.append(check(f"{case}_score_improves", bool(scores) and scores[0] < scores[1] < scores[2], f"scores: {scores}"))
        checks.append(check(f"{case}_production_score", bool(scores) and scores[-1] >= 0.92, f"final score: {scores[-1] if scores else 'missing'}"))
        if 3 in rounds:
            artifacts = rounds[3].get("artifacts") or {}
            checks.append(check(f"{case}_round3_artifacts", all(Path(path).exists() for path in artifacts.values()), "round 3 artifacts exist"))
    return checks


def validate_project_profile() -> list[dict[str, str]]:
    index_path = ROOT / ".ai/knowledge/project-index.yaml"
    snapshot_path = ROOT / ".ai/knowledge/project-snapshot.md"
    context_skill = read_text(ROOT / ".agents/skills/nfp-01-context/SKILL.md")
    profile = read_yaml(index_path) if index_path.exists() else {}
    counts = profile.get("counts") or {}
    return [
        check("init_project_index_exists", index_path.exists(), "project-index.yaml exists"),
        check("init_project_snapshot_exists", snapshot_path.exists(), "project-snapshot.md exists"),
        check("init_source_count", int(counts.get("source_files") or 0) > 0, f"source files: {counts.get('source_files')}"),
        check("init_test_count", int(counts.get("test_files") or 0) > 0, f"test files: {counts.get('test_files')}"),
        check("init_feature_signals", len(profile.get("feature_signals") or []) >= 3, "feature signals extracted"),
        check("context_skill_uses_profile", "featurectl.py init --profile-project" in context_skill, "context skill invokes project profiling when knowledge is sparse"),
    ]


def validate_skill_matrix() -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    skill_paths = sorted((ROOT / ".agents/skills").glob("nfp-*/SKILL.md"))
    checks.append(check("skill_count", len(skill_paths) == 13, f"found {len(skill_paths)} nfp skills"))
    for path in skill_paths:
        content = read_text(path)
        name = path.parent.name
        missing = []
        for token in (
            "pipeline_contract_version: '0.1.0'",
            ".agents/pipeline-core/references/native-skill-protocol.md",
            "methodology/extracted/upstream-pattern-map.md",
            "featurectl.py load-docset",
            "Docs Consulted:",
            "featurectl.py validate",
        ):
            if token not in content:
                missing.append(token)
        checks.append(check(f"skill_{name}", not missing, "missing: " + ", ".join(missing) if missing else "shared protocol present"))
    return checks


def validate_web_best_practices() -> list[dict[str, str]]:
    path = ROOT / "methodology/extracted/web-best-practices-20260512.md"
    content = read_text(path) if path.exists() else ""
    checks = [check("web_best_practices_doc", path.exists(), "web best-practices synthesis exists")]
    for source in REQUIRED_WEB_SOURCES:
        checks.append(check(f"web_source_{source}", source in content, f"source recorded: {source}"))
    for section in ("## What To Borrow", "## What To Reject", "## Native Artifact Influence", "## Native Skill Influence", "## Validation Rule Implied"):
        checks.append(check(f"web_doc_{section}", section in content, f"{section} present"))
    return checks


def repeated_validate(native_run: Path, passes: int) -> list[dict[str, Any]]:
    results = []
    for pass_number in range(1, passes + 1):
        checks = validate_once(native_run)
        failures = [item for item in checks if item["status"] == "fail"]
        results.append({"pass": pass_number, "status": "fail" if failures else "pass", "checks": checks})
    return results


def render_report(results: list[dict[str, Any]], native_run: Path) -> str:
    lines = [
        "# Pipeline Goal Validation",
        "",
        f"- Native run: `{native_run}`",
        f"- Repeated passes: `{len(results)}`",
        f"- Generated at: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## Pass Summary",
        "",
        "| Pass | Status | Failed Checks |",
        "| ---: | --- | ---: |",
    ]
    for result in results:
        failed = [item for item in result["checks"] if item["status"] == "fail"]
        lines.append(f"| {result['pass']} | {result['status']} | {len(failed)} |")
    lines.extend(["", "## Skill Side By Side", "", "| Skill | Status | Detail |", "| --- | --- | --- |"])
    first = results[0]["checks"]
    for item in first:
        if item["name"].startswith("skill_"):
            lines.append(f"| `{item['name'].removeprefix('skill_')}` | {item['status']} | {item['detail']} |")
    lines.extend(["", "## All Checks", ""])
    for result in results:
        lines.append(f"### Pass {result['pass']}")
        for item in result["checks"]:
            lines.append(f"- `{item['status']}` `{item['name']}`: {item['detail']}")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-run", default=str(DEFAULT_NATIVE_RUN), help="Native emulation run directory")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Report path")
    parser.add_argument("--passes", type=int, default=3, help="Repeated validation passes")
    args = parser.parse_args(argv)

    native_run = Path(args.native_run).expanduser()
    if not native_run.is_absolute():
        native_run = (ROOT / native_run).resolve()
    report = Path(args.report).expanduser()
    if not report.is_absolute():
        report = (ROOT / report).resolve()
    results = repeated_validate(native_run, args.passes)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(results, native_run), encoding="utf-8")
    failures = [item for result in results for item in result["checks"] if item["status"] == "fail"]
    print(f"report: {report}")
    print(f"passes: {args.passes}")
    print(f"failures: {len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
