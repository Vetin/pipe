"""Benchmark scenario definitions and lab initialization."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import CONTRACT_VERSION, read_yaml, write_yaml

SCENARIOS = {
    "auth-reset-password": {
        "required_files": ["feature.md", "architecture.md", "tech-design.md", "slices.yaml", "state.yaml", "execution.md"],
        "hard_checks": [
            "core_artifacts",
            "no_forbidden_files",
            "schema_valid",
            "docs_consulted_recorded",
            "slices_have_tdd",
            "slice_budget_declared",
            "no_auto_implementation",
            "state_has_no_next_skill",
        ],
    },
    "webhook-integration": {
        "required_files": ["feature.md", "architecture.md", "tech-design.md", "slices.yaml", "state.yaml", "execution.md"],
        "hard_checks": [
            "core_artifacts",
            "no_forbidden_files",
            "schema_valid",
            "docs_consulted_recorded",
            "slices_have_tdd",
            "slice_budget_declared",
            "state_has_no_next_skill",
        ],
    },
    "frontend-settings": {
        "required_files": ["feature.md", "architecture.md", "tech-design.md", "slices.yaml", "state.yaml", "execution.md"],
        "hard_checks": [
            "core_artifacts",
            "no_forbidden_files",
            "schema_valid",
            "docs_consulted_recorded",
            "slices_have_tdd",
            "slice_budget_declared",
            "state_has_no_next_skill",
        ],
    },
}

def scenario_doc(scenario: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_contract_version": CONTRACT_VERSION,
        "scenario": scenario,
        "mode": "offline",
        "required_files": data["required_files"],
        "hard_checks": data["hard_checks"],
        "soft_score_placeholders": [
            "requirement_quality",
            "architecture_clarity",
            "module_communication_quality",
            "adr_usefulness",
            "reuse_quality",
            "review_quality",
        ],
    }

def scorecard_doc(scorecard: str) -> dict[str, Any]:
    return {
        "artifact_contract_version": CONTRACT_VERSION,
        "scorecard": scorecard,
        "hard_checks_required": True,
        "soft_scores": "placeholder",
    }

def ensure_lab_initialized(root: Path) -> None:
    if not (root / "pipeline-lab/benchmarks/scenarios/auth-reset-password.yaml").exists():
        cmd_init_lab(argparse.Namespace())
