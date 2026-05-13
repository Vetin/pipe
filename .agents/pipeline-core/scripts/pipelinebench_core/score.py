"""Workspace scoring and hard-check logic for pipelinebench."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import BenchError, CONTRACT_VERSION, read_yaml, utc_now

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

def parse_manual_soft_scores(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    if not path.exists():
        raise BenchError(f"soft score file does not exist: {path}")
    data = read_yaml(path)
    if not isinstance(data, dict):
        raise BenchError("soft score file must be a mapping")
    comments = str(data.get("comments") or "").strip()
    scores: dict[str, Any] = {}
    total_score = 0
    total_max = 0
    for key, value in data.items():
        if key == "comments":
            continue
        if isinstance(value, (int, float)):
            score = numeric_score(value, f"{key}.score")
            scores[key] = {"score": score, "max": 5}
            total_score += score
            total_max += 5
        elif isinstance(value, dict):
            score = numeric_score(value.get("score"), f"{key}.score")
            max_score = numeric_score(value.get("max", 5), f"{key}.max")
            if max_score <= 0:
                raise BenchError(f"{key}.max must be positive")
            item = {"score": score, "max": max_score}
            if value.get("comment"):
                item["comment"] = str(value["comment"])
            scores[key] = item
            total_score += score
            total_max += max_score
        else:
            raise BenchError(f"{key} must be a number or mapping with score/max")
    if not scores:
        raise BenchError("soft score file must contain at least one score")
    return scores, {
        "score": total_score,
        "max": total_max,
        "percent": round(total_score / total_max, 3) if total_max else 0,
        "comments": comments,
    }

def numeric_score(value: Any, field: str) -> int:
    if not isinstance(value, (int, float)):
        raise BenchError(f"{field} must be numeric")
    if value < 0:
        raise BenchError(f"{field} must be non-negative")
    return int(value)

def run_hard_check(workspace: Path, scenario: dict[str, Any], check: str) -> dict[str, Any]:
    if check == "core_artifacts":
        missing = [rel for rel in scenario.get("required_files", []) if not (workspace / rel).exists()]
        return hard_result(check, not missing, f"missing: {', '.join(missing)}" if missing else "all required files present")
    if check == "no_forbidden_files":
        forbidden = [str(path.relative_to(workspace)) for name in ("approvals.yaml", "handoff.md") for path in workspace.rglob(name)]
        return hard_result(check, not forbidden, f"forbidden: {', '.join(forbidden)}" if forbidden else "no forbidden files")
    if check == "schema_valid":
        blockers = schema_valid_blockers(workspace)
        return hard_result(check, not blockers, "; ".join(blockers) if blockers else "machine-readable artifacts have valid contract versions")
    if check == "docs_consulted_recorded":
        blockers = docs_consulted_blockers(workspace)
        return hard_result(check, not blockers, "; ".join(blockers) if blockers else "required docs consulted entries present")
    if check == "slices_have_tdd":
        blockers = slices_have_tdd_blockers(workspace / "slices.yaml")
        return hard_result(check, not blockers, "; ".join(blockers) if blockers else "all slices have TDD commands")
    if check == "evidence_files_exist":
        blockers = evidence_file_blockers(workspace)
        return hard_result(check, not blockers, "; ".join(blockers) if blockers else "evidence manifest file references exist")
    if check == "no_auto_implementation":
        state = read_yaml(workspace / "state.yaml") if (workspace / "state.yaml").exists() else {}
        implementation_ready = (state.get("gates") or {}).get("implementation") in {"approved", "delegated", "complete"}
        return hard_result(check, not implementation_ready, "implementation gate is not auto-approved")
    if check == "state_has_no_next_skill":
        state = read_yaml(workspace / "state.yaml") if (workspace / "state.yaml").exists() else {}
        return hard_result(check, "next_skill" not in state, "state.yaml has no next_skill" if "next_skill" not in state else "state.yaml contains next_skill")
    if check == "iteration_log_has_10_entries":
        content = read_text(workspace / "execution.md")
        missing = [f"I-{index:03d}" for index in range(1, 11) if f"I-{index:03d}" not in content]
        return hard_result(check, not missing, f"missing iterations: {', '.join(missing)}" if missing else "I-001 through I-010 present")
    if check == "iteration_entries_are_structured":
        content = read_text(workspace / "execution.md")
        required = ["slice:", "command:", "outcome:", "decision:", "next_action:"]
        missing = [term for term in required if term not in content]
        return hard_result(check, not missing, f"missing structured terms: {', '.join(missing)}" if missing else "iteration entries are structured")
    if check == "failed_iterations_have_triage":
        content = read_text(workspace / "execution.md")
        classes = [
            "failure_class: test_expected",
            "failure_class: implementation_bug",
            "failure_class: test_bug",
            "failure_class: design_gap",
            "failure_class: scope_change",
            "failure_class: environment_failure",
            "failure_class: flaky",
        ]
        has_failure = "outcome: failed" in content
        has_class = any(item in content for item in classes)
        return hard_result(check, (not has_failure) or has_class, "failed iterations have triage" if (not has_failure) or has_class else "failed iteration missing approved failure_class")
    if check == "loop_resume_checkpoint_present":
        content = read_text(workspace / "execution.md")
        count = content.count("resume_checkpoint:")
        return hard_result(check, count >= 10, f"resume checkpoints: {count}")
    if check == "slice_budget_declared":
        blockers = slice_budget_blockers(workspace / "slices.yaml")
        return hard_result(check, not blockers, "; ".join(blockers) if blockers else "slice budgets declared")
    if check == "plan_drift_recorded":
        feature_card = read_text(workspace / "feature-card.md")
        return hard_result(check, "Plan Drift" in feature_card or "plan drift" in feature_card.lower(), "plan drift recorded" if "plan drift" in feature_card.lower() else "feature-card.md missing plan drift")
    return hard_result(check, False, "unknown hard check")

def schema_valid_blockers(workspace: Path) -> list[str]:
    blockers = []
    for rel in ("feature.yaml", "state.yaml", "slices.yaml", "evidence/manifest.yaml"):
        path = workspace / rel
        if not path.exists():
            continue
        data = read_yaml(path)
        if data.get("artifact_contract_version") != CONTRACT_VERSION:
            blockers.append(f"{rel} artifact_contract_version mismatch")
    for path in sorted((workspace / "reviews").glob("*.yaml")) if (workspace / "reviews").exists() else []:
        data = read_yaml(path)
        if data.get("artifact_contract_version") != CONTRACT_VERSION:
            blockers.append(f"{path.relative_to(workspace)} artifact_contract_version mismatch")
    return blockers

def docs_consulted_blockers(workspace: Path) -> list[str]:
    execution = read_text(workspace / "execution.md")
    required = ("Feature Contract", "Architecture", "Technical Design", "Slicing")
    return [f"execution.md missing Docs Consulted: {label}" for label in required if f"Docs Consulted: {label}" not in execution]

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

def evidence_file_blockers(workspace: Path) -> list[str]:
    manifest_path = workspace / "evidence/manifest.yaml"
    if not manifest_path.exists():
        return ["missing evidence/manifest.yaml"]
    manifest = read_yaml(manifest_path)
    blockers = []
    if manifest.get("artifact_contract_version") != CONTRACT_VERSION:
        blockers.append("evidence/manifest.yaml artifact_contract_version mismatch")
    for slice_id, phases in (manifest.get("slices") or {}).items():
        if not isinstance(phases, dict):
            blockers.append(f"{slice_id} evidence entry must be a mapping")
            continue
        for phase, entry in phases.items():
            if not isinstance(entry, dict):
                blockers.append(f"{slice_id} {phase} evidence must be a mapping")
                continue
            for field in ("command_file", "output_file", "git_state_file", "summary_file"):
                rel = entry.get(field)
                if rel and not (workspace / "evidence" / rel).exists():
                    blockers.append(f"{slice_id} {phase} evidence file missing: {rel}")
    return blockers

def slice_budget_blockers(path: Path) -> list[str]:
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
        for field in ("iteration_budget", "rollback_point", "independent_verification", "failure_triage_notes"):
            if field not in item:
                blockers.append(f"{item.get('id', 'unknown')} missing {field}")
    return blockers

def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")

def hard_result(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "passed": passed, "detail": detail}
