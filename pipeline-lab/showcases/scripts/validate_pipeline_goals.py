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
DEFAULT_INIT_RUN = ROOT / "pipeline-lab/showcases/init-profile-runs/20260512-init-profile"
DEFAULT_RANDOM_STRESS_RUN = ROOT / "pipeline-lab/showcases/random-feature-stress-runs/20260512-random-stress"
DEFAULT_CODEX_DEBUG_RUN = ROOT / "pipeline-lab/showcases/codex-debug-runs/20260512-debug"
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


def validate_once(native_run: Path, init_run: Path, codex_debug_run: Path) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    checks.extend(validate_agents_policy())
    checks.extend(validate_vision_and_plan())
    checks.extend(validate_best_three(native_run))
    checks.extend(validate_project_profile())
    checks.extend(validate_init_showcases(init_run))
    checks.extend(validate_skill_matrix())
    checks.extend(validate_random_feature_stress(DEFAULT_RANDOM_STRESS_RUN))
    checks.extend(validate_codex_debug_run(codex_debug_run))
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


def validate_agents_policy() -> list[dict[str, str]]:
    agents = read_text(ROOT / "AGENTS.md")
    return [
        check(
            "agents_pipeline_mandatory",
            "The Native Feature Pipeline is mandatory" in agents and "If there is doubt, use the pipeline" in agents,
            "AGENTS.md makes pipeline use mandatory for feature-building work",
        ),
        check(
            "agents_self_modification_policy",
            "Use our own technology while changing it" in agents and "Do not bypass the pipeline because a change is \"internal\"" in agents,
            "AGENTS.md applies the pipeline to pipeline self-modification",
        ),
        check(
            "agents_init_before_feature_work",
            "featurectl.py init --profile-project" in agents and ".ai/knowledge/project-index.yaml" in agents,
            "AGENTS.md requires project init and knowledge inspection before feature planning",
        ),
        check(
            "agents_feature_worktree_sequence",
            "featurectl.py new" in agents and "dedicated feature worktree" in agents and "nfp-00-intake" in agents and "nfp-12-promote" in agents,
            "AGENTS.md requires new/resumed workspace and full pipeline sequence",
        ),
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
        check("init_feature_catalog", len(profile.get("feature_catalog") or []) >= 3, "feature catalog extracted"),
        check("init_current_feature_picture", "Current Feature Picture" in read_text(ROOT / ".ai/knowledge/features-overview.md"), "features overview describes current feature picture"),
        check("context_skill_uses_profile", "featurectl.py init --profile-project" in context_skill, "context skill invokes project profiling when knowledge is sparse"),
    ]


def validate_init_showcases(init_run: Path) -> list[dict[str, str]]:
    summary_path = init_run / "summary.yaml"
    report_path = ROOT / "pipeline-lab/showcases/init-profile-report.md"
    if not summary_path.exists():
        return [check("init_showcase_summary_exists", False, f"missing {summary_path}")]
    summary = read_yaml(summary_path)
    results = summary.get("results") or []
    comparisons = summary.get("comparisons") or []
    failures = summary.get("failures") or []
    expected_results = int(summary.get("passes") or 0) * len(summary.get("cases") or [])
    return [
        check("init_showcase_summary_exists", summary_path.exists(), "init showcase summary exists"),
        check("init_showcase_report_exists", report_path.exists(), "init showcase report exists"),
        check("init_showcase_three_passes", int(summary.get("passes") or 0) == 3, f"passes: {summary.get('passes')}"),
        check("init_showcase_ten_cases", len(summary.get("cases") or []) == 10, f"cases: {len(summary.get('cases') or [])}"),
        check("init_showcase_all_results", len(results) == expected_results == 30, f"results: {len(results)} expected: {expected_results}"),
        check("init_showcase_no_failures", not failures, f"failures: {len(failures)}"),
        check("init_showcase_stable", comparisons and all(item.get("stable_metrics") for item in comparisons), "all repos stable across repeated init passes"),
        check(
            "init_showcase_feature_catalogs",
            results and all(int(item.get("feature_catalog_count") or 0) > 0 for item in results),
            "every init run produced a feature catalog",
        ),
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
            "skills/native-feature-pipeline/references/upstream-pattern-map.md",
            "featurectl.py load-docset",
            "Docs Consulted:",
            "featurectl.py validate",
        ):
            if token not in content:
                missing.append(token)
        checks.append(check(f"skill_{name}", not missing, "missing: " + ", ".join(missing) if missing else "shared protocol present"))
    architecture_skill = read_text(ROOT / ".agents/skills/nfp-03-architecture/SKILL.md")
    checks.append(
        check(
            "skill_architecture_mermaid_topology",
            "## Feature Topology" in architecture_skill and "Mermaid" in architecture_skill and ".ai/knowledge" in architecture_skill,
            "architecture skill requires Mermaid topology and shared knowledge impact",
        )
    )
    checks.append(
        check(
            "skill_architecture_shared_knowledge_decision_table",
            "Shared Knowledge Decision Table" in architecture_skill
            and "Decision" in architecture_skill
            and "Evidence" in architecture_skill
            and "Future reuse" in architecture_skill,
            "architecture skill requires shared knowledge decisions with evidence and future reuse",
        )
    )
    finish_skill = read_text(ROOT / ".agents/skills/nfp-11-finish/SKILL.md")
    checks.append(
        check(
            "skill_finish_shared_knowledge_updates",
            "## Shared Knowledge Updates" in finish_skill and ".ai/knowledge/features-overview.md" in finish_skill,
            "finish skill requires shared knowledge update reporting",
        )
    )
    checks.append(
        check(
            "skill_finish_shared_knowledge_decision_table",
            "Shared Knowledge Decision Table" in finish_skill
            and "Decision" in finish_skill
            and "Evidence" in finish_skill
            and "Future reuse" in finish_skill,
            "finish skill requires shared knowledge decisions with evidence and future reuse",
        )
    )
    tdd_skill = ROOT / ".agents/skills/nfp-08-tdd-implementation/SKILL.md"
    tdd_content = read_text(tdd_skill) if tdd_skill.exists() else ""
    missing_subagent_tokens = [
        token
        for token in (
            "Subagent Flow Is Mandatory",
            "skills/superpowers/subagent-driven-development/SKILL.md",
            "fresh implementer subagent",
            "spec-compliance reviewer subagent",
            "code-quality reviewer subagent",
        )
        if token not in tdd_content
    ]
    checks.append(
        check(
            "skill_tdd_superpowers_subagent_flow",
            not missing_subagent_tokens,
            "missing: " + ", ".join(missing_subagent_tokens) if missing_subagent_tokens else "mandatory Superpowers subagent flow present",
        )
    )
    init_skill = ROOT / ".agents/skills/project-init/SKILL.md"
    if not init_skill.exists():
        checks.append(check("skill_project-init", False, "missing project-init skill"))
    else:
        content = read_text(init_skill)
        missing = [
            token
            for token in (
                "featurectl.py init --profile-project",
                ".ai/knowledge/project-index.yaml",
                "feature_catalog",
                "Current Feature Picture",
                "No implementation code is changed",
            )
            if token not in content
        ]
        checks.append(check("skill_project-init", not missing, "missing: " + ", ".join(missing) if missing else "/init profile protocol present"))
    return checks


def validate_random_feature_stress(run_dir: Path) -> list[dict[str, str]]:
    summary_path = run_dir / "summary.yaml"
    report_path = run_dir / "side-by-side.md"
    if not summary_path.exists():
        return [check("random_stress_summary_exists", False, f"missing {summary_path}")]
    summary = read_yaml(summary_path)
    common = summary.get("common_mistakes") or []
    open_improvements = summary.get("open_improvements") or []
    side_by_side = read_text(report_path) if report_path.exists() else ""
    return [
        check("random_stress_summary_exists", summary_path.exists(), "random stress summary exists"),
        check("random_stress_ten_features", int(summary.get("feature_count") or 0) == 10, f"features: {summary.get('feature_count')}"),
        check("random_stress_ten_iterations", int(summary.get("iterations") or 0) == 10, f"iterations: {summary.get('iterations')}"),
        check("random_stress_hundred_runs", int(summary.get("total_feature_runs") or 0) == 100, f"runs: {summary.get('total_feature_runs')}"),
        check("random_stress_common_mistakes", "generic shared-knowledge path bullets" in common, "common shared-knowledge mistake detected"),
        check("random_stress_no_open_improvements", not open_improvements, f"open improvements: {len(open_improvements)}"),
        check("random_stress_side_by_side", "Side By Side Knowledge Comparison" in side_by_side and "10/10" in side_by_side, "side-by-side knowledge report exists"),
    ]


def validate_codex_debug_run(run_dir: Path) -> list[dict[str, str]]:
    summary_path = run_dir / "summary.yaml"
    validation_path = run_dir / "validation.md"
    comparison_path = run_dir / "comparison.md"
    if not summary_path.exists():
        return [check("codex_debug_summary_exists", False, f"missing {summary_path}")]
    summary = read_yaml(summary_path)
    comparison = summary.get("comparison") or {}
    results = summary.get("results") or []
    artifact_results = [
        all((item.get("artifacts") or {}).get(name) for name in ("feature.md", "architecture.md", "tech-design.md", "slices.yaml"))
        for item in results
        if item.get("mode") != "dry-run"
    ]
    comparison_text = read_text(comparison_path) if comparison_path.exists() else ""
    validation_text = read_text(validation_path) if validation_path.exists() else ""
    return [
        check("codex_debug_summary_exists", summary_path.exists(), "codex debug summary exists"),
        check("codex_debug_status_pass", summary.get("status") == "pass", f"status: {summary.get('status')}"),
        check("codex_debug_explicit_mode", summary.get("mode") in {"mock", "dry-run", "real"}, f"mode: {summary.get('mode')}"),
        check("codex_debug_real_flag", isinstance(summary.get("uses_real_codex"), bool), "uses_real_codex is explicit"),
        check(
            "codex_debug_compares_current_tests",
            comparison.get("current_unit_tests_use_fake_codex") is True and "Uses fake Codex" in comparison_text,
            "comparison proves current unit tests use fake Codex",
        ),
        check("codex_debug_artifacts_validated", bool(results) and all(artifact_results), "generated NFP artifacts validated"),
        check("codex_debug_validation_report", "Codex Debug Pipeline Validation" in validation_text, "validation report exists"),
    ]


def validate_web_best_practices() -> list[dict[str, str]]:
    path = ROOT / "skills/native-feature-pipeline/references/web-best-practices-20260512.md"
    content = read_text(path) if path.exists() else ""
    checks = [check("web_best_practices_doc", path.exists(), "web best-practices synthesis exists")]
    for source in REQUIRED_WEB_SOURCES:
        checks.append(check(f"web_source_{source}", source in content, f"source recorded: {source}"))
    for section in (
        "## What To Borrow",
        "## What To Reject",
        "## Native Artifact Influence",
        "## Native Skill Influence",
        "## Init Bootstrap Influence",
        "## Three-Pass Init Validation",
        "## Validation Rule Implied",
    ):
        checks.append(check(f"web_doc_{section}", section in content, f"{section} present"))
    return checks


def repeated_validate(native_run: Path, init_run: Path, codex_debug_run: Path, passes: int) -> list[dict[str, Any]]:
    results = []
    for pass_number in range(1, passes + 1):
        checks = validate_once(native_run, init_run, codex_debug_run)
        failures = [item for item in checks if item["status"] == "fail"]
        results.append({"pass": pass_number, "status": "fail" if failures else "pass", "checks": checks})
    return results


def render_report(results: list[dict[str, Any]], native_run: Path, init_run: Path, codex_debug_run: Path) -> str:
    lines = [
        "# Pipeline Goal Validation",
        "",
        f"- Native run: `{native_run}`",
        f"- Init profile run: `{init_run}`",
        f"- Codex debug run: `{codex_debug_run}`",
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
        if item["name"].startswith("skill_") and item["name"] != "skill_count":
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
    parser.add_argument("--init-run", default=str(DEFAULT_INIT_RUN), help="Init profile run directory")
    parser.add_argument("--codex-debug-run", default=str(DEFAULT_CODEX_DEBUG_RUN), help="Codex debug run directory")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Report path")
    parser.add_argument("--passes", type=int, default=3, help="Repeated validation passes")
    args = parser.parse_args(argv)

    native_run = Path(args.native_run).expanduser()
    if not native_run.is_absolute():
        native_run = (ROOT / native_run).resolve()
    init_run = Path(args.init_run).expanduser()
    if not init_run.is_absolute():
        init_run = (ROOT / init_run).resolve()
    codex_debug_run = Path(args.codex_debug_run).expanduser()
    if not codex_debug_run.is_absolute():
        codex_debug_run = (ROOT / codex_debug_run).resolve()
    report = Path(args.report).expanduser()
    if not report.is_absolute():
        report = (ROOT / report).resolve()
    results = repeated_validate(native_run, init_run, codex_debug_run, args.passes)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(results, native_run, init_run, codex_debug_run), encoding="utf-8")
    failures = [item for result in results for item in result["checks"] if item["status"] == "fail"]
    print(f"report: {report}")
    print(f"passes: {args.passes}")
    print(f"failures: {len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
