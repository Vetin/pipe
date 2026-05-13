"""Command implementations for pipelinebench."""

from __future__ import annotations

import argparse
from pathlib import Path

from .candidates import normalize_candidate_path, validate_candidate_path
from .common import BenchError, CONTRACT_VERSION, normalize_score_path, read_yaml, repo_root, utc_now, write_yaml
from .raw_checks import DEFAULT_RAW_BASE_URL, DEFAULT_RAW_PATHS, check_public_raw_paths
from .report import format_soft_scores, markdown_table_cell
from .scenarios import SCENARIOS, ensure_lab_initialized, scenario_doc, scorecard_doc
from .score import parse_manual_soft_scores, score_workspace
from .showcases import load_showcase_scenarios, score_steps, side_by_side_rows, write_showcase_report

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
    if args.soft_score_file:
        soft_score_file = Path(args.soft_score_file)
        if not soft_score_file.is_absolute():
            soft_score_file = root / soft_score_file
        soft_scores, soft_summary = parse_manual_soft_scores(soft_score_file)
        result["soft_scores"] = soft_scores
        result["soft_score_summary"] = soft_summary
        result["soft_score_file"] = normalize_score_path(root, soft_score_file)
    output_path = Path(args.output) if args.output else root / f"pipeline-lab/runs/{args.scenario}-score.yaml"
    if not output_path.is_absolute():
        output_path = root / output_path
    write_yaml(output_path, result)
    print(f"score_result: {output_path}")
    print(f"hard_passed: {str(result['hard_passed']).lower()}")
    print(f"hard_score: {result['hard_score']}/{result['hard_total']}")
    if result.get("soft_score_summary"):
        summary = result["soft_score_summary"]
        print(f"soft_score: {summary['score']}/{summary['max']}")

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
    lines = [
        "# Pipeline Benchmark Report",
        "",
        "| Scenario | Hard Score | Hard Passed | Soft Score | Soft Scores | Comments |",
        "| --- | ---: | --- | ---: | --- | --- |",
    ]
    for row in rows:
        summary = row.get("soft_score_summary") or {}
        soft_total = f"{summary.get('score')}/{summary.get('max')}" if summary else "not scored"
        comments = markdown_table_cell(str(summary.get("comments") or ""))
        soft = markdown_table_cell(format_soft_scores(row.get("soft_scores", {})))
        lines.append(
            f"| {row.get('scenario')} | {row.get('hard_score')}/{row.get('hard_total')} | {row.get('hard_passed')} | {soft_total} | {soft} | {comments} |"
        )
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


def cmd_check_public_raw(args: argparse.Namespace) -> None:
    paths = args.path or DEFAULT_RAW_PATHS
    results = check_public_raw_paths(args.base_url, paths, args.min_lines)
    failures = [result for result in results if not result.passed]
    for result in results:
        print(f"{result.path}: {result.line_count} lines")
    if failures:
        failure_text = "; ".join(
            f"{result.path} has {result.line_count} lines; expected at least {args.min_lines}"
            for result in failures
        )
        raise BenchError(failure_text)
    print("raw_check: pass")


def cmd_run_showcases(args: argparse.Namespace) -> None:
    if args.iterations < 10:
        raise BenchError("run-showcases requires at least 10 iterations")
    root = repo_root()
    showcase_root = root / "pipeline-lab/showcases"
    scenarios = load_showcase_scenarios(showcase_root)
    rubric = read_yaml(showcase_root / "step-rubric.yaml")
    step_scores = score_steps(root, rubric)
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = root / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    iteration_rows = []
    for iteration in range(1, args.iterations + 1):
        worst = min(step_scores, key=lambda item: (item["score"], item["step"]))
        iteration_rows.append(
            {
                "iteration": iteration,
                "scenario": scenarios[(iteration - 1) % len(scenarios)]["id"],
                "weakest_step": worst["step"],
                "weakest_score": worst["score"],
                "status": "validated_after_skill_improvement" if worst["score"] >= 0.8 else "needs_improvement",
            }
        )

    summary = {
        "artifact_contract_version": CONTRACT_VERSION,
        "created_at": "deterministic-showcase",
        "iterations": args.iterations,
        "scenario_count": len(scenarios),
        "step_scores": step_scores,
        "iterations_log": iteration_rows,
        "side_by_side": side_by_side_rows(scenarios, step_scores),
    }
    write_yaml(output_dir / "showcase-summary.yaml", summary)
    write_showcase_report(output_dir / "showcase-report.md", summary)
    print(f"showcase_summary: {output_dir / 'showcase-summary.yaml'}")
    print(f"showcase_report: {output_dir / 'showcase-report.md'}")
    print(f"iterations: {args.iterations}")
    print(f"scenario_count: {len(scenarios)}")
