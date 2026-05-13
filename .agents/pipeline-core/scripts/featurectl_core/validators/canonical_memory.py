"""Canonical feature memory and source-of-truth validators."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..formatting import read_yaml
from ..shared import FeatureCtlError


def validate_repository_source_truth(root: Path, workspace: Path, feature: dict[str, Any], state: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    index_path = root / ".ai/features/index.yaml"
    if not index_path.exists():
        return blockers
    try:
        index = read_yaml(index_path)
    except FeatureCtlError as exc:
        return [str(exc)]
    features = index.get("features") or []
    if not isinstance(features, list):
        return ["features index features must be a list"]

    overview_path = root / ".ai/features/overview.md"
    overview = overview_path.read_text(encoding="utf-8") if overview_path.exists() else ""
    complete_keys: set[str] = set()
    for item in features:
        if not isinstance(item, dict):
            blockers.append("features index entries must be mappings")
            continue
        feature_key = str(item.get("feature_key") or "")
        status = item.get("status")
        path = str(item.get("path") or "")
        if not feature_key:
            blockers.append("features index entry missing feature_key")
            continue
        if status == "complete":
            complete_keys.add(feature_key)
            if feature_key not in overview:
                blockers.append(f".ai/features/overview.md missing canonical feature {feature_key}")
            canonical_dir = root / path if path else root / ".ai/features" / feature_key
            canonical_feature_path = canonical_dir / "feature.yaml"
            if not canonical_feature_path.exists():
                blockers.append(f"canonical feature {feature_key} missing feature.yaml")
                continue
            canonical_feature = read_yaml(canonical_feature_path)
            if canonical_feature.get("status") == "draft":
                blockers.append(f"canonical feature {feature_key} is indexed complete but feature.yaml status is draft")

    if complete_keys:
        knowledge_overview_path = root / ".ai/knowledge/features-overview.md"
        if not knowledge_overview_path.exists():
            blockers.append(".ai/knowledge/features-overview.md missing canonical feature memory")
        else:
            knowledge_overview = knowledge_overview_path.read_text(encoding="utf-8")
            for feature_key in sorted(complete_keys):
                if feature_key not in knowledge_overview:
                    blockers.append(f".ai/knowledge/features-overview.md missing canonical feature {feature_key}")

        project_index_path = root / ".ai/knowledge/project-index.yaml"
        if not project_index_path.exists():
            blockers.append(".ai/knowledge/project-index.yaml missing canonical feature memory")
        else:
            project_index = read_yaml(project_index_path)
            project_root = str((project_index.get("project") or {}).get("root") or "")
            if project_root and Path(project_root).is_absolute():
                blockers.append(".ai/knowledge/project-index.yaml project.root must be repository-relative")
            canonical_items = project_index.get("canonical_features") or []
            canonical_keys = {
                str(item.get("feature_key"))
                for item in canonical_items
                if isinstance(item, dict) and item.get("feature_key")
            }
            for feature_key in sorted(complete_keys):
                if feature_key not in canonical_keys:
                    blockers.append(f".ai/knowledge/project-index.yaml canonical_features missing {feature_key}")

    if feature.get("status") == "promoted" and state.get("lifecycle") not in {"promoted-readonly", "archived"}:
        blockers.append("promoted workspace must use promoted-readonly or archived lifecycle")
    if feature.get("status") == "promoted-readonly":
        if state.get("lifecycle") != "promoted-readonly":
            blockers.append("promoted-readonly workspace must set lifecycle promoted-readonly")
        if state.get("read_only") is not True:
            blockers.append("promoted-readonly workspace must set read_only true")

    active_workspaces = sorted((root / ".ai/feature-workspaces").glob("*/*/feature.yaml"))
    if is_active_workspace(root, workspace):
        active_workspaces.append(workspace / "feature.yaml")
    seen_active_paths: set[Path] = set()
    for active_feature_path in active_workspaces:
        active_feature_path = active_feature_path.resolve()
        if active_feature_path in seen_active_paths or not active_feature_path.exists():
            continue
        seen_active_paths.add(active_feature_path)
        active_workspace = active_feature_path.parent
        active_feature = read_yaml(active_feature_path)
        active_key = active_feature.get("feature_key")
        if active_key not in complete_keys:
            continue
        active_state_path = active_workspace / "state.yaml"
        active_state = read_yaml(active_state_path) if active_state_path.exists() else {}
        if not workspace_inactive_lifecycle(active_feature, active_state):
            blockers.append(f"active workspace {active_key} duplicates complete canonical feature without inactive lifecycle")
    return blockers


def workspace_inactive_lifecycle(feature: dict[str, Any], state: dict[str, Any]) -> bool:
    if feature.get("status") in {"promoted-readonly", "archived"}:
        return True
    return state.get("lifecycle") in {"promoted-readonly", "archived", "abandoned"}


def is_active_workspace(root: Path, workspace: Path) -> bool:
    resolved = workspace.resolve()
    for inactive_root in (root / ".ai/features", root / ".ai/features-archive"):
        try:
            resolved.relative_to(inactive_root.resolve())
            return False
        except ValueError:
            pass
    try:
        resolved.relative_to((root / ".ai/feature-workspaces").resolve())
    except ValueError:
        return (workspace / "state.yaml").exists() and (workspace / "feature.yaml").exists()
    if not (workspace / "state.yaml").exists() or not (workspace / "feature.yaml").exists():
        return False
    state = read_yaml(workspace / "state.yaml")
    feature = read_yaml(workspace / "feature.yaml")
    return not workspace_inactive_lifecycle(feature, state)
