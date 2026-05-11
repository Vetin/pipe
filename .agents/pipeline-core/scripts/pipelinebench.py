#!/usr/bin/env python3
"""Offline benchmark harness for the Native Feature Pipeline."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("pipelinebench.py requires PyYAML.") from exc


CONTRACT_VERSION = "0.1.0"
SCENARIOS = {
    "auth-reset-password": {
        "required_files": ["feature.md", "architecture.md", "tech-design.md", "slices.yaml", "state.yaml", "execution.md"],
        "hard_checks": ["core_artifacts", "no_forbidden_files", "slices_have_tdd", "no_auto_implementation"],
    },
    "webhook-integration": {
        "required_files": ["feature.md", "architecture.md", "tech-design.md", "slices.yaml", "state.yaml", "execution.md"],
        "hard_checks": ["core_artifacts", "no_forbidden_files", "slices_have_tdd"],
    },
    "frontend-settings": {
        "required_files": ["feature.md", "architecture.md", "tech-design.md", "slices.yaml", "state.yaml", "execution.md"],
        "hard_checks": ["core_artifacts", "no_forbidden_files", "slices_have_tdd"],
    },
}


class BenchError(RuntimeError):
    pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pipelinebench.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_lab_parser = subparsers.add_parser("init-lab", help="create benchmark MVP files")
    init_lab_parser.set_defaults(func=cmd_init_lab)

    list_parser = subparsers.add_parser("list-scenarios", help="list benchmark scenarios")
    list_parser.set_defaults(func=cmd_list_scenarios)

    score_parser = subparsers.add_parser("score-run", help="score an existing run")
    score_parser.add_argument("--workspace", required=True)
    score_parser.add_argument("--scenario", required=True)
    score_parser.add_argument("--output")
    score_parser.add_argument("--candidate")
    score_parser.set_defaults(func=cmd_score_run)

    compare_parser = subparsers.add_parser("compare-runs", help="compare scored runs")
    compare_parser.add_argument("--left", required=True)
    compare_parser.add_argument("--right", required=True)
    compare_parser.set_defaults(func=cmd_compare_runs)

    report_parser = subparsers.add_parser("generate-report", help="generate a Markdown report from scores")
    report_parser.add_argument("--scores", nargs="+", required=True)
    report_parser.add_argument("--output", required=True)
    report_parser.set_defaults(func=cmd_generate_report)

    regression_parser = subparsers.add_parser("add-regression", help="record a regression note")
    regression_parser.add_argument("--name", required=True)
    regression_parser.add_argument("--note", required=True)
    regression_parser.set_defaults(func=cmd_add_regression)

    try:
        args = parser.parse_args(argv)
        args.func(args)
    except BenchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_init_lab(_args: argparse.Namespace) -> None:
    root = repo_root()
    for scenario, data in SCENARIOS.items():
        write_yaml(root / f"pipeline-lab/benchmarks/scenarios/{scenario}.yaml", scenario_doc(scenario, data))
    for scorecard in ("artifact-quality", "architecture-quality", "safety-and-gates"):
        write_yaml(root / f"pipeline-lab/scorecards/{scorecard}.yaml", scorecard_doc(scorecard))
    (root / "pipeline-lab/runs").mkdir(parents=True, exist_ok=True)
    print("pipeline lab initialized")


def cmd_list_scenarios(_args: argparse.Namespace) -> None:
    root = repo_root()
    ensure_lab_initialized(root)
    for path in sorted((root / "pipeline-lab/benchmarks/scenarios").glob("*.yaml")):
        data = read_yaml(path)
        print(data["scenario"])


def cmd_score_run(args: argparse.Namespace) -> None:
    root = repo_root()
    ensure_lab_initialized(root)
    workspace = Path(args.workspace)
    if not workspace.is_absolute():
        workspace = root / workspace
    scenario_path = root / f"pipeline-lab/benchmarks/scenarios/{args.scenario}.yaml"
    if not scenario_path.exists():
        raise BenchError(f"unknown scenario: {args.scenario}")
    scenario = read_yaml(scenario_path)
    if args.candidate:
        validate_candidate_path(root, Path(args.candidate))
    result = score_workspace(workspace.resolve(), scenario)
    if args.candidate:
        result["candidate"] = normalize_candidate_path(root, Path(args.candidate))
    output_path = Path(args.output) if args.output else root / f"pipeline-lab/runs/{args.scenario}-score.yaml"
    if not output_path.is_absolute():
        output_path = root / output_path
    write_yaml(output_path, result)
    print(f"score_result: {output_path}")
    print(f"hard_passed: {str(result['hard_passed']).lower()}")
    print(f"hard_score: {result['hard_score']}/{result['hard_total']}")


def cmd_compare_runs(args: argparse.Namespace) -> None:
    left = read_yaml(Path(args.left))
    right = read_yaml(Path(args.right))
    print(f"left: {left.get('scenario')} hard_score={left.get('hard_score')}/{left.get('hard_total')}")
    print(f"right: {right.get('scenario')} hard_score={right.get('hard_score')}/{right.get('hard_total')}")
    delta = int(right.get("hard_score", 0)) - int(left.get("hard_score", 0))
    print(f"hard_score_delta: {delta}")


def cmd_generate_report(args: argparse.Namespace) -> None:
    rows = [read_yaml(Path(path)) for path in args.scores]
    output = Path(args.output)
    lines = ["# Pipeline Benchmark Report", "", "| Scenario | Hard Score | Hard Passed | Soft Scores |", "| --- | ---: | --- | --- |"]
    for row in rows:
        soft = ", ".join(f"{key}: {value}" for key, value in row.get("soft_scores", {}).items())
        lines.append(f"| {row.get('scenario')} | {row.get('hard_score')}/{row.get('hard_total')} | {row.get('hard_passed')} | {soft} |")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"report: {output}")


def cmd_add_regression(args: argparse.Namespace) -> None:
    root = repo_root()
    path = root / "pipeline-lab/benchmarks/regressions.yaml"
    data = read_yaml(path) if path.exists() else {"artifact_contract_version": CONTRACT_VERSION, "regressions": []}
    data.setdefault("regressions", []).append({"name": args.name, "note": args.note, "created_at": utc_now()})
    write_yaml(path, data)
    print(f"regression_added: {args.name}")


def score_workspace(workspace: Path, scenario: dict[str, Any]) -> dict[str, Any]:
    hard_results = []
    for check in scenario.get("hard_checks", []):
        hard_results.append(run_hard_check(workspace, scenario, check))
    hard_score = sum(1 for item in hard_results if item["passed"])
    return {
        "artifact_contract_version": CONTRACT_VERSION,
        "scenario": scenario["scenario"],
        "workspace": str(workspace),
        "created_at": utc_now(),
        "hard_passed": hard_score == len(hard_results),
        "hard_score": hard_score,
        "hard_total": len(hard_results),
        "hard_results": hard_results,
        "soft_scores": {
            "requirement_quality": "not_scored_offline",
            "architecture_clarity": "not_scored_offline",
            "module_communication_quality": "not_scored_offline",
            "adr_usefulness": "not_scored_offline",
            "reuse_quality": "not_scored_offline",
            "review_quality": "not_scored_offline",
        },
    }


def run_hard_check(workspace: Path, scenario: dict[str, Any], check: str) -> dict[str, Any]:
    if check == "core_artifacts":
        missing = [rel for rel in scenario.get("required_files", []) if not (workspace / rel).exists()]
        return hard_result(check, not missing, f"missing: {', '.join(missing)}" if missing else "all required files present")
    if check == "no_forbidden_files":
        forbidden = [str(path.relative_to(workspace)) for name in ("approvals.yaml", "handoff.md") for path in workspace.rglob(name)]
        return hard_result(check, not forbidden, f"forbidden: {', '.join(forbidden)}" if forbidden else "no forbidden files")
    if check == "slices_have_tdd":
        blockers = slices_have_tdd_blockers(workspace / "slices.yaml")
        return hard_result(check, not blockers, "; ".join(blockers) if blockers else "all slices have TDD commands")
    if check == "no_auto_implementation":
        state = read_yaml(workspace / "state.yaml") if (workspace / "state.yaml").exists() else {}
        implementation_ready = (state.get("gates") or {}).get("implementation") in {"approved", "delegated", "complete"}
        return hard_result(check, not implementation_ready, "implementation gate is not auto-approved")
    if check == "state_has_no_next_skill":
        state = read_yaml(workspace / "state.yaml") if (workspace / "state.yaml").exists() else {}
        return hard_result(check, "next_skill" not in state, "state.yaml has no next_skill" if "next_skill" not in state else "state.yaml contains next_skill")
    return hard_result(check, False, "unknown hard check")


def slices_have_tdd_blockers(path: Path) -> list[str]:
    if not path.exists():
        return ["missing slices.yaml"]
    data = read_yaml(path)
    slices = data.get("slices") or []
    if isinstance(slices, dict):
        slices = list(slices.values())
    blockers = []
    for item in slices:
        if not isinstance(item, dict):
            blockers.append("slice is not a mapping")
            continue
        tdd = item.get("tdd") or {}
        for field in ("failing_test_file", "red_command", "expected_failure", "green_command"):
            if not tdd.get(field):
                blockers.append(f"{item.get('id', 'unknown')} missing tdd.{field}")
    return blockers


def hard_result(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "passed": passed, "detail": detail}


def scenario_doc(scenario: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_contract_version": CONTRACT_VERSION,
        "scenario": scenario,
        "mode": "offline",
        "required_files": data["required_files"],
        "hard_checks": data["hard_checks"],
        "soft_score_placeholders": ["requirement_quality", "architecture_clarity", "review_quality"],
    }


def scorecard_doc(scorecard: str) -> dict[str, Any]:
    return {
        "artifact_contract_version": CONTRACT_VERSION,
        "scorecard": scorecard,
        "hard_checks_required": True,
        "soft_scores": "placeholder",
    }


def validate_candidate_path(root: Path, candidate: Path) -> None:
    candidate = candidate.resolve()
    quarantine = (root / ".agents/skill-lab/quarantine").resolve()
    try:
        candidate.relative_to(quarantine)
    except ValueError as exc:
        raise BenchError("candidate must be under .agents/skill-lab/quarantine") from exc
    if candidate.name != "SKILL.candidate.md":
        raise BenchError("candidate file must be named SKILL.candidate.md")
    if not candidate.exists():
        raise BenchError(f"candidate file does not exist: {candidate}")


def normalize_candidate_path(root: Path, candidate: Path) -> str:
    candidate = candidate.resolve()
    try:
        return candidate.relative_to(root).as_posix()
    except ValueError:
        return str(candidate)


def ensure_lab_initialized(root: Path) -> None:
    if not (root / "pipeline-lab/benchmarks/scenarios/auth-reset-password.yaml").exists():
        cmd_init_lab(argparse.Namespace())


def repo_root() -> Path:
    path = Path.cwd().resolve()
    for candidate in [path, *path.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise BenchError("must be run inside a repository")


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise BenchError(f"missing YAML file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise BenchError(f"YAML file must contain a mapping: {path}")
    return loaded


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=False)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
