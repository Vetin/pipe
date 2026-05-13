#!/usr/bin/env python3
"""Command parser for the Native Feature Pipeline benchmark harness."""

from __future__ import annotations

import argparse
import sys

from .commands import (
    cmd_add_regression,
    cmd_compare_runs,
    cmd_generate_report,
    cmd_init_lab,
    cmd_list_scenarios,
    cmd_run_showcases,
    cmd_score_run,
)
from .common import BenchError

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
    score_parser.add_argument("--soft-score-file")
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

    showcase_parser = subparsers.add_parser("run-showcases", help="score 10 showcase scenarios side by side")
    showcase_parser.add_argument("--output-dir", required=True)
    showcase_parser.add_argument("--iterations", type=int, default=10)
    showcase_parser.set_defaults(func=cmd_run_showcases)

    try:
        args = parser.parse_args(argv)
        args.func(args)
    except BenchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0
