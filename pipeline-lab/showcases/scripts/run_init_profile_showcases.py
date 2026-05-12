#!/usr/bin/env python3
"""Run project-init profiling across configured showcase repositories."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[3]
FEATURECTL = ROOT / ".agents/pipeline-core/scripts/featurectl.py"
DEFAULT_CASES = ROOT / "pipeline-lab/showcases/codex-e2e-cases.yaml"
DEFAULT_OUTPUT_DIR = ROOT / "pipeline-lab/showcases/init-profile-runs"
DEFAULT_REPORT = ROOT / "pipeline-lab/showcases/init-profile-report.md"


def read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def resolve_path(value: str, base: Path = ROOT) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (base / path).resolve()
    return path


def load_cases(path: Path) -> list[dict[str, Any]]:
    config = read_yaml(path)
    cases = []
    for key, item in sorted((config.get("cases") or {}).items()):
        repo_path = resolve_path(str((item.get("original_codebase") or {}).get("repo_path") or ""))
        cases.append(
            {
                "key": key,
                "title": item.get("title", key),
                "repo_path": repo_path,
                "feature_request": item.get("feature_request", ""),
                "expected_result": item.get("expected_result", ""),
            }
        )
    return cases


def run_profile(case: dict[str, Any], pass_number: int) -> dict[str, Any]:
    repo_path = Path(case["repo_path"])
    result: dict[str, Any] = {
        "case": case["key"],
        "title": case["title"],
        "repo_path": str(repo_path),
        "pass": pass_number,
        "status": "fail",
        "command": f"{sys.executable} {FEATURECTL} init --profile-project",
        "duration_seconds": 0.0,
        "counts": {},
        "feature_catalog_count": 0,
        "feature_signals_count": 0,
        "top_features": [],
        "knowledge_paths": [],
        "failure": "",
    }
    if not repo_path.exists():
        result["failure"] = f"missing repository path: {repo_path}"
        return result
    if not (repo_path / ".git").exists():
        result["failure"] = f"not a git repository: {repo_path}"
        return result

    started = time.monotonic()
    completed = subprocess.run(
        [sys.executable, str(FEATURECTL), "init", "--profile-project"],
        cwd=repo_path,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
    )
    result["duration_seconds"] = round(time.monotonic() - started, 3)
    result["stdout_tail"] = "\n".join(completed.stdout.splitlines()[-8:])
    result["stderr_tail"] = "\n".join(completed.stderr.splitlines()[-8:])
    if completed.returncode != 0:
        result["failure"] = f"featurectl exited {completed.returncode}"
        return result

    index_path = repo_path / ".ai/knowledge/project-index.yaml"
    discovered_path = repo_path / ".ai/knowledge/discovered-signals.md"
    if not index_path.exists():
        result["failure"] = "missing .ai/knowledge/project-index.yaml after init"
        return result
    if not discovered_path.exists():
        result["failure"] = "missing .ai/knowledge/discovered-signals.md after init"
        return result
    profile = read_yaml(index_path)
    discovered = parse_discovered_signals(discovered_path)
    counts = profile.get("counts") or {}
    result["project"] = profile.get("project") or {}
    result["counts"] = counts
    result["feature_catalog_count"] = len(discovered["catalog"])
    result["feature_signals_count"] = discovered["signal_count"]
    result["top_features"] = discovered["catalog"][:8]
    result["knowledge_paths"] = [
        ".ai/knowledge/project-index.yaml",
        ".ai/knowledge/project-snapshot.md",
        ".ai/knowledge/features-overview.md",
        ".ai/knowledge/discovered-signals.md",
        ".ai/knowledge/module-map.md",
        ".ai/knowledge/testing-overview.md",
        ".ai/knowledge/contracts-overview.md",
        ".ai/knowledge/integration-map.md",
    ]

    blockers = result_blockers(result)
    if blockers:
        result["failure"] = "; ".join(blockers)
        return result
    result["status"] = "pass"
    return result


def parse_discovered_signals(path: Path) -> dict[str, Any]:
    content = path.read_text(encoding="utf-8")
    catalog: list[str] = []
    for line in content.splitlines():
        if line.startswith("### "):
            name = line.removeprefix("### ").strip()
            if name:
                catalog.append(name)
    return {
        "catalog": catalog,
        "signal_count": content.count("[lab_signal]")
        + content.count("[doc_signal]")
        + content.count("[source_signal]")
        + content.count("[test_signal]"),
    }


def result_blockers(result: dict[str, Any]) -> list[str]:
    counts = result.get("counts") or {}
    blockers = []
    if int(counts.get("profiled_files") or 0) <= 0:
        blockers.append("no profiled files")
    if int(counts.get("source_files") or 0) <= 0 and int(counts.get("doc_files") or 0) <= 0:
        blockers.append("no source or documentation files")
    if int(result.get("feature_catalog_count") or 0) <= 0:
        blockers.append("empty feature catalog")
    return blockers


def compare_results(results: list[dict[str, Any]], passes: int) -> list[dict[str, Any]]:
    comparisons: list[dict[str, Any]] = []
    by_case: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        by_case.setdefault(result["case"], []).append(result)
    for case, case_results in sorted(by_case.items()):
        case_results = sorted(case_results, key=lambda item: int(item["pass"]))
        metrics = [metric_signature(item) for item in case_results]
        stable = len(metrics) == passes and len({tuple(sorted(metric.items())) for metric in metrics}) == 1
        comparisons.append(
            {
                "case": case,
                "status": "pass" if all(item["status"] == "pass" for item in case_results) and stable else "fail",
                "passes_seen": [item["pass"] for item in case_results],
                "stable_metrics": stable,
                "metrics": metrics,
                "top_features_by_pass": {item["pass"]: item.get("top_features", []) for item in case_results},
            }
        )
    return comparisons


def metric_signature(result: dict[str, Any]) -> dict[str, int]:
    counts = result.get("counts") or {}
    return {
        "profiled_files": int(counts.get("profiled_files") or 0),
        "source_files": int(counts.get("source_files") or 0),
        "test_files": int(counts.get("test_files") or 0),
        "doc_files": int(counts.get("doc_files") or 0),
        "contract_files": int(counts.get("contract_files") or 0),
        "integration_files": int(counts.get("integration_files") or 0),
        "feature_catalog": int(result.get("feature_catalog_count") or 0),
        "feature_signals": int(result.get("feature_signals_count") or 0),
    }


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Init Profile Showcase Validation",
        "",
        f"- Run id: `{summary['run_id']}`",
        f"- Repeated passes: `{summary['passes']}`",
        f"- Cases: `{len(summary['cases'])}`",
        f"- Generated at: `{summary['generated_at']}`",
        "",
        "## Pass Summary",
        "",
        "| Repository | Pass | Status | Source | Tests | Docs | Features | Failure |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for result in summary["results"]:
        counts = result.get("counts") or {}
        lines.append(
            f"| `{result['case']}` | {result['pass']} | {result['status']} | "
            f"{counts.get('source_files', 0)} | {counts.get('test_files', 0)} | "
            f"{counts.get('doc_files', 0)} | {result.get('feature_catalog_count', 0)} | "
            f"{result.get('failure') or 'none'} |"
        )

    lines.extend(["", "## Side By Side", "", "| Repository | Stable | Pass 1 | Pass 2 | Pass 3 | Top Feature Signals |", "| --- | --- | --- | --- | --- | --- |"])
    for comparison in summary["comparisons"]:
        metrics_by_pass = {index + 1: metrics for index, metrics in enumerate(comparison.get("metrics") or [])}
        top_features = comparison.get("top_features_by_pass", {}).get(1, [])
        lines.append(
            f"| `{comparison['case']}` | {comparison['stable_metrics']} | "
            f"{compact_metrics(metrics_by_pass.get(1, {}))} | "
            f"{compact_metrics(metrics_by_pass.get(2, {}))} | "
            f"{compact_metrics(metrics_by_pass.get(3, {}))} | "
            f"{', '.join(top_features[:5]) or 'none'} |"
        )

    failures = summary.get("failures") or []
    lines.extend(["", "## Validation Findings", ""])
    if failures:
        for failure in failures:
            lines.append(f"- `{failure['case']}` pass `{failure.get('pass', 'all')}`: {failure['failure']}")
    else:
        lines.append("- All init profile passes produced stable source-backed knowledge and non-empty feature catalogs.")

    lines.extend(
        [
            "",
            "## Reuse In Feature Pipeline",
            "",
            "- Use `project-init` before feature planning when `.ai/knowledge` is missing, stale, or generic.",
            "- Treat `feature_catalog` and `Current Feature Picture` as source maps, then verify cited files in `nfp-01-context`.",
            "- The repeated side-by-side pass catches unstable project indexing before a feature pipeline run depends on it.",
        ]
    )
    return "\n".join(lines)


def compact_metrics(metrics: dict[str, int]) -> str:
    if not metrics:
        return "missing"
    return (
        f"src={metrics.get('source_files', 0)}, "
        f"test={metrics.get('test_files', 0)}, "
        f"doc={metrics.get('doc_files', 0)}, "
        f"features={metrics.get('feature_catalog', 0)}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="Showcase cases YAML")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Latest markdown report")
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S-init-profile"), help="Run id")
    parser.add_argument("--passes", type=int, default=3, help="Repeated passes per repository")
    parser.add_argument("--clean", action="store_true", help="Remove existing run directory first")
    args = parser.parse_args(argv)

    cases_path = resolve_path(args.cases)
    output_dir = resolve_path(args.output_dir)
    report_path = resolve_path(args.report)
    run_dir = output_dir / args.run_id
    if args.clean and run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    cases = load_cases(cases_path)
    results = []
    for pass_number in range(1, args.passes + 1):
        for case in cases:
            results.append(run_profile(case, pass_number))
    comparisons = compare_results(results, args.passes)
    failures = [
        {"case": item["case"], "pass": item["pass"], "failure": item.get("failure", "failed")}
        for item in results
        if item["status"] != "pass"
    ]
    failures.extend(
        {"case": item["case"], "pass": "comparison", "failure": "metrics changed across repeated passes"}
        for item in comparisons
        if item["status"] != "pass"
    )

    summary = {
        "artifact_contract_version": "0.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "run_init_profile_showcases.py",
        "run_id": args.run_id,
        "passes": args.passes,
        "cases": [{"key": item["key"], "title": item["title"], "repo_path": str(item["repo_path"])} for item in cases],
        "results": results,
        "comparisons": comparisons,
        "failures": failures,
    }
    write_yaml(run_dir / "summary.yaml", summary)
    report = render_report(summary)
    (run_dir / "report.md").write_text(report, encoding="utf-8")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(f"run_id: {args.run_id}")
    print(f"report: {report_path}")
    print(f"summary: {run_dir / 'summary.yaml'}")
    print(f"passes: {args.passes}")
    print(f"failures: {len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
