"""Pipeline docset loading helpers for featurectl."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .formatting import read_yaml
from .shared import CONTRACT_VERSION, FeatureCtlError, VALID_STEPS

def next_skill_for_step(step: str | None) -> str:
    mapping = {
        "context": "nfp-01-context",
        "feature_contract": "nfp-02-feature-contract",
        "architecture": "nfp-03-architecture",
        "tech_design": "nfp-04-tech-design",
        "slicing": "nfp-05-slicing",
        "readiness": "nfp-06-readiness",
        "worktree": "nfp-07-worktree",
        "tdd_implementation": "nfp-08-tdd-implementation",
        "review": "nfp-09-review",
        "verification": "nfp-10-verification",
        "finish": "nfp-11-finish",
        "promote": "nfp-12-promote",
    }
    return mapping.get(step or "", "unknown")


def normalize_step_name(step: str) -> str:
    normalized = step.strip().lower().replace("_", "-")
    valid_steps = {
        "intake",
        "context",
        "feature-contract",
        "architecture",
        "tech-design",
        "slicing",
        "readiness",
        "worktree",
        "tdd-implementation",
        "review",
        "verification",
        "finish",
        "promote",
    }
    if normalized not in valid_steps:
        raise FeatureCtlError(f"unknown docset step: {step}")
    return normalized


def load_docset(root: Path, step: str) -> dict[str, Any]:
    index_path = root / ".ai/pipeline-docs/docset-index.yaml"
    if not index_path.exists():
        raise FeatureCtlError("missing .ai/pipeline-docs/docset-index.yaml")
    index = read_yaml(index_path)
    rel = (index.get("steps") or {}).get(step)
    if not rel:
        raise FeatureCtlError(f"docset index has no entry for step: {step}")
    docset_path = root / ".ai/pipeline-docs" / rel
    docset = read_yaml(docset_path)
    if docset.get("artifact_contract_version") != CONTRACT_VERSION:
        raise FeatureCtlError(f"docset artifact_contract_version mismatch in {docset_path}")
    if docset.get("step") != step:
        raise FeatureCtlError(f"docset step mismatch in {docset_path}")
    return docset


def missing_docs(root: Path, docset: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for key in ("required_docs", "optional_docs"):
        for rel in docset.get(key, []) or []:
            if not (root / rel).exists():
                missing.append(rel)
    return missing


def print_docs(label: str, root: Path, docs: list[str], *, check_exists: bool = True) -> None:
    print(f"{label}:")
    if not docs:
        print("  none")
        return
    for rel in docs:
        suffix = ""
        if check_exists and not (root / rel).exists():
            suffix = " (missing)"
        print(f"  - {rel}{suffix}")
