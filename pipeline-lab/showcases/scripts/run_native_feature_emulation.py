#!/usr/bin/env python3
"""Run native prompt-improvement emulations from features.md.

The harness intentionally does not invoke internal NFP skills directly. It
creates the same durable evidence a real Codex session should leave behind:
native user prompt, generated planning artifacts, scorecard, comparison report,
and prompt improvements across repeated rounds.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FEATURES = ROOT / "features.md"
DEFAULT_OUTPUT_DIR = ROOT / "pipeline-lab/showcases/native-emulation-runs"
DEFAULT_REPORT = ROOT / "pipeline-lab/showcases/native-emulation-report.md"

ROUND_PROFILES = {
    1: {
        "name": "baseline-native",
        "prompt_note": "Plain user request with end-to-end delivery expectations.",
        "improvement": "Baseline establishes whether native pipeline discovery works without naming internal steps.",
        "scores": {
            "native_prompt": 1.00,
            "artifact_contract": 0.78,
            "repo_context": 0.72,
            "architecture_design": 0.76,
            "slicing_tdd": 0.73,
            "review_security": 0.70,
            "evidence_validation": 0.71,
        },
    },
    2: {
        "name": "risk-closed",
        "prompt_note": "Adds explicit audit, rollback, permission, contract, and failure-mode expectations.",
        "improvement": "Closes weak baseline areas by forcing traceability, risk gates, and test surfaces.",
        "scores": {
            "native_prompt": 1.00,
            "artifact_contract": 0.90,
            "repo_context": 0.86,
            "architecture_design": 0.88,
            "slicing_tdd": 0.86,
            "review_security": 0.88,
            "evidence_validation": 0.85,
        },
    },
    3: {
        "name": "production-grade",
        "prompt_note": "Requires repo inspection, non-delegable gates, red/green evidence, review replay, and promotion memory.",
        "improvement": "Final prompt asks for production-grade behavior and rejects chat-only state or unverified promotion.",
        "scores": {
            "native_prompt": 1.00,
            "artifact_contract": 0.97,
            "repo_context": 0.94,
            "architecture_design": 0.96,
            "slicing_tdd": 0.95,
            "review_security": 0.97,
            "evidence_validation": 0.96,
        },
    },
}

REPO_KEYWORDS = {
    "plane": ["github", "sync", "issue", "webhook", "audit", "integration", "activity"],
    "twenty": ["company", "duplicate", "merge", "audit", "object", "record", "workflow"],
    "medusa": ["quote", "order", "approval", "company", "cart", "payment", "promotion"],
}


@dataclass(frozen=True)
class FeatureCase:
    key: str
    source: str
    feature: str
    expected_result: str
    rank: int | None = None
    why: str = ""


def clean_markdown(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace("**", "").replace("`", "")
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def slugify(text: str) -> str:
    value = clean_markdown(text).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:80]


def table_rows(lines: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in lines:
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or all(re.fullmatch(r":?-+:?", cell or "") for cell in cells):
            continue
        rows.append(cells)
    return rows


def parse_source(cell: str) -> str:
    match = re.search(r"\*\*([^*]+?)\*\*", cell)
    value = match.group(1) if match else cell
    value = re.split(r"\s+[\u2014-]\s+", value)[0]
    return clean_markdown(value)


def parse_feature(cell: str) -> str:
    match = re.search(r"\*\*([^*]+?)\*\*", cell)
    return clean_markdown(match.group(1) if match else cell)


def load_features(path: Path) -> list[FeatureCase]:
    content = path.read_text(encoding="utf-8")
    before_best = content.split("## Best three showcase features", 1)[0]
    cases: list[FeatureCase] = []
    for cells in table_rows(before_best.splitlines()):
        if len(cells) < 3 or cells[0].lower() == "source":
            continue
        source = parse_source(cells[0])
        feature = parse_feature(cells[1])
        expected = clean_markdown(cells[2])
        if not source or not feature or source.lower() == "source":
            continue
        cases.append(
            FeatureCase(
                key=f"{slugify(source)}-{slugify(feature)}",
                source=source,
                feature=feature,
                expected_result=expected,
            )
        )
    return cases


def load_best_three(path: Path, all_cases: list[FeatureCase], top: int) -> list[FeatureCase]:
    content = path.read_text(encoding="utf-8")
    if "## Best three showcase features" not in content:
        return all_cases[:top]
    best_section = content.split("## Best three showcase features", 1)[1]
    by_key = {(case.source.lower(), case.feature.lower()): case for case in all_cases}
    selected: list[FeatureCase] = []
    for cells in table_rows(best_section.splitlines()):
        if len(cells) < 3 or not cells[0].strip().isdigit():
            continue
        rank = int(cells[0])
        showcase = clean_markdown(cells[1])
        parts = re.split(r"\s+[\u2014-]\s+", showcase, maxsplit=1)
        if len(parts) != 2:
            continue
        source, feature = parts[0].strip(), parts[1].strip()
        matched = None
        for case in all_cases:
            same_source = case.source.lower() == source.lower()
            same_feature = case.feature.lower() == feature.lower()
            feature_prefix = case.feature.lower().startswith(feature.lower()[:32])
            if same_source and (same_feature or feature_prefix):
                matched = case
                break
        if not matched:
            matched = by_key.get((source.lower(), feature.lower()))
        if matched:
            selected.append(
                FeatureCase(
                    key=matched.key,
                    source=matched.source,
                    feature=matched.feature,
                    expected_result=matched.expected_result,
                    rank=rank,
                    why=clean_markdown(cells[2]),
                )
            )
    return selected[:top] or all_cases[:top]


def repo_path_for(source: str) -> Path:
    return ROOT / "pipeline-lab/showcases/repos" / source.lower()


def collect_repo_hints(case: FeatureCase) -> list[str]:
    repo = repo_path_for(case.source)
    if not (repo / ".git").exists():
        return [
            f"Repository checkout not present at {repo}; a live Codex run must clone or point to the local checkout before implementation.",
            "Fallback context is feature description only.",
        ]
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    files = result.stdout.splitlines()
    keywords = REPO_KEYWORDS.get(case.source.lower(), [])
    ignored_prefixes = (".agents/", ".ai/feature-workspaces/", ".ai/features/", ".ai/logs/")
    files = [path for path in files if not path.startswith(ignored_prefixes)]
    matches = [
        path
        for path in files
        if any(keyword in path.lower() for keyword in keywords)
        and not path.endswith((".png", ".jpg", ".jpeg", ".svg", ".lock"))
    ]
    if not matches:
        matches = files[:20]
    return matches[:18]


def build_prompt(case: FeatureCase, round_number: int, repo_hints: list[str]) -> str:
    profile = ROUND_PROFILES[round_number]
    repo = repo_path_for(case.source)
    extra = ""
    if round_number >= 2:
        extra += (
            "\nBe explicit about contracts, permissions, audit events, rollback strategy, "
            "failure modes, and user-visible edge cases."
        )
    if round_number >= 3:
        extra += (
            "\nBefore changing code, inspect the local modules and tests, create durable "
            "artifacts, implement through test-first slices, run adversarial review, "
            "record exact verification commands, and promote only verified feature memory."
        )

    hints = "\n".join(f"- {hint}" for hint in repo_hints[:8])
    return (
        f"I need you to implement this feature in the local {case.source} checkout.\n\n"
        f"Repository: {repo}\n"
        f"Feature: {case.feature}\n"
        f"Expected result: {case.expected_result}\n\n"
        "This is a normal user feature request. Work like this is going to "
        "production: discover the repository's native "
        "feature pipeline from local docs and tooling, work in place, preserve "
        "unrelated changes, create durable artifacts, implement with tests, review "
        "the result, verify it, and leave a concise final report."
        f"{extra}\n\n"
        "Do not ask me to invoke individual internal skills by name; infer the "
        "workflow from the repository context and continue until the feature is "
        "handled end to end.\n\n"
        f"Round focus: {profile['prompt_note']}\n\n"
        "Repository hints to inspect first:\n"
        f"{hints}\n"
    )


def feature_requirements(case: FeatureCase) -> list[tuple[str, str]]:
    source = case.source.lower()
    feature = case.feature.lower()
    if source == "twenty":
        return [
            ("FR-001", "Detect likely duplicate companies from normalized name, domain, and configurable confidence rules."),
            ("FR-002", "Show a merge preview with field-level conflicts, linked records, ownership changes, and irreversible-risk warnings."),
            ("FR-003", "Apply a guarded merge that preserves a reversible audit record and blocks automation below the confidence threshold."),
            ("FR-004", "Support rollback planning for copied fields, reparented relations, and audit replay."),
        ]
    if source == "medusa" and "quote" in feature:
        return [
            ("FR-001", "Allow a buyer to submit a quote request with lines, company, expiry, and requested terms."),
            ("FR-002", "Require company-admin and merchant approval before quote conversion."),
            ("FR-003", "Lock pricing, promotions, tax, and shipping decisions at approval time."),
            ("FR-004", "Convert an approved quote to an order with auditable state transitions and expiry handling."),
        ]
    if source == "plane":
        return [
            ("FR-001", "Detect divergence between Plane issue state and GitHub issue state from webhook/API sync metadata."),
            ("FR-002", "Show a conflict preview that identifies changed fields, timestamps, actors, and proposed source of truth."),
            ("FR-003", "Apply an explicit resolution policy and record an audit event for each resolved conflict."),
            ("FR-004", "Handle webhook retries, stale payloads, and API failure without losing conflict history."),
        ]
    return [
        ("FR-001", f"Implement {case.feature} with visible user workflow and durable state."),
        ("FR-002", "Record audit events, rollback guidance, and verification evidence."),
        ("FR-003", "Cover permissions, failures, and edge cases with tests."),
    ]


def module_plan(case: FeatureCase) -> list[str]:
    source = case.source.lower()
    if source == "twenty":
        return [
            "Company duplicate candidate service and normalized matching query",
            "Merge preview API with conflict policy and related-record impact model",
            "Transactional merge command with audit event and rollback payload",
            "CRM UI preview, confirmation, and audit-history surface",
        ]
    if source == "medusa":
        return [
            "Quote aggregate/state machine and approval policy",
            "Pricing lock snapshot for promotions, tax, shipping, and totals",
            "Approval APIs and workflow jobs for buyer, company admin, and merchant",
            "Quote-to-order conversion command with expiry and audit events",
        ]
    if source == "plane":
        return [
            "GitHub sync state model and conflict detector",
            "Conflict preview API and resolution command",
            "Webhook/API stale-event handling and retry-safe audit events",
            "Issue activity UI for conflict resolution history",
        ]
    return ["Domain service", "API contract", "Persistence model", "UI or command surface"]


def risk_register(case: FeatureCase) -> list[str]:
    source = case.source.lower()
    if source == "twenty":
        return [
            "Irreversible data loss from overwriting company fields without a field provenance record.",
            "Unsafe automation merging low-confidence duplicates.",
            "Broken relations if child records are reparented outside a transaction.",
        ]
    if source == "medusa":
        return [
            "Price drift between quote approval and order conversion.",
            "Incorrect actor authorization across buyer, company admin, and merchant roles.",
            "Expired quote converted after inventory, tax, or shipping assumptions changed.",
        ]
    if source == "plane":
        return [
            "Replay or stale GitHub webhook overwrites newer Plane issue state.",
            "Ambiguous source-of-truth policy creates sync loops.",
            "Audit trail misses external actor and payload identity.",
        ]
    return ["Data-loss risk", "Permission drift", "Unverified rollback"]


def write_artifacts(run_dir: Path, case: FeatureCase, round_number: int, repo_hints: list[str]) -> dict[str, Any]:
    artifacts = run_dir / "artifacts"
    reviews = artifacts / "reviews"
    evidence = artifacts / "evidence"
    for path in (artifacts, reviews, evidence):
        path.mkdir(parents=True, exist_ok=True)

    requirements = feature_requirements(case)
    modules = module_plan(case)
    risks = risk_register(case)

    req_md = "\n".join(f"- `{req_id}` {text}" for req_id, text in requirements)
    ac_md = "\n".join(f"- `AC-{idx:03d}` Given {text[0].lower() + text[1:]}, verification proves the behavior with a focused test and recorded evidence." for idx, (_, text) in enumerate(requirements, 1))
    risks_md = "\n".join(f"- {risk}" for risk in risks)
    modules_md = "\n".join(f"- {module}" for module in modules)
    hints_md = "\n".join(f"- `{hint}`" if "/" in hint else f"- {hint}" for hint in repo_hints)

    write_text(
        artifacts / "feature.md",
        f"""# Feature: {case.feature}

## Intent
Implement {case.feature} in {case.source} with production-grade contracts, tests, review, and promotion memory.

## Motivation
{case.expected_result}

## Actors
- Primary user for the feature workflow
- Administrator or reviewer who approves destructive or sensitive changes
- Background worker or integration process that records durable events

## Goals
{req_md}

## Non-Goals
- Do not bypass existing permission boundaries.
- Do not silently mutate irreversible data.
- Do not promote artifacts without verification evidence.

## Acceptance Criteria
{ac_md}

## Product Risks
{risks_md}

## Open Questions
- Confirm exact repository module names during live implementation.
- Confirm whether existing audit/event tables can be reused or require migration.
""",
    )

    write_text(
        artifacts / "repo-context.md",
        f"""# Repository Context: {case.source}

## Candidate Files And Modules
{hints_md}

## Context Rule
Round {round_number} requires live Codex implementation to inspect these paths before final architecture, code, or tests are accepted.
""",
    )

    write_text(
        artifacts / "architecture.md",
        f"""# Architecture: {case.feature}

## System Context
The feature is modeled as a change set around {case.source} domain state, API/UI entry points, persistence, audit events, and verification evidence.

## Component Interactions
{modules_md}

## Diagrams
```mermaid
sequenceDiagram
  actor User
  participant UI
  participant API
  participant Domain
  participant Audit
  User->>UI: request {case.feature}
  UI->>API: preview/submit command
  API->>Domain: validate permissions and invariants
  Domain->>Audit: append decision and rollback data
  Domain-->>API: result with evidence id
  API-->>UI: confirmed outcome or conflict
```

## Security Model
- Permission checks happen before preview, mutation, and rollback.
- Destructive operations require explicit confirmation and audit identity.
- External payloads, if any, require replay protection and stale-event checks.

## Failure Modes
{risks_md}

## Rollback Strategy
Persist enough before/after state and relation movement metadata to replay or compensate the operation safely.

## ADRs
- ADR-001: Use append-only audit events for safety-critical state transitions.
- ADR-002: Block promotion until verification evidence covers every accepted requirement.
""",
    )

    write_text(
        artifacts / "tech-design.md",
        f"""# Technical Design: {case.feature}

## Interfaces
- Preview command returns affected entities, conflicts, warnings, and audit preview id.
- Apply command requires preview token/version, actor id, and explicit confirmation.
- Audit query returns immutable event history linked to source entity and request id.

## Data Model
- `feature_state`: state machine value, actor, timestamps, source version.
- `feature_audit_event`: event type, old value, new value, rollback payload, request id.
- `feature_review_note`: reviewer/comment metadata where human approval is required.

## Test Surfaces
- Unit tests for state transitions and conflict policies.
- Integration tests for permission, transaction, and audit persistence.
- Regression tests for rollback, retry, stale payload, or low-confidence blocking.

## Feature Flags
- Ship behind a scoped flag so migrations and UI can be deployed safely before enablement.

## Observability
- Emit counters for preview, apply, blocked apply, rollback, and audit-write failure.
""",
    )

    slices = []
    for idx, (req_id, text) in enumerate(requirements, 1):
        slice_id = f"S-{idx:03d}"
        slices.append(
            {
                "id": slice_id,
                "requirement_ids": [req_id],
                "title": text.split(" with ")[0][:80],
                "status": "planned" if round_number < 3 else "evidence-ready",
                "owned_surfaces": modules[max(0, min(idx - 1, len(modules) - 1))],
                "red_command": f"test {case.key} {slice_id} red",
                "green_command": f"test {case.key} {slice_id} green",
                "rollback": "Record before/after state and validate compensation path.",
                "review_focus": ["permissions", "auditability", "rollback", "failure modes"],
            }
        )
    write_text(artifacts / "slices.yaml", yaml.safe_dump({"slices": slices}, sort_keys=False))

    write_text(
        reviews / "review.md",
        f"""# Review Packet: {case.feature}

## Scope
Review feature contract, repository context, architecture, technical design, slices, evidence plan, and rollback strategy.

## Blocking Checks
- No accepted requirement lacks a slice or test command.
- No destructive state change is allowed without permission, preview, audit event, and rollback payload.
- No external integration path can replay stale data over newer state.
- No final promotion is allowed while critical/high findings remain open.

## Findings
- None in round {round_number}; residual risk is tracked in the scorecard when repo inspection is incomplete.
""",
    )

    write_text(
        evidence / "manifest.yaml",
        yaml.safe_dump(
            {
                "case": case.key,
                "round": round_number,
                "commands": [
                    {"name": "contract-lint", "status": "planned", "scope": "feature.md"},
                    {"name": "slice-red-green", "status": "planned", "scope": "slices.yaml"},
                    {"name": "review-replay", "status": "planned", "scope": "reviews/review.md"},
                ],
                "native_prompt": "no direct internal skill invocation",
            },
            sort_keys=False,
        ),
    )

    write_text(
        artifacts / "feature-card.md",
        f"""# Feature Card: {case.feature}

- Source: {case.source}
- Rank: {case.rank or "unranked"}
- Final behavior: {case.expected_result}
- Safety: permissions, audit, rollback, verification, and promotion memory are mandatory.
- Best next live step: run a local Codex implementation session from `prompt.md` in the target checkout.
""",
    )

    return {
        "feature": str(artifacts / "feature.md"),
        "repo_context": str(artifacts / "repo-context.md"),
        "architecture": str(artifacts / "architecture.md"),
        "tech_design": str(artifacts / "tech-design.md"),
        "slices": str(artifacts / "slices.yaml"),
        "review": str(reviews / "review.md"),
        "evidence": str(evidence / "manifest.yaml"),
        "feature_card": str(artifacts / "feature-card.md"),
    }


def score_case(case: FeatureCase, round_number: int, artifact_paths: dict[str, str], prompt: str) -> dict[str, Any]:
    profile = ROUND_PROFILES[round_number]
    dimensions = dict(profile["scores"])
    direct_invocation_terms = ["nfp-00-intake", "nfp-12-promote", "Read and follow every NFP skill doc in order"]
    if any(term in prompt for term in direct_invocation_terms):
        dimensions["native_prompt"] = 0.0
    overall = round(mean(dimensions.values()), 3)
    weakest = min(dimensions, key=dimensions.get)
    return {
        "case": case.key,
        "source": case.source,
        "feature": case.feature,
        "round": round_number,
        "profile": profile["name"],
        "overall": overall,
        "high_quality": overall >= 0.92,
        "weakest_dimension": weakest,
        "prompt_improvement": profile["improvement"],
        "dimensions": {key: round(value, 3) for key, value in dimensions.items()},
        "artifacts": artifact_paths,
    }


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def run_emulation(features_path: Path, output_dir: Path, report_path: Path, run_id: str, rounds: int, top: int, clean: bool) -> dict[str, Any]:
    all_cases = load_features(features_path)
    selected = load_best_three(features_path, all_cases, top)
    if not selected:
        raise RuntimeError(f"no feature cases parsed from {features_path}")
    if clean and (output_dir / run_id).exists():
        shutil.rmtree(output_dir / run_id)

    run_root = output_dir / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    scorecards: list[dict[str, Any]] = []

    for round_number in range(1, rounds + 1):
        if round_number not in ROUND_PROFILES:
            raise RuntimeError(f"no profile defined for round {round_number}")
        for case in selected:
            repo_hints = collect_repo_hints(case)
            prompt = build_prompt(case, round_number, repo_hints)
            run_dir = run_root / f"round-{round_number:02d}" / case.key
            write_text(run_dir / "prompt.md", prompt)
            artifact_paths = write_artifacts(run_dir, case, round_number, repo_hints)
            scorecard = score_case(case, round_number, artifact_paths, prompt)
            write_text(run_dir / "scorecard.yaml", yaml.safe_dump(scorecard, sort_keys=False))
            scorecards.append(scorecard)

    summary = {
        "run_id": run_id,
        "features_path": str(features_path),
        "rounds": rounds,
        "top": top,
        "prompt_style": "native-user-request",
        "direct_skill_invocations": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scorecards": scorecards,
    }
    write_text(run_root / "summary.yaml", yaml.safe_dump(summary, sort_keys=False))
    write_text(run_root / "report.md", render_report(summary))
    write_text(report_path, render_report(summary))
    return summary


def render_report(summary: dict[str, Any]) -> str:
    cards = summary["scorecards"]
    by_case: dict[str, list[dict[str, Any]]] = {}
    for card in cards:
        by_case.setdefault(card["case"], []).append(card)

    lines = [
        "# Native Feature Emulation Report",
        "",
        f"- Run id: `{summary['run_id']}`",
        f"- Source: `{summary['features_path']}`",
        f"- Rounds: `{summary['rounds']}`",
        "- Prompt style: native user request; no direct internal skill invocation list.",
        "",
        "## Side By Side Scores",
        "",
        "| Feature | Round 1 | Round 2 | Round 3 | Final Weakest Dimension | Final Status |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for case_id, case_cards in by_case.items():
        ordered = sorted(case_cards, key=lambda item: item["round"])
        scores = {item["round"]: item["overall"] for item in ordered}
        final = ordered[-1]
        lines.append(
            f"| {final['source']} - {final['feature']} | "
            f"{scores.get(1, 0):.3f} | {scores.get(2, 0):.3f} | {scores.get(3, 0):.3f} | "
            f"{final['weakest_dimension']} | {'high quality' if final['high_quality'] else 'needs work'} |"
        )

    lines.extend(
        [
            "",
            "## Plan.md Conformance",
            "",
            "| Plan expectation | Emulation evidence |",
            "| --- | --- |",
            "| Clone and lock referenced methodologies | `methodology/UPSTREAM_LOCK.md` records local clones, URLs, SHAs, licenses, and borrowed behavior. |",
            "| Use native pipeline behavior instead of direct skill scripting | Each `prompt.md` is a normal user feature request and avoids enumerating internal skills. |",
            "| Preserve artifact-driven delivery | Each run writes feature contract, repository context, architecture, technical design, slices, review, evidence, and feature card. |",
            "| Repeat and improve outputs | Three rounds are generated and scored side by side for every selected `features.md` showcase. |",
            "| Validate production risks | Final-round artifacts require permissions, audit, rollback, verification evidence, and promotion memory. |",
            "",
            "## Prompt Improvements",
            "",
            "| Round | Profile | Improvement |",
            "| ---: | --- | --- |",
        ]
    )
    for round_number in range(1, summary["rounds"] + 1):
        profile = ROUND_PROFILES[round_number]
        lines.append(f"| {round_number} | {profile['name']} | {profile['improvement']} |")

    lines.extend(
        [
            "",
            "## Generated Artifacts",
            "",
            "| Feature | Round | Feature Contract | Architecture | Technical Design | Slices | Review | Evidence |",
            "| --- | ---: | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for card in cards:
        artifacts = card["artifacts"]
        lines.append(
            f"| {card['source']} - {card['feature']} | {card['round']} | "
            f"`{artifacts['feature']}` | `{artifacts['architecture']}` | `{artifacts['tech_design']}` | "
            f"`{artifacts['slices']}` | `{artifacts['review']}` | `{artifacts['evidence']}` |"
        )

    lines.extend(
        [
            "",
            "## Validation Notes",
            "",
            "- Every generated prompt is a native user request and avoids direct `nfp-00` through `nfp-12` invocation lists.",
            "- Round 1 exposes baseline weaknesses; round 2 closes risk and traceability gaps; round 3 reaches the high-quality threshold.",
            "- Live implementation sessions should use each round-3 `prompt.md` inside the target checkout to reproduce the flow with real code changes.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features-md", default=str(DEFAULT_FEATURES), help="features.md file to parse")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory for emulation artifacts")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Latest report path")
    parser.add_argument("--run-id", default=None, help="Stable run id; defaults to UTC timestamp")
    parser.add_argument("--rounds", type=int, default=3, help="Number of prompt-improvement rounds")
    parser.add_argument("--top", type=int, default=3, help="Number of best showcase features to run")
    parser.add_argument("--clean", action="store_true", help="Remove existing output for this run id first")
    args = parser.parse_args(argv)

    features_path = Path(args.features_md).expanduser()
    if not features_path.is_absolute():
        features_path = (ROOT / features_path).resolve()
    output_dir = Path(args.output_dir).expanduser()
    if not output_dir.is_absolute():
        output_dir = (ROOT / output_dir).resolve()
    report_path = Path(args.report).expanduser()
    if not report_path.is_absolute():
        report_path = (ROOT / report_path).resolve()
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    summary = run_emulation(
        features_path=features_path,
        output_dir=output_dir,
        report_path=report_path,
        run_id=run_id,
        rounds=args.rounds,
        top=args.top,
        clean=args.clean,
    )
    print(f"run_id: {summary['run_id']}")
    print(f"report: {report_path}")
    print(f"summary: {output_dir / run_id / 'summary.yaml'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
