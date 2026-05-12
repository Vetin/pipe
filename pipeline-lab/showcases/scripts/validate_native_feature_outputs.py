#!/usr/bin/env python3
"""Validate native feature emulation outputs with repeated self-review passes."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RUN_DIR = ROOT / "pipeline-lab/showcases/native-emulation-runs/20260512-native-debug"
DEFAULT_REPORT = ROOT / "pipeline-lab/showcases/native-emulation-validation-report.md"

DIRECT_INVOCATION_TERMS = (
    "Read and follow every NFP skill doc in order",
    "nfp-00-intake",
    "nfp-12-promote",
)

REQUIRED_ARTIFACT_SECTIONS = {
    "feature": ("## Intent", "## Motivation", "## Actors", "## Goals", "## Acceptance Criteria", "## Product Risks"),
    "repo_context": ("## Candidate Files And Modules", "## Context Rule"),
    "architecture": ("## System Context", "## Component Interactions", "## Feature Topology", "```mermaid", "flowchart", "## Shared Knowledge Impact", "## Security Model", "## Failure Modes", "## Rollback Strategy", "## ADRs"),
    "tech_design": ("## Interfaces", "## Data Model", "## Test Surfaces", "## Feature Flags", "## Observability"),
    "review": ("## Scope", "## Blocking Checks", "## Findings"),
    "feature_card": ("- Source:", "- Final behavior:", "- Safety:", "## Shared Knowledge Updates", ".ai/knowledge/"),
}

DOMAIN_SIGNALS = {
    "Twenty": ("duplicate", "merge", "rollback", "audit", "confidence"),
    "Medusa": ("quote", "approval", "price", "order", "expiry"),
    "Plane": ("github", "conflict", "webhook", "stale", "audit"),
}


def read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def resolve_artifact_path(path_text: str | None) -> Path:
    if not path_text:
        return Path("")
    path = Path(path_text)
    if path.is_absolute() and path.exists():
        return path
    normalized = str(path_text)
    if normalized.startswith("/pipeline-lab/") or normalized.startswith("/.ai/") or normalized.startswith("/.agents/"):
        return ROOT / normalized.lstrip("/")
    if path.is_absolute():
        return path
    return ROOT / path


def validate_run(run_dir: Path, min_final_score: float) -> list[dict[str, Any]]:
    summary_path = run_dir / "summary.yaml"
    if not summary_path.exists():
        return [{"status": "fail", "case": "summary", "message": f"missing {summary_path}"}]
    summary = read_yaml(summary_path)
    cards = summary.get("scorecards") or []
    findings: list[dict[str, Any]] = []
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)

    if summary.get("prompt_style") != "native-user-request":
        findings.append({"status": "fail", "case": "summary", "message": "summary prompt_style must be native-user-request"})
    if summary.get("direct_skill_invocations") is not False:
        findings.append({"status": "fail", "case": "summary", "message": "summary must state direct_skill_invocations: false"})

    for card in cards:
        by_case[card.get("case", "unknown")].append(card)
        findings.extend(validate_card(card, min_final_score))

    if len(by_case) != 3:
        findings.append({"status": "fail", "case": "summary", "message": f"expected 3 best-feature cases, got {len(by_case)}"})

    for case_id, case_cards in sorted(by_case.items()):
        rounds = {int(card["round"]): card for card in case_cards}
        if set(rounds) != {1, 2, 3}:
            findings.append({"status": "fail", "case": case_id, "message": f"expected rounds 1, 2, 3; got {sorted(rounds)}"})
            continue
        scores = [float(rounds[index]["overall"]) for index in (1, 2, 3)]
        if not (scores[0] < scores[1] < scores[2]):
            findings.append({"status": "fail", "case": case_id, "message": f"scores must improve strictly, got {scores}"})
        if scores[-1] < min_final_score:
            findings.append({"status": "fail", "case": case_id, "message": f"final score {scores[-1]:.3f} below {min_final_score:.3f}"})

    if not findings:
        findings.append({"status": "pass", "case": "all", "message": "all native feature outputs passed"})
    return findings


def validate_card(card: dict[str, Any], min_final_score: float) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    case = card.get("case", "unknown")
    source = card.get("source", "unknown")
    round_number = int(card.get("round", 0))
    artifacts = card.get("artifacts") or {}

    feature_path = resolve_artifact_path(artifacts.get("feature"))
    run_dir = feature_path.parents[1] if feature_path.parts else Path(".")
    prompt_path = run_dir / "prompt.md"
    if not prompt_path.exists():
        findings.append({"status": "fail", "case": case, "message": "missing prompt.md"})
    else:
        prompt = read_text(prompt_path)
        if "normal user feature request" not in prompt:
            findings.append({"status": "fail", "case": case, "message": "prompt must identify native user request"})
        for term in DIRECT_INVOCATION_TERMS:
            if term in prompt:
                findings.append({"status": "fail", "case": case, "message": f"prompt contains direct invocation term: {term}"})

    for artifact_name, required_sections in REQUIRED_ARTIFACT_SECTIONS.items():
        path_text = artifacts.get(artifact_name)
        if not path_text:
            findings.append({"status": "fail", "case": case, "message": f"missing artifact path: {artifact_name}"})
            continue
        path = resolve_artifact_path(path_text)
        if not path.exists():
            findings.append({"status": "fail", "case": case, "message": f"artifact does not exist: {path}"})
            continue
        content = read_text(path)
        for section in required_sections:
            if section not in content:
                findings.append({"status": "fail", "case": case, "message": f"{artifact_name} missing {section}"})

    findings.extend(validate_slices(case, resolve_artifact_path(artifacts.get("slices"))))
    findings.extend(validate_evidence(case, resolve_artifact_path(artifacts.get("evidence"))))
    findings.extend(validate_domain_signals(case, source, artifacts))

    if round_number == 3 and float(card.get("overall", 0.0)) < min_final_score:
        findings.append({"status": "fail", "case": case, "message": "round 3 overall below threshold"})
    if card.get("weakest_dimension") not in (card.get("dimensions") or {}):
        findings.append({"status": "fail", "case": case, "message": "weakest_dimension must be present in dimensions"})
    return findings


def validate_slices(case: str, path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return [{"status": "fail", "case": case, "message": "missing slices.yaml"}]
    data = read_yaml(path)
    slices = data.get("slices") or []
    findings: list[dict[str, Any]] = []
    if len(slices) < 3:
        findings.append({"status": "fail", "case": case, "message": "expected at least three implementation slices"})
    for item in slices:
        slice_id = item.get("id", "unknown") if isinstance(item, dict) else "unknown"
        for field in ("requirement_ids", "red_command", "green_command", "rollback", "review_focus"):
            if not isinstance(item, dict) or not item.get(field):
                findings.append({"status": "fail", "case": case, "message": f"slice {slice_id} missing {field}"})
    return findings


def validate_evidence(case: str, path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return [{"status": "fail", "case": case, "message": "missing evidence manifest"}]
    data = read_yaml(path)
    commands = data.get("commands") or []
    findings: list[dict[str, Any]] = []
    command_names = {item.get("name") for item in commands if isinstance(item, dict)}
    for expected in ("contract-lint", "slice-red-green", "review-replay"):
        if expected not in command_names:
            findings.append({"status": "fail", "case": case, "message": f"evidence missing command {expected}"})
    if data.get("native_prompt") != "no direct internal skill invocation":
        findings.append({"status": "fail", "case": case, "message": "evidence must record native prompt constraint"})
    return findings


def validate_domain_signals(case: str, source: str, artifacts: dict[str, str]) -> list[dict[str, Any]]:
    expected = DOMAIN_SIGNALS.get(source)
    if not expected:
        return []
    corpus = ""
    for key in ("feature", "architecture", "tech_design", "review", "feature_card"):
        path_text = artifacts.get(key)
        path = resolve_artifact_path(path_text)
        if path_text and path.exists():
            corpus += "\n" + read_text(path).lower()
    return [
        {"status": "fail", "case": case, "message": f"missing domain signal: {signal}"}
        for signal in expected
        if signal not in corpus
    ]


def repeated_validate(run_dir: Path, passes: int, min_final_score: float) -> list[dict[str, Any]]:
    pass_results: list[dict[str, Any]] = []
    for pass_number in range(1, passes + 1):
        findings = validate_run(run_dir, min_final_score)
        failures = [finding for finding in findings if finding["status"] == "fail"]
        pass_results.append(
            {
                "pass": pass_number,
                "status": "fail" if failures else "pass",
                "findings": findings,
            }
        )
    return pass_results


def render_report(run_dir: Path, results: list[dict[str, Any]], min_final_score: float) -> str:
    lines = [
        "# Native Feature Output Validation",
        "",
        f"- Run directory: `{run_dir}`",
        f"- Repeated passes: `{len(results)}`",
        f"- Minimum final score: `{min_final_score:.3f}`",
        f"- Generated at: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## Pass Summary",
        "",
        "| Pass | Status | Findings |",
        "| ---: | --- | ---: |",
    ]
    for result in results:
        failures = [finding for finding in result["findings"] if finding["status"] == "fail"]
        lines.append(f"| {result['pass']} | {result['status']} | {len(failures)} |")
    lines.extend(["", "## Findings", ""])
    for result in results:
        lines.append(f"### Pass {result['pass']}")
        for finding in result["findings"]:
            lines.append(f"- `{finding['status']}` `{finding['case']}`: {finding['message']}")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", default=str(DEFAULT_RUN_DIR), help="Native emulation run directory")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Markdown report path")
    parser.add_argument("--passes", type=int, default=3, help="Number of repeated validation passes")
    parser.add_argument("--min-final-score", type=float, default=0.92, help="Minimum round-3 score")
    args = parser.parse_args(argv)

    run_dir = Path(args.run_dir).expanduser()
    if not run_dir.is_absolute():
        run_dir = (ROOT / run_dir).resolve()
    report = Path(args.report).expanduser()
    if not report.is_absolute():
        report = (ROOT / report).resolve()

    results = repeated_validate(run_dir, args.passes, args.min_final_score)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(run_dir, results, args.min_final_score), encoding="utf-8")
    failures = [finding for result in results for finding in result["findings"] if finding["status"] == "fail"]
    print(f"report: {report}")
    print(f"passes: {args.passes}")
    print(f"failures: {len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
