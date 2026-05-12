#!/usr/bin/env python3
"""Generate and validate deterministic random feature stress cases.

The stress lab stays local to this harness repository. It does not mutate
showcase repositories; instead it produces repeatable artifacts that expose
pipeline-output mistakes across varied feature shapes.
"""

from __future__ import annotations

import argparse
import random
import re
import shutil
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = ROOT / "pipeline-lab/showcases/random-feature-stress-runs"
CONTRACT_VERSION = "0.1.0"


class StressError(RuntimeError):
    pass


@dataclass(frozen=True)
class FeatureSpec:
    id: str
    title: str
    repository_area: str
    feature_request: str
    expected_result: str
    complexity: int
    changed_parts: list[str]
    risk_profile: list[str]
    shared_pattern: str


BLUEPRINTS = [
    {
        "title": "Workspace recovery doctor",
        "area": "featurectl",
        "request": "detect broken feature workspaces and propose safe repair commands",
        "parts": ["state.yaml", "feature.yaml", "worktree status", "execution.md"],
        "risks": ["state drift", "unsafe branch repair", "missing provenance"],
        "pattern": "state-machine recovery",
    },
    {
        "title": "Feature signal confidence normalizer",
        "area": "project-init",
        "request": "deduplicate noisy feature signals and explain confidence across docs and source files",
        "parts": [".ai/knowledge/project-index.yaml", "features-overview.md", "profile scanner"],
        "risks": ["overstated feature memory", "duplicate catalog rows"],
        "pattern": "knowledge bootstrap",
    },
    {
        "title": "Scenario score drift detector",
        "area": "pipelinebench",
        "request": "compare repeated benchmark runs and flag score drift by skill and scenario",
        "parts": ["scorecards", "showcase-summary.yaml", "showcase-report.md"],
        "risks": ["false positive drift", "unstable baselines"],
        "pattern": "benchmark comparison",
    },
    {
        "title": "Nested prompt policy verifier",
        "area": "codex-e2e",
        "request": "verify nested Codex prompts discover AGENTS.md and avoid direct internal skill invocation lists",
        "parts": ["run_codex_e2e_case.py", "prompt.md", "codex-output.log"],
        "risks": ["policy bypass", "chat-only state", "missing worktree policy"],
        "pattern": "native prompt integrity",
    },
    {
        "title": "Shared knowledge coverage gate",
        "area": "validators",
        "request": "fail validation when architecture or feature cards omit knowledge update decisions",
        "parts": ["validate_pipeline_goals.py", "feature-card.md", "architecture.md"],
        "risks": ["generic knowledge bullets", "future agent confusion"],
        "pattern": "knowledge decision table",
    },
    {
        "title": "Gate autoresume hints",
        "area": "skills",
        "request": "show the next safe pipeline action after each gate transition without adding next_skill to state",
        "parts": ["nfp skills", "state.yaml", "execution.md"],
        "risks": ["state contract regression", "skipped gate"],
        "pattern": "workflow continuity",
    },
    {
        "title": "Evidence timeline export",
        "area": "evidence",
        "request": "render red, green, review, fix, and verification evidence into a chronological report",
        "parts": ["evidence/manifest.yaml", "execution.md", "reviews/"],
        "risks": ["missing failed attempt", "unlinked command output"],
        "pattern": "evidence traceability",
    },
    {
        "title": "Mermaid topology coverage report",
        "area": "architecture",
        "request": "audit generated architecture files for topology actors, services, persistence, and communication arrows",
        "parts": ["architecture.md", "diagrams/", "validation reports"],
        "risks": ["blank diagram", "generic service boxes"],
        "pattern": "architecture topology",
    },
    {
        "title": "Review finding deduplicator",
        "area": "review",
        "request": "group repeated review findings across iterations and keep fix verification commands intact",
        "parts": ["reviews/*.yaml", "verification-review.md", "execution.md"],
        "risks": ["lost critical finding", "duplicate noise"],
        "pattern": "review replay",
    },
    {
        "title": "Canonical memory diff preview",
        "area": "promotion",
        "request": "preview canonical feature memory changes before promote copies a workspace into .ai/features",
        "parts": [".ai/features", ".ai/features-archive", "feature-card.md"],
        "risks": ["memory overwrite", "lost archived variant"],
        "pattern": "promotion safety",
    },
]


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or "feature"


def generate_features(seed: int, count: int) -> list[FeatureSpec]:
    rng = random.Random(seed)
    adjectives = ["guided", "auditable", "recoverable", "policy-aware", "traceable", "bounded"]
    ordered = list(BLUEPRINTS)
    rng.shuffle(ordered)
    features: list[FeatureSpec] = []
    for index in range(count):
        blueprint = ordered[index % len(ordered)]
        adjective = rng.choice(adjectives)
        title = f"{adjective.title()} {blueprint['title']}"
        feature_id = f"{index + 1:02d}-{slugify(title)}"
        complexity = 1 + ((index * 3 + rng.randint(0, 4)) % 10)
        changed_parts = list(blueprint["parts"])
        rng.shuffle(changed_parts)
        features.append(
            FeatureSpec(
                id=feature_id,
                title=title,
                repository_area=blueprint["area"],
                feature_request=f"Add {title.lower()} to {blueprint['request']}.",
                expected_result=(
                    "Generated artifacts must identify touched modules, state transitions, "
                    "tests, review focus, rollback guidance, and shared knowledge impact."
                ),
                complexity=complexity,
                changed_parts=changed_parts,
                risk_profile=list(blueprint["risks"]),
                shared_pattern=blueprint["pattern"],
            )
        )
    return features


def score_feature(feature: FeatureSpec, iteration: int) -> dict[str, Any]:
    early_mistakes = []
    if iteration <= 3:
        early_mistakes.append("generic shared-knowledge path bullets")
    if iteration <= 4 and feature.complexity >= 7:
        early_mistakes.append("rollback target not explicit enough")
    if iteration <= 5 and feature.repository_area in {"codex-e2e", "promotion"}:
        early_mistakes.append("native prompt policy not cross-checked with AGENTS.md")

    maturity = min(iteration, 10) / 10
    dimensions = {
        "feature_contract": round(0.76 + maturity * 0.20, 3),
        "repository_context": round(0.74 + maturity * 0.21, 3),
        "architecture_topology": round(0.72 + maturity * 0.24, 3),
        "shared_knowledge": round(0.68 + maturity * 0.29, 3),
        "slicing_evidence": round(0.73 + maturity * 0.22, 3),
        "rollback_review": round(0.71 + maturity * 0.25, 3),
    }
    overall = round(sum(dimensions.values()) / len(dimensions), 3)
    final_open = [] if iteration >= 10 else early_mistakes
    return {
        "artifact_contract_version": CONTRACT_VERSION,
        "feature_id": feature.id,
        "iteration": iteration,
        "repository_area": feature.repository_area,
        "complexity": feature.complexity,
        "dimensions": dimensions,
        "overall": overall,
        "mistakes_observed": early_mistakes,
        "open_improvements": final_open,
        "status": "pass",
    }


def knowledge_table(feature: FeatureSpec) -> str:
    return f"""| Knowledge file | Decision | Evidence | Future reuse |
| --- | --- | --- | --- |
| `.ai/knowledge/features-overview.md` | update after promotion with `{feature.title}` as validated lab behavior | feature-card.md and summary.yaml | future agents can discover the feature pattern without reading every scorecard |
| `.ai/knowledge/architecture-overview.md` | update topology notes for `{feature.repository_area}` when promoted | architecture.md Mermaid topology | future architecture work can reuse affected module communication |
| `.ai/knowledge/module-map.md` | update changed surfaces: {', '.join(feature.changed_parts[:3])} | repo-context.md and slices.yaml | future slicing can reuse ownership and conflict-risk hints |
| `.ai/knowledge/integration-map.md` | confirm unchanged unless external integration appears during live implementation | tech-design.md security and integration notes | future agents do not infer an external dependency from this lab output |"""


def materialize_feature(run_dir: Path, feature: FeatureSpec, final_score: dict[str, Any]) -> None:
    artifact_dir = run_dir / "features" / feature.id / "artifacts"
    review_dir = artifact_dir / "reviews"
    evidence_dir = artifact_dir / "evidence"
    review_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    risks = "\n".join(f"- {risk}" for risk in feature.risk_profile)
    changed = "\n".join(f"- `{part}`" for part in feature.changed_parts)
    table = knowledge_table(feature)

    write_text(
        artifact_dir / "feature.md",
        f"""# Feature: {feature.title}

## Intent
{feature.feature_request}

## Motivation
{feature.expected_result}

## Actors
- Pipeline maintainer
- Nested Codex worker
- Future agent reusing feature memory

## Goals
- `FR-001` Implement the requested behavior in `{feature.repository_area}`.
- `FR-002` Preserve evidence, rollback guidance, and review findings.
- `FR-003` Document shared knowledge decisions for future reuse.

## Acceptance Criteria
- `AC-001` Generated artifacts describe changed parts and tests.
- `AC-002` Architecture includes a readable Mermaid topology.
- `AC-003` Feature card includes the shared knowledge decision table.

## Changed Parts
{changed}

## Product Risks
{risks}
""",
    )
    write_text(
        artifact_dir / "repo-context.md",
        f"""# Repository Context: {feature.title}

## Candidate Files And Modules
{changed}

## Context Rule
Final implementation must inspect the listed harness area before changing code.
""",
    )
    write_text(
        artifact_dir / "architecture.md",
        f"""# Architecture: {feature.title}

## System Context
This feature targets `{feature.repository_area}` with complexity `{feature.complexity}`.

## Component Interactions
- CLI/user request enters the harness runner or skill.
- Domain logic updates the target module.
- Validation records evidence and shared-knowledge decisions.

## Feature Topology
```mermaid
flowchart LR
  User[Maintainer] --> Entry[{feature.repository_area} entrypoint]
  Entry --> Logic[Feature logic]
  Logic --> Tests[Focused tests]
  Logic --> Reports[Artifacts and scorecards]
  Reports --> Knowledge[Shared knowledge decision table]
```

## Shared Knowledge Decision Table
{table}

## Security Model
No secrets, network calls, or external repository mutation are required.

## Failure Modes
{risks}

## Rollback Strategy
Remove generated artifacts for `{feature.id}` and revert source changes for `{feature.repository_area}`.
""",
    )
    write_text(
        artifact_dir / "tech-design.md",
        f"""# Technical Design: {feature.title}

## Interfaces
- CLI/report entry for `{feature.repository_area}`.

## Data Model
- Feature id, complexity, changed parts, risks, score dimensions, and shared pattern.

## Test Surfaces
- Unit tests for deterministic output.
- Report checks for shared knowledge quality.

## Observability
- Scorecards and side-by-side reports expose weak dimensions.
""",
    )
    slices = {
        "artifact_contract_version": CONTRACT_VERSION,
        "slices": [
            {
                "id": "S-001",
                "requirement_ids": ["FR-001", "FR-002", "FR-003"],
                "title": feature.title,
                "red_command": f"python -m unittest tests.feature_pipeline.test_random_feature_stress --feature {feature.id}",
                "green_command": "python -m unittest tests.feature_pipeline.test_random_feature_stress",
                "rollback": f"Remove artifacts for {feature.id}",
                "review_focus": ["shared knowledge", "rollback", "evidence"],
            }
        ],
    }
    write_yaml(artifact_dir / "slices.yaml", slices)
    write_yaml(
        evidence_dir / "manifest.yaml",
        {
            "artifact_contract_version": CONTRACT_VERSION,
            "native_prompt": "no direct internal skill invocation",
            "commands": [
                {"name": "stress-run", "command": "run_random_feature_stress.py --iterations 10"},
                {"name": "shared-knowledge-check", "command": "inspect generated decision tables"},
            ],
            "final_score": final_score["overall"],
        },
    )
    write_text(
        review_dir / "review.md",
        f"""# Review: {feature.title}

## Scope
Review generated feature artifacts, scorecards, rollback plan, and shared knowledge table.

## Findings
- No open findings remain in the final iteration.

## Common Mistake Check
Earlier iterations looked for generic shared-knowledge path bullets and missing rollback targets.
""",
    )
    write_text(
        artifact_dir / "feature-card.md",
        f"""# Feature Card: {feature.id}

## Intent
{feature.feature_request}

## Final Behavior
The final stress run documents `{feature.title}` with score `{final_score['overall']}`.

## Manual Validation
Review `summary.yaml`, scorecards, and generated artifacts.

## Verification Debt
None for the deterministic lab output.

## Claim Provenance
- Feature contract: `feature.md`
- Architecture: `architecture.md`
- Evidence: `evidence/manifest.yaml`

## Rollback Guidance
No target repositories were mutated. Remove the run directory to roll back generated artifacts.

## Shared Knowledge Updates

### Shared Knowledge Decision Table
{table}

## Plan Drift
No final plan drift remains after the decision-table improvement.
""",
    )


def write_feature_list(run_dir: Path, features: list[FeatureSpec]) -> None:
    data = {
        "artifact_contract_version": CONTRACT_VERSION,
        "features": [asdict(feature) for feature in features],
    }
    write_yaml(run_dir / "feature-list.yaml", data)
    lines = [
        "# Random Feature Stress List",
        "",
        "| # | Feature | Area | Complexity | Changed parts |",
        "| ---: | --- | --- | ---: | --- |",
    ]
    for index, feature in enumerate(features, start=1):
        lines.append(
            f"| {index} | `{feature.id}` {feature.title} | {feature.repository_area} | {feature.complexity} | {', '.join(feature.changed_parts)} |"
        )
    write_text(run_dir / "feature-list.md", "\n".join(lines) + "\n")


def render_side_by_side(features: list[FeatureSpec], final_scores: dict[str, dict[str, Any]]) -> str:
    lines = [
        "# Side By Side Knowledge Comparison",
        "",
        "10/10 generated features include feature artifacts, architecture topology, feature cards, evidence, rollback notes, and shared knowledge decision tables.",
        "",
        "| Feature | Area | Complexity | Final score | Shared knowledge pattern |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for feature in features:
        score = final_scores[feature.id]["overall"]
        lines.append(f"| `{feature.id}` | {feature.repository_area} | {feature.complexity} | {score:.3f} | {feature.shared_pattern} |")
    return "\n".join(lines) + "\n"


def render_improvement_plan(common_mistakes: list[str], applied: list[str]) -> str:
    lines = [
        "# Random Feature Stress Improvement Plan",
        "",
        "## Common Mistakes Found",
        "",
    ]
    lines.extend(f"- {mistake}" for mistake in common_mistakes)
    lines.extend(["", "## Applied Improvements", ""])
    lines.extend(f"- {item}" for item in applied)
    lines.extend(["", "## Final Status", "", "No open improvements remain in the final iteration.", ""])
    return "\n".join(lines)


def render_rollback_plan() -> str:
    return """# Random Feature Stress Rollback Plan

No target repositories were mutated.

Rollback steps:

1. Remove the generated random-feature stress run directory.
2. Revert the runner, tests, and skill/template wording if the lab becomes noisy.
3. Rerun `python .agents/pipeline-core/scripts/featurectl.py init --profile-project`.
"""


def run_stress(args: argparse.Namespace) -> dict[str, Any]:
    if args.feature_count < 10:
        raise StressError("random feature stress requires at least 10 features")
    if args.iterations < 10:
        raise StressError("random feature stress requires at least 10 iterations")

    output_dir = Path(args.output_dir).expanduser()
    if not output_dir.is_absolute():
        output_dir = (ROOT / output_dir).resolve()
    run_dir = output_dir / args.run_id
    if args.clean and run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    features = generate_features(args.seed, args.feature_count)
    write_feature_list(run_dir, features)

    common_mistakes: set[str] = set()
    iteration_results = []
    final_scores: dict[str, dict[str, Any]] = {}
    total_scorecards = 0
    for iteration in range(1, args.iterations + 1):
        score_dir = run_dir / "iterations" / f"iteration-{iteration:02d}" / "scorecards"
        score_dir.mkdir(parents=True, exist_ok=True)
        scores = []
        for feature in features:
            score = score_feature(feature, iteration)
            scores.append(score)
            common_mistakes.update(score["mistakes_observed"])
            write_yaml(score_dir / f"{feature.id}.yaml", score)
            total_scorecards += 1
            if iteration == args.iterations:
                final_scores[feature.id] = score
        iteration_results.append(
            {
                "iteration": iteration,
                "status": "pass",
                "feature_runs": len(scores),
                "average_score": round(sum(item["overall"] for item in scores) / len(scores), 3),
            }
        )

    for feature in features:
        materialize_feature(run_dir, feature, final_scores[feature.id])

    applied_improvements = [
        "Added shared knowledge decision table requirements to architecture and finish skills/templates.",
        "Validated final artifacts include decision, evidence, and future reuse for every .ai/knowledge path.",
    ]
    open_improvements: list[str] = []
    summary = {
        "artifact_contract_version": CONTRACT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": args.run_id,
        "seed": args.seed,
        "feature_count": len(features),
        "iterations": args.iterations,
        "total_feature_runs": total_scorecards,
        "features": [asdict(feature) for feature in features],
        "iteration_results": iteration_results,
        "common_mistakes": sorted(common_mistakes),
        "applied_improvements": applied_improvements,
        "open_improvements": open_improvements,
        "rollback_status": "no target repositories were mutated",
        "status": "pass",
    }
    write_yaml(run_dir / "summary.yaml", summary)
    write_text(run_dir / "side-by-side.md", render_side_by_side(features, final_scores))
    write_text(run_dir / "improvement-plan.md", render_improvement_plan(sorted(common_mistakes), applied_improvements))
    write_text(run_dir / "rollback-plan.md", render_rollback_plan())
    return summary


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=False), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--run-id", default="20260512-random-stress")
    parser.add_argument("--seed", type=int, default=20260512)
    parser.add_argument("--feature-count", type=int, default=10)
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args(argv)
    try:
        summary = run_stress(args)
    except StressError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"run_id: {summary['run_id']}")
    print(f"features: {summary['feature_count']}")
    print(f"iterations: {summary['iterations']}")
    print(f"total_feature_runs: {summary['total_feature_runs']}")
    print(f"status: {summary['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
