#!/usr/bin/env python3
"""Judge native feature-building emulation outputs.

This is a deterministic, LLM-judge-style scorer. It uses the same dimensions a
real LLM judge should consider, but keeps local validation reproducible when no
LLM credentials are configured.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REPORT = ROOT / "pipeline-lab/showcases/native-emulation-judge-report.md"
DEFAULT_OUTPUT = ROOT / "pipeline-lab/showcases/native-emulation-judge.yaml"

REQUIRED_ARTIFACT_KEYS = (
    "feature",
    "repo_context",
    "architecture",
    "tech_design",
    "slices",
    "review",
    "evidence",
    "feature_card",
)

DIRECT_SKILL_TERMS = (
    "nfp-00-intake",
    "nfp-12-promote",
    "Read and follow every NFP skill doc in order",
)

SKILL_COVERAGE_TERMS = {
    "adaptive_rigor": ("adaptive rigor", "minimal, standard, or comprehensive"),
    "ambiguity_taxonomy": ("ambiguity taxonomy", "ambiguity score"),
    "bounded_clarification": ("at most five", "blocking clarification"),
    "brownfield_reuse": ("does this already exist", "reuse map", "existing-solution"),
    "source_provenance": ("source-backed", "cited source", "claim provenance"),
    "task_graph": ("critical path", "complexity", "conflict risk", "file ownership"),
    "tdd_law": ("red evidence", "failing test", "green evidence"),
    "adversarial_review": ("adversarial review", "hard findings", "soft concerns"),
    "verification_debt": ("verification debt", "completion claim"),
    "eval_metrics": ("run id", "scorecard", "baseline-vs-after", "judge dimensions"),
}


@dataclass(frozen=True)
class CaseJudgment:
    case: str
    source: str
    feature: str
    round: int
    overall: float
    dimensions: dict[str, float]
    hard_failures: list[str]
    weakest_dimension: str
    high_quality: bool


def read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def read_text(path: Path | str | None) -> str:
    if not path:
        return ""
    candidate = Path(path)
    if not candidate.exists():
        return ""
    return candidate.read_text(encoding="utf-8", errors="replace")


def score_terms(text: str, terms: tuple[str, ...]) -> float:
    if not terms:
        return 1.0
    lowered = text.lower()
    hits = sum(1 for term in terms if term.lower() in lowered)
    return round(hits / len(terms), 3)


def bool_score(condition: bool) -> float:
    return 1.0 if condition else 0.0


def artifact_path(card: dict[str, Any], key: str) -> Path | None:
    value = (card.get("artifacts") or {}).get(key)
    return Path(value) if value else None


def prompt_for_card(card: dict[str, Any]) -> str:
    feature_path = artifact_path(card, "feature")
    if not feature_path:
        return ""
    return read_text(feature_path.parents[1] / "prompt.md")


def latest_cards(summary: dict[str, Any]) -> list[dict[str, Any]]:
    by_case: dict[str, dict[str, Any]] = {}
    for card in summary.get("scorecards") or []:
        case = card.get("case", "")
        if not case:
            continue
        if case not in by_case or int(card.get("round", 0)) > int(by_case[case].get("round", 0)):
            by_case[case] = card
    return list(by_case.values())


def judge_card(card: dict[str, Any]) -> CaseJudgment:
    artifacts = card.get("artifacts") or {}
    hard_failures: list[str] = []
    missing = [key for key in REQUIRED_ARTIFACT_KEYS if not artifacts.get(key) or not Path(artifacts[key]).exists()]
    if missing:
        hard_failures.append("missing artifacts: " + ", ".join(missing))

    prompt = prompt_for_card(card)
    if any(term in prompt for term in DIRECT_SKILL_TERMS):
        hard_failures.append("prompt directly invokes internal skill sequence")

    feature = read_text(artifact_path(card, "feature"))
    repo_context = read_text(artifact_path(card, "repo_context"))
    architecture = read_text(artifact_path(card, "architecture"))
    tech_design = read_text(artifact_path(card, "tech_design"))
    slices = read_text(artifact_path(card, "slices"))
    review = read_text(artifact_path(card, "review"))
    verification_review = read_text(artifact_path(card, "verification_review"))
    evidence = read_text(artifact_path(card, "evidence"))
    final_output = read_text(artifact_path(card, "final_verification_output"))
    feature_card = read_text(artifact_path(card, "feature_card"))

    dimensions = {
        "native_prompt_integrity": bool_score("normal user feature request" in prompt and not hard_failures),
        "artifact_completeness": round((len(REQUIRED_ARTIFACT_KEYS) - len(missing)) / len(REQUIRED_ARTIFACT_KEYS), 3),
        "contract_clarity": score_terms(
            feature,
            (
                "FR-",
                "AC-",
                "Non-Goals",
                "Non-Functional Requirements",
                "Product Risks",
                "Ambiguity Score",
                "Clarification Ledger",
                "Related Existing Features",
                "Source-Backed Reuse Map",
                "Open Questions",
            ),
        ),
        "repo_context_research": max(
            score_terms(
                repo_context,
                (
                    "Candidate Files",
                    "Existing-Solution Reuse Map",
                    "Source-Backed Facts",
                    "Hypotheses To Verify",
                    "inspect",
                    "source",
                ),
            ),
            score_terms(feature, ("Related", "existing", "reuse", "Source-Backed")),
        ),
        "architecture_design": score_terms(
            architecture + "\n" + tech_design,
            (
                "Change Delta",
                "Security",
                "Failure",
                "Rollback",
                "Migration Strategy",
                "ADR",
                "Alternatives Considered",
                "Completeness Correctness Coherence",
                "Dependency And Ownership Plan",
                "critical path",
                "Decision Traceability",
                "Observability",
                "Data Model",
            ),
        ),
        "slicing_tdd": score_terms(
            slices,
            (
                "requirement",
                "complexity",
                "critical_path",
                "parallelizable",
                "file_ownership",
                "conflict_risk",
                "dependency_notes",
                "test_strategy",
                "red_command",
                "green_command",
                "rollback",
                "review_focus",
            ),
        ),
        "review_evidence": score_terms(
            review + "\n" + verification_review + "\n" + evidence + "\n" + final_output + "\n" + feature_card,
            (
                "Blocking",
                "Hard Findings",
                "Soft Concerns",
                "Zero-Finding Justification",
                "Manual Validation",
                "Verification Debt",
                "Claim Provenance",
                "Rollback Guidance",
                "source_revision",
                "final-verification-output",
                "evidence",
                "commands",
                "judge_dimensions",
                "promotion",
                "verification",
            ),
        ),
    }
    overall = round(mean(dimensions.values()), 3)
    weakest = min(dimensions, key=dimensions.get)
    return CaseJudgment(
        case=str(card.get("case", "")),
        source=str(card.get("source", "")),
        feature=str(card.get("feature", "")),
        round=int(card.get("round", 0)),
        overall=overall,
        dimensions=dimensions,
        hard_failures=hard_failures,
        weakest_dimension=weakest,
        high_quality=overall >= 0.86 and not hard_failures,
    )


def methodology_coverage(skill_root: Path, reference_root: Path) -> dict[str, Any]:
    paths = list(skill_root.glob("*/SKILL.md")) + [reference_root / "methodology-lenses.md"]
    corpus = "\n".join(read_text(path) for path in paths if path.exists())
    dimensions = {
        name: score_terms(corpus, terms)
        for name, terms in SKILL_COVERAGE_TERMS.items()
    }
    missing = [name for name, score in dimensions.items() if score < 0.5]
    return {
        "overall": round(mean(dimensions.values()), 3),
        "dimensions": dimensions,
        "missing_or_weak": missing,
        "scanned_files": [str(path) for path in paths if path.exists()],
    }


def judge_summary(summary_path: Path, skill_root: Path, reference_root: Path) -> dict[str, Any]:
    summary = read_yaml(summary_path)
    case_judgments = [judge_card(card) for card in latest_cards(summary)]
    coverage = methodology_coverage(skill_root, reference_root)
    case_average = round(mean([case.overall for case in case_judgments]), 3) if case_judgments else 0.0
    hard_failures = [failure for case in case_judgments for failure in case.hard_failures]
    overall = round(mean([case_average, coverage["overall"]]), 3)
    return {
        "summary_path": str(summary_path),
        "run_id": summary.get("run_id", summary_path.parent.name),
        "judge_mode": "deterministic-llm-style",
        "case_average": case_average,
        "methodology_coverage": coverage,
        "overall": overall,
        "high_quality": overall >= 0.86 and not hard_failures,
        "hard_failures": hard_failures,
        "cases": [
            {
                "case": case.case,
                "source": case.source,
                "feature": case.feature,
                "round": case.round,
                "overall": case.overall,
                "weakest_dimension": case.weakest_dimension,
                "high_quality": case.high_quality,
                "hard_failures": case.hard_failures,
                "dimensions": case.dimensions,
            }
            for case in case_judgments
        ],
    }


def render_report(results: dict[str, Any]) -> str:
    lines = [
        "# Native Feature Build Judge Report",
        "",
        f"- Judge mode: `{results['judge_mode']}`",
        f"- Generated at: `{results['generated_at']}`",
        "",
        "## Run Comparison",
        "",
        "| Run | Case Avg | Methodology Coverage | Overall | Status | Hard Failures |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for run in results["runs"]:
        lines.append(
            f"| `{run['run_id']}` | {run['case_average']:.3f} | "
            f"{run['methodology_coverage']['overall']:.3f} | {run['overall']:.3f} | "
            f"{'high quality' if run['high_quality'] else 'needs work'} | "
            f"{len(run['hard_failures'])} |"
        )

    lines.extend(["", "## Case Scores", "", "| Run | Feature | Score | Weakest | Status |", "| --- | --- | ---: | --- | --- |"])
    for run in results["runs"]:
        for case in run["cases"]:
            lines.append(
                f"| `{run['run_id']}` | {case['source']} - {case['feature']} | "
                f"{case['overall']:.3f} | {case['weakest_dimension']} | "
                f"{'high quality' if case['high_quality'] else 'needs work'} |"
            )

    lines.extend(["", "## Methodology Coverage", "", "| Run | Weak Dimensions |", "| --- | --- |"])
    for run in results["runs"]:
        weak = ", ".join(run["methodology_coverage"]["missing_or_weak"]) or "none"
        lines.append(f"| `{run['run_id']}` | {weak} |")

    if results["runs"]:
        baseline = results["runs"][0]
        latest = results["runs"][-1]
        delta = latest["overall"] - baseline["overall"]
        lines.extend(
            [
                "",
                "## Baseline Delta",
                "",
                f"- Baseline run: `{baseline['run_id']}` overall `{baseline['overall']:.3f}`",
                f"- Latest run: `{latest['run_id']}` overall `{latest['overall']:.3f}`",
                f"- Delta: `{delta:+.3f}`",
            ]
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="append", required=True, help="summary.yaml path; repeat for comparisons")
    parser.add_argument("--skill-root", default=str(ROOT / ".agents/skills"))
    parser.add_argument("--reference-root", default=str(ROOT / ".agents/pipeline-core/references"))
    parser.add_argument("--output-md", default=str(DEFAULT_REPORT))
    parser.add_argument("--output-yaml", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)

    skill_root = Path(args.skill_root).resolve()
    reference_root = Path(args.reference_root).resolve()
    summaries = [Path(item).resolve() for item in args.summary]
    runs = [judge_summary(path, skill_root, reference_root) for path in summaries]
    results = {
        "artifact_contract_version": "0.1.0",
        "judge_mode": "deterministic-llm-style",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runs": runs,
    }

    output_yaml = Path(args.output_yaml).resolve()
    output_md = Path(args.output_md).resolve()
    output_yaml.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_yaml.write_text(yaml.safe_dump(results, sort_keys=False), encoding="utf-8")
    output_md.write_text(render_report(results), encoding="utf-8")
    print(f"judge_report: {output_md}")
    print(f"judge_yaml: {output_yaml}")
    print(f"latest_overall: {runs[-1]['overall']:.3f}")
    return 0 if runs[-1]["high_quality"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
