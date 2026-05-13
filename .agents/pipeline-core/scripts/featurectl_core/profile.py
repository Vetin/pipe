"""Project profiling and generated knowledge rendering for featurectl."""

from __future__ import annotations

import copy
import json
import os
import random
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .formatting import read_yaml, write_if_missing, write_text, write_yaml
from .shared import CONTRACT_VERSION, PROFILE_EXAMPLE_KEYS, FeatureCtlError, run_git, utc_now
from .docsets import next_skill_for_step

def ensure_init_tree(root: Path) -> None:
    dirs = [
        ".ai/feature-workspaces",
        ".ai/features",
        ".ai/features-archive",
        ".ai/knowledge",
        ".ai/pipeline-docs/global",
        ".agents/pipeline-core/references",
        ".agents/pipeline-core/references/generated-templates",
        ".agents/pipeline-core/scripts/schemas",
        ".agents/skills",
        ".agents/skill-lab/quarantine",
        ".agents/skill-lab/accepted",
        ".agents/skill-lab/rejected",
        "skills/superpowers/subagent-driven-development",
        "methodology/upstream",
        "methodology/docs-snapshots",
        "methodology/extracted",
        "pipeline-lab/benchmarks/scenarios",
        "pipeline-lab/benchmarks/suites",
        "pipeline-lab/envs/toy-monolith",
        "pipeline-lab/envs/modular-api",
        "pipeline-lab/scorecards",
        "tests/feature_pipeline",
    ]
    for dirname in dirs:
        (root / dirname).mkdir(parents=True, exist_ok=True)

    write_if_missing(
        root / ".ai/features/index.yaml",
        "artifact_contract_version: '0.1.0'\nfeatures: []\n",
    )
    write_if_missing(root / ".ai/features/overview.md", "# Feature Overview\n\nNo canonical features have been promoted yet.\n")
    write_if_missing(
        root / ".gitignore",
        "pipeline-lab/runs/\n.ai/logs/\n*.tmp\n__pycache__/\n.pytest_cache/\n",
    )


def build_project_profile(root: Path) -> dict[str, Any]:
    files = git_ls_files(root)
    visible_files = [path for path in files if not generated_or_vendor_path(path)]
    source_files = [path for path in visible_files if source_path(path)]
    test_files = [path for path in visible_files if test_path(path)]
    doc_files = [path for path in visible_files if doc_path(path)]
    contract_files = [path for path in visible_files if contract_path(path)]
    integration_files = [path for path in visible_files if integration_path(path)]
    module_dirs = summarize_module_dirs(visible_files)
    package_files = [path for path in visible_files if Path(path).name in package_manifest_names()]
    scripts = collect_project_scripts(root, package_files[:20])
    feature_signals = collect_feature_signals(root, visible_files, doc_files)
    canonical_features = collect_canonical_features(root)
    feature_catalog = build_feature_catalog(canonical_features, feature_signals)

    return {
        "artifact_contract_version": CONTRACT_VERSION,
        "generated_by": "featurectl.py init --profile-project",
        "generated_at": utc_now(),
        "project": {
            "name": infer_project_name(root, package_files),
            "root": ".",
            "branch": safe_git(root, "rev-parse", "--abbrev-ref", "HEAD") or "unknown",
            "head": safe_git(root, "rev-parse", "--short", "HEAD") or "unknown",
            "remote": safe_git(root, "remote", "get-url", "origin") or "none",
        },
        "counts": {
            "tracked_files": len(files),
            "profiled_files": len(visible_files),
            "source_files": len(source_files),
            "test_files": len(test_files),
            "doc_files": len(doc_files),
            "contract_files": len(contract_files),
            "integration_files": len(integration_files),
        },
        "package_manifests": package_files[:30],
        "scripts": scripts,
        "module_dirs": module_dirs,
        "source_examples": source_files[:40],
        "test_examples": test_files[:30],
        "doc_examples": doc_files[:30],
        "contract_examples": contract_files[:30],
        "integration_examples": integration_files[:30],
        "canonical_features": canonical_features,
        "feature_signals": feature_signals[:40],
        "feature_catalog": feature_catalog,
    }


def git_ls_files(root: Path) -> list[str]:
    try:
        output = run_git(root, "ls-files")
    except FeatureCtlError:
        return []
    return [line for line in output.splitlines() if line.strip()]


def generated_or_vendor_path(path: str) -> bool:
    parts = Path(path).parts
    if not parts:
        return True
    ignored_prefixes = (
        ".git",
        ".venv",
        "node_modules",
        "dist",
        "build",
        "coverage",
        ".pytest_cache",
        "__pycache__",
        ".ai/feature-workspaces",
        ".ai/features",
        ".ai/features-archive",
        ".ai/logs",
        "skills",
        "methodology",
        "pipeline-lab/showcases",
        "pipeline-lab/runs",
        "pipeline-lab/benchmarks/scenarios",
    )
    normalized = "/".join(parts)
    return any(normalized == prefix or normalized.startswith(f"{prefix}/") for prefix in ignored_prefixes)


def source_path(path: str) -> bool:
    suffix = Path(path).suffix.lower()
    if suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".kt", ".rb", ".php", ".cs", ".swift", ".vue", ".svelte"}:
        return False
    lowered = path.lower()
    return not test_path(path) and not lowered.endswith((".config.js", ".config.ts", ".d.ts"))


def test_path(path: str) -> bool:
    lowered = path.lower()
    return lowered.startswith(("test/", "tests/")) or any(part in lowered for part in ("/test/", "/tests/", "__tests__", ".test.", ".spec.", "_test."))


def doc_path(path: str) -> bool:
    lowered = path.lower()
    return lowered.endswith((".md", ".mdx", ".rst", ".adoc")) or lowered.startswith("docs/")


def contract_path(path: str) -> bool:
    lowered = path.lower()
    return any(token in lowered for token in ("openapi", "schema", "graphql", "proto", "contract", "migration", "event"))


def integration_path(path: str) -> bool:
    lowered = path.lower()
    return lowered.startswith((".github/", ".gitlab/", "docker", "deploy", "infra", "k8s", "helm")) or any(
        token in lowered for token in ("dockerfile", "compose", "terraform", "workflow", "integration")
    )


def package_manifest_names() -> set[str]:
    return {
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "poetry.lock",
        "pnpm-workspace.yaml",
        "turbo.json",
        "go.mod",
        "Cargo.toml",
        "pom.xml",
        "build.gradle",
        "Gemfile",
        "composer.json",
        "Makefile",
    }


def infer_project_name(root: Path, package_files: list[str]) -> str:
    for path in package_files:
        if Path(path).name == "package.json":
            try:
                package = json.loads((root / path).read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if package.get("name"):
                return str(package["name"])
    remote_name = infer_project_name_from_remote(safe_git(root, "remote", "get-url", "origin"))
    if remote_name:
        return remote_name
    return root.name


def infer_project_name_from_remote(remote: str | None) -> str:
    if not remote:
        return ""
    value = remote.strip().rstrip("/")
    if not value or value == "none":
        return ""
    if value.endswith(".git"):
        value = value[:-4]
    if ":" in value and not value.startswith(("http://", "https://", "ssh://")):
        value = value.rsplit(":", 1)[1]
    return value.rsplit("/", 1)[-1].strip()


def collect_project_scripts(root: Path, package_files: list[str]) -> list[dict[str, str]]:
    scripts: list[dict[str, str]] = []
    for path in package_files:
        file_name = Path(path).name
        if file_name == "package.json":
            try:
                package = json.loads((root / path).read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            for name, command in sorted((package.get("scripts") or {}).items()):
                scripts.append({"source": path, "name": str(name), "command": str(command)})
        elif file_name == "Makefile":
            content = read_repo_file(root, path)
            if content is None:
                continue
            for line in content.splitlines():
                if re.match(r"^[A-Za-z0-9_.-]+:", line) and not line.startswith("."):
                    scripts.append({"source": path, "name": line.split(":", 1)[0], "command": "make target"})
    return scripts[:40]


def summarize_module_dirs(files: list[str]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for path in files:
        parts = Path(path).parts
        if len(parts) < 2:
            continue
        top = parts[0]
        if top.startswith(".") and top not in {".agents", ".ai", ".github"}:
            continue
        counts[top] = counts.get(top, 0) + 1
        if top in {"apps", "packages", "services", "src"} and len(parts) > 2:
            nested = f"{parts[0]}/{parts[1]}"
            counts[nested] = counts.get(nested, 0) + 1
    return [{"path": path, "tracked_files": count} for path, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:30]]


def collect_feature_signals(root: Path, files: list[str], doc_files: list[str]) -> list[dict[str, str]]:
    signals: list[dict[str, str]] = []
    heading_re = re.compile(r"^#{1,3}\s+(.+)")
    signal_doc_files = [path for path in doc_files if feature_signal_candidate_path(path)]
    for path in signal_doc_files[:80]:
        content = read_repo_file(root, path)
        if content is None:
            continue
        for line in content.splitlines()[:300]:
            match = heading_re.match(line.strip())
            if not match:
                continue
            heading = re.sub(r"\s+", " ", match.group(1)).strip()
            if feature_signal_text(heading):
                signals.append({"source": path, "signal": heading, "kind": feature_signal_kind(path)})
                break
    for path in files:
        if not feature_signal_candidate_path(path):
            continue
        if test_path(path):
            continue
        path_signal = feature_signal_from_source_path(path)
        if path_signal:
            signals.append({"source": path, "signal": path_signal, "kind": feature_signal_kind(path)})
        if len(signals) >= 60:
            break
    return dedupe_signal_list(signals)


def feature_signal_candidate_path(path: str) -> bool:
    if Path(path).name in {"AGENTS.md"}:
        return False
    if path in {"plan.md", "vision.md", "features.md"}:
        return False
    if generated_showcase_report_path(path):
        return False
    blocked_prefixes = (
        ".ai/knowledge/",
        ".ai/feature-workspaces/",
        ".ai/features/",
        ".ai/features-archive/",
        ".ai/logs/",
        ".ai/",
        ".ai/pipeline-docs/",
        ".agents/skills/",
        ".agents/pipeline-core/references/",
        ".agents/pipeline-core/references/generated-templates/",
        ".github/",
        ".gitlab/",
        "pipeline-lab/showcases/",
        "pipeline-lab/runs/",
        "pipeline-lab/benchmarks/scenarios/",
    )
    return not any(path.startswith(prefix) for prefix in blocked_prefixes)


def feature_signal_kind(path: str) -> str:
    if path.startswith("pipeline-lab/"):
        return "lab_signal"
    return "detected"


def generated_showcase_report_path(path: str) -> bool:
    if not path.startswith("pipeline-lab/showcases/"):
        return False
    name = Path(path).name
    return name.endswith("-report.md") or name in {
        "validation.md",
        "native-emulation-validation-report.md",
        "native-emulation-judge-report.md",
        "pipeline-goal-validation-report.md",
        "init-profile-report.md",
    }


def feature_signal_text(text: str) -> bool:
    lowered = text.lower()
    ignored = {
        "license",
        "contributing",
        "installation",
        "usage",
        "table of contents",
        "build",
        "check",
        "quality checks",
        "integration tests command",
        "development workflow",
        "release notes",
        "changelog",
    }
    if lowered in ignored:
        return False
    return any(token in lowered for token in ("feature", "workflow", "api", "integration", "architecture", "module", "service", "pipeline", "dashboard"))


def feature_signal_from_source_path(path: str) -> str:
    parts = Path(path).parts
    lower_parts = [part.lower() for part in parts]
    blocked_parts = {
        "components",
        "component",
        "ui",
        "icons",
        "icon",
        "styles",
        "assets",
        "fixtures",
        "mocks",
        "mock",
        "tests",
        "test",
        "__tests__",
        "scripts",
        "generated",
    }
    for marker in ("features", "feature", "domains", "domain", "modules", "module"):
        if marker in lower_parts:
            index = lower_parts.index(marker)
            for candidate in parts[index + 1 : index + 4]:
                candidate_name = path_part_signal(candidate)
                if candidate.lower() not in blocked_parts and normalize_feature_catalog_name(candidate_name):
                    return candidate_name
    for marker in ("routes", "controllers", "services", "workflows", "integrations"):
        if marker in lower_parts:
            index = lower_parts.index(marker)
            if index + 1 < len(parts):
                candidate_name = path_part_signal(parts[index + 1])
                if normalize_feature_catalog_name(candidate_name):
                    return candidate_name
    lowered = path.lower()
    if any(token in lowered for token in ("controller", "service", "workflow", "integration")):
        stem = Path(path).stem.replace("-", " ").replace("_", " ")
        if normalize_feature_catalog_name(stem):
            return stem
    return ""


def path_part_signal(part: str) -> str:
    value = part
    while Path(value).suffix:
        value = Path(value).stem
    return value.replace("-", " ").replace("_", " ").replace(".", " ")


def dedupe_signal_list(signals: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, str]] = []
    for signal in signals:
        key = (signal["source"], signal["signal"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(signal)
    return deduped


def read_repo_file(root: Path, path: str) -> str | None:
    try:
        return (root / path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def build_feature_catalog(canonical_features: list[dict[str, str]], signals: list[dict[str, str]]) -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    for feature in canonical_features:
        name = feature.get("feature_key", "").strip()
        if not name:
            continue
        seen_names.add(name.lower())
        catalog.append(
            {
                "name": name,
                "kind": "canonical",
                "confidence": "high",
                "description": "Promoted feature memory recorded by the Native Feature Pipeline.",
                "source_count": 1,
                "sources": [feature.get("path", "")],
            }
        )

    grouped: dict[str, dict[str, Any]] = {}
    for signal in signals:
        name = normalize_feature_catalog_name(signal.get("signal", ""))
        if not name or name.lower() in seen_names:
            continue
        source = signal.get("source", "")
        entry = grouped.setdefault(
            name.lower(),
            {"name": name, "sources": [], "doc_sources": 0, "source_sources": 0, "lab_sources": 0},
        )
        if source and source not in entry["sources"]:
            entry["sources"].append(source)
            if signal.get("kind") == "lab_signal" or source.startswith("pipeline-lab/"):
                entry["lab_sources"] += 1
            if doc_path(source):
                entry["doc_sources"] += 1
            elif source_path(source):
                entry["source_sources"] += 1

    for entry in sorted(grouped.values(), key=lambda item: (-len(item["sources"]), item["name"].lower())):
        source_count = len(entry["sources"])
        confidence = feature_catalog_confidence(source_count, entry["doc_sources"], entry["source_sources"])
        kind = "lab_signal" if entry["lab_sources"] and entry["lab_sources"] == source_count else "detected"
        catalog.append(
            {
                "name": entry["name"],
                "kind": kind,
                "confidence": confidence,
                "description": feature_catalog_description(
                    entry["name"],
                    source_count,
                    entry["doc_sources"],
                    entry["source_sources"],
                    lab_sources=entry["lab_sources"],
                    kind=kind,
                ),
                "source_count": source_count,
                "sources": entry["sources"][:6],
            }
        )
        if len(catalog) >= 30:
            break
    return catalog


def normalize_feature_catalog_name(text: str) -> str:
    value = re.sub(r"\s+", " ", text or "").strip(" #-:._")
    value = re.sub(r"^(feature|workflow|service|controller|route|api|module)\s*[:/-]\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^(test|tests?)\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\b(ts|tsx|js|jsx|py|go|vue|yml|yaml|md|mdx)\b$", "", value, flags=re.IGNORECASE).strip()
    value = value.strip(" #-:._")
    if not value:
        return ""
    lowered = value.lower()
    generic = {
        "index",
        "overview",
        "readme",
        "skill",
        "openai",
        "configuration",
        "config",
        "setup",
        "install",
        "usage",
        "api",
        "service",
        "controller",
        "route",
        "routes",
        "page",
        "header",
        "wrapper",
        "action",
        "actions",
        "build",
        "check",
        "quality checks",
        "integration tests command",
        "development workflow",
        "gitignore",
        "agent docs",
        "features",
        "changed files",
        "release notes",
        "changelog",
        "autofix",
        "feature requests",
        "package",
        "breaking",
        "fixtures",
        "globalsetup",
        "globalteardown",
        "global setup",
        "global teardown",
        "integration tests",
        "admin seeder",
        "admin seeder js",
        "batch job seeder",
        "batch job seeder js",
        "bootstrap app",
        "architecture package structure",
        "architecture notes",
        "run the services in the background",
        "call helpers",
        "cart seeder",
        "claim seeder",
    }
    if lowered in generic or lowered.endswith((".schema", " seeder", " helpers")):
        return ""
    words = [word for word in re.split(r"[^A-Za-z0-9]+", value) if word]
    if len(words) == 1 and len(words[0]) < 4:
        return ""
    return " ".join(word if word.isupper() else word[:1].upper() + word[1:] for word in words)


def feature_catalog_confidence(source_count: int, doc_sources: int, source_sources: int) -> str:
    if source_count >= 3 and doc_sources:
        return "high"
    if source_count >= 2 or doc_sources or source_sources >= 2:
        return "medium"
    return "low"


def feature_catalog_description(
    name: str,
    source_count: int,
    doc_sources: int,
    source_sources: int,
    *,
    lab_sources: int = 0,
    kind: str = "detected",
) -> str:
    if kind == "lab_signal":
        return (
            f"{name} appears only in {lab_sources or source_count} pipeline-lab signal"
            f"{'s' if (lab_sources or source_count) != 1 else ''}; use lab_signal only for pipeline-lab or benchmark work."
        )
    sources = []
    if doc_sources:
        sources.append(f"{doc_sources} documentation signal{'s' if doc_sources != 1 else ''}")
    if source_sources:
        sources.append(f"{source_sources} source signal{'s' if source_sources != 1 else ''}")
    if not sources:
        sources.append(f"{source_count} repository signal{'s' if source_count != 1 else ''}")
    source_summary = " and ".join(sources)
    return f"{name} appears in {source_summary}; inspect the listed files before relying on this as architecture truth."


def collect_canonical_features(root: Path) -> list[dict[str, str]]:
    index_path = root / ".ai/features/index.yaml"
    features: list[dict[str, str]] = []
    if index_path.exists():
        try:
            data = read_yaml(index_path)
        except FeatureCtlError:
            data = {}
        for item in data.get("features") or []:
            if isinstance(item, dict):
                features.append(
                    {
                        "feature_key": str(item.get("feature_key") or item.get("key") or "unknown"),
                        "path": str(item.get("path") or item.get("canonical_path") or ""),
                    }
                )
    for card in sorted((root / ".ai/features").glob("*/*/feature-card.md")):
        features.append({"feature_key": "/".join(card.parts[-3:-1]), "path": str(card.relative_to(root))})
    return dedupe_canonical_features(features)


def dedupe_canonical_features(features: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for feature in features:
        key = feature.get("feature_key", "")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(feature)
    return deduped[:40]


def write_project_profile(root: Path, profile: dict[str, Any]) -> None:
    knowledge = root / ".ai/knowledge"
    knowledge.mkdir(parents=True, exist_ok=True)
    write_yaml(knowledge / "project-index.yaml", compact_project_index_profile(profile))
    write_yaml(knowledge / "profile-examples.yaml", profile_examples(profile))
    write_generated_doc(knowledge / "project-snapshot.md", render_project_snapshot(profile))
    write_generated_doc(knowledge / "project-overview.md", render_project_overview(profile))
    write_generated_doc(knowledge / "features-overview.md", render_features_overview(profile))
    write_generated_doc(knowledge / "discovered-signals.md", render_discovered_signals(profile))
    write_generated_doc(knowledge / "module-map.md", render_module_map(profile))
    write_generated_doc(knowledge / "architecture-overview.md", render_architecture_overview(profile))
    write_generated_doc(knowledge / "testing-overview.md", render_testing_overview(profile))
    write_generated_doc(knowledge / "contracts-overview.md", render_contracts_overview(profile))
    write_generated_doc(knowledge / "integration-map.md", render_integration_map(profile))


def sync_knowledge_canonical_features(root: Path) -> None:
    """Refresh canonical feature memory after promotion without storing local paths."""
    profile = build_project_profile(root)
    profile["generated_by"] = "featurectl.py promote canonical sync"
    profile["generated_at"] = utc_now()
    profile.setdefault("project", {})["root"] = "."
    knowledge = root / ".ai/knowledge"
    knowledge.mkdir(parents=True, exist_ok=True)
    write_yaml(knowledge / "project-index.yaml", compact_project_index_profile(profile))
    write_yaml(knowledge / "profile-examples.yaml", profile_examples(profile))
    write_text(knowledge / "features-overview.md", render_features_overview(profile))
    write_text(knowledge / "discovered-signals.md", render_discovered_signals(profile))


def compact_project_index_profile(profile: dict[str, Any]) -> dict[str, Any]:
    compact = copy.deepcopy(profile)
    for key in {*PROFILE_EXAMPLE_KEYS, "feature_signals", "feature_catalog"}:
        compact.pop(key, None)
    project = compact.get("project")
    if isinstance(project, dict):
        project.pop("branch", None)
        project.pop("head", None)
    return compact


def profile_examples(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_contract_version": CONTRACT_VERSION,
        "generated_by": profile.get("generated_by", "featurectl.py init --profile-project"),
        "generated_at": profile.get("generated_at", utc_now()),
        **{key: profile.get(key, []) for key in sorted(PROFILE_EXAMPLE_KEYS)},
    }


def write_generated_doc(path: Path, content: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    can_replace = not existing.strip() or "Status: initial" in existing or "Status: provisional" in existing or "Generated by featurectl project profile" in existing
    if can_replace:
        path.write_text(content, encoding="utf-8")


def render_project_snapshot(profile: dict[str, Any]) -> str:
    project = profile["project"]
    counts = profile["counts"]
    return f"""# Project Snapshot

Status: generated
Confidence: medium
Needs human review: yes
Generated by featurectl project profile: {profile['generated_at']}

## Identity

- Name: `{project['name']}`
- Branch: `{project['branch']}`
- HEAD: `{project['head']}`
- Remote: `{project['remote']}`

## Counts

- Tracked files: {counts['tracked_files']}
- Profiled files: {counts['profiled_files']}
- Source files: {counts['source_files']}
- Test files: {counts['test_files']}
- Documentation files: {counts['doc_files']}
- Contract/schema files: {counts['contract_files']}
- Integration/deployment files: {counts['integration_files']}

## Use In Feature Pipeline

Treat this as a source-backed map, not as final architecture truth. Feature
steps must still inspect the cited files before making behavior or design
claims.
"""


def render_project_overview(profile: dict[str, Any]) -> str:
    project = profile["project"]
    package_lines = bullet_list(profile["package_manifests"], empty="No package manifests detected.")
    catalog_lines = feature_catalog_lines(profile.get("feature_catalog", [])[:10], empty="No current feature catalog entries detected.")
    feature_lines = signal_lines(profile["feature_signals"][:12], empty="No feature-like signals detected from docs or paths.")
    return f"""# Project Overview

Status: generated
Confidence: medium
Needs human review: yes
Generated by featurectl project profile: {profile['generated_at']}

This repository appears to be `{project['name']}`.

## Package And Tooling Signals

{package_lines}

## Current Feature Picture

{catalog_lines}

## Detected Feature Signals

{feature_lines}

## Sources Inspected

- `git ls-files`
- `.ai/features/index.yaml`
- README/docs headings
- source, test, contract, and integration path patterns
"""


def render_features_overview(profile: dict[str, Any]) -> str:
    canonical = profile["canonical_features"]
    canonical_lines = "\n".join(f"- `{item['feature_key']}` from `{item['path']}`" for item in canonical) or "No canonical features have been promoted yet."
    return f"""# Features Overview

Status: generated
Confidence: medium
Needs human review: yes
Generated by featurectl project profile: {profile['generated_at']}

## Canonical Feature Memory

{canonical_lines}
"""


def render_discovered_signals(profile: dict[str, Any]) -> str:
    catalog = profile.get("feature_catalog", [])
    canonical = [item for item in catalog if item.get("kind") == "canonical"]
    noncanonical = [item for item in catalog if item.get("kind") != "canonical"]
    canonical_lines = signal_catalog_blocks(canonical, empty="No canonical signals detected.")
    noncanonical_lines = signal_catalog_blocks(noncanonical, empty="No noncanonical signals detected.")
    signal_text = signal_lines(profile["feature_signals"][:30], empty="No feature-like signals detected from docs or paths.")
    return f"""# Discovered Signals

Status: generated
Confidence: low
Needs human review: yes
Generated by featurectl project profile: {profile['generated_at']}

## Current Feature Picture

This file separates current repository signals into canonical feature memory and
noncanonical source leads. Canonical entries are safe retrieval anchors;
noncanonical entries require source inspection before reuse.

## Canonical Signals

Canonical signals are promoted feature memories. Prefer these before detected
or lab-only signals.

{canonical_lines}

## Noncanonical Signals

Noncanonical signals are source leads. They are not product or architecture truth
until the cited files are inspected. Use `lab_signal` only for pipeline-lab,
benchmark, showcase, or validation-tooling work.

{noncanonical_lines}

## Detected Feature Signals

{signal_text}
"""


def render_module_map(profile: dict[str, Any]) -> str:
    module_lines = "\n".join(f"- `{item['path']}`: {item['tracked_files']} tracked files" for item in profile["module_dirs"]) or "No module directories detected."
    source_lines = bullet_list(profile["source_examples"][:20], empty="No source examples detected.")
    return f"""# Module Map

Status: generated
Confidence: medium
Needs human review: yes
Generated by featurectl project profile: {profile['generated_at']}

## Directory Weight

{module_lines}

## Source Examples

{source_lines}
"""


def render_architecture_overview(profile: dict[str, Any]) -> str:
    packages = "\n".join(f"- `{path}`" for path in profile["package_manifests"][:15]) or "No package manifests detected."
    modules = "\n".join(f"- `{item['path']}`" for item in profile["module_dirs"][:10]) or "No module directories detected."
    return f"""# Architecture Overview

Status: generated
Confidence: medium
Needs human review: yes
Generated by featurectl project profile: {profile['generated_at']}

## Architecture Signals

{packages}

## Likely Module Boundaries

{modules}

## Feature Topology Reuse

Feature architecture artifacts must include a Mermaid feature topology and a
`Shared Knowledge Impact` section. Finish artifacts must record how completed
features update `.ai/knowledge/features-overview.md`,
`.ai/knowledge/architecture-overview.md`, `.ai/knowledge/module-map.md`, and
`.ai/knowledge/integration-map.md`.

Architecture claims for a feature must cite the exact modules and files read
during context discovery.
"""


def render_testing_overview(profile: dict[str, Any]) -> str:
    script_lines = "\n".join(f"- `{item['name']}` from `{item['source']}`: `{item['command']}`" for item in profile["scripts"] if "test" in item["name"].lower()) or "No test scripts detected."
    test_lines = bullet_list(profile["test_examples"][:20], empty="No test files detected.")
    return f"""# Testing Overview

Status: generated
Confidence: medium
Needs human review: yes
Generated by featurectl project profile: {profile['generated_at']}

## Test Commands

{script_lines}

## Test File Examples

{test_lines}
"""


def render_contracts_overview(profile: dict[str, Any]) -> str:
    return f"""# Contracts Overview

Status: generated
Confidence: medium
Needs human review: yes
Generated by featurectl project profile: {profile['generated_at']}

## Contract And Schema Examples

{bullet_list(profile['contract_examples'][:30], empty='No contract/schema files detected.')}
"""


def render_integration_map(profile: dict[str, Any]) -> str:
    return f"""# Integration Map

Status: generated
Confidence: medium
Needs human review: yes
Generated by featurectl project profile: {profile['generated_at']}

## Integration And Deployment Examples

{bullet_list(profile['integration_examples'][:30], empty='No integration/deployment files detected.')}
"""


def bullet_list(items: list[str], *, empty: str) -> str:
    return "\n".join(f"- `{item}`" for item in items) if items else empty


def signal_lines(items: list[dict[str, str]], *, empty: str) -> str:
    return "\n".join(f"- `{item['source']}` [{item.get('kind', 'detected')}]: {item['signal']}" for item in items) if items else empty


def feature_catalog_lines(items: list[dict[str, Any]], *, empty: str) -> str:
    if not items:
        return empty
    lines = []
    for item in items:
        sources = ", ".join(f"`{source}`" for source in item.get("sources", [])[:3] if source) or "`unknown`"
        kind = item.get("kind", "detected")
        reason_label = "Canonical reason" if kind == "canonical" else "Why not canonical"
        lines.extend(
            [
                f"- Signal: {item.get('name', 'unknown')}",
                f"  - Kind: {kind}",
                f"  - Confidence: {item.get('confidence', 'low')}",
                f"  - Source count: {item.get('source_count', 0)}",
                f"  - {reason_label}: {item.get('description', 'Inspect cited sources before using this feature signal.')}",
                f"  - Sources: {sources}",
            ]
        )
    return "\n".join(lines)


def signal_catalog_blocks(items: list[dict[str, Any]], *, empty: str) -> str:
    if not items:
        return empty
    blocks = []
    for item in items:
        name = item.get("name", "unknown")
        kind = item.get("kind", "detected")
        reason_label = "Canonical reason" if kind == "canonical" else "Why not canonical"
        sources = item.get("sources", [])[:6]
        source_lines = "\n".join(f"  - `{source}`" for source in sources if source) or "  - `unknown`"
        blocks.append(
            "\n".join(
                [
                    f"### {name}",
                    "",
                    f"- Kind: {kind}",
                    f"- Confidence: {item.get('confidence', 'low')}",
                    f"- Source count: {item.get('source_count', 0)}",
                    f"- {reason_label}: {item.get('description', 'Inspect cited sources before using this feature signal.')}",
                    "- Sources:",
                    source_lines,
                ]
            )
        )
    return "\n\n".join(blocks)


def safe_git(root: Path, *args: str) -> str | None:
    try:
        return run_git(root, *args).strip()
    except FeatureCtlError:
        return None


def render_apex(feature_key: str) -> str:
    return f"""# Apex: {feature_key}

## Read Order

1. `feature.yaml` - identity and paths
2. `state.yaml` - machine state
3. `execution.md` - run plan, approvals, docs consulted, next step
4. `feature.md` - product contract
5. `architecture.md` - system design
6. `tech-design.md` - implementation design
7. `slices.yaml` - TDD execution plan
8. `events.yaml` - machine-readable execution events
9. `evidence/manifest.yaml` - evidence index
10. `reviews/` - review results

## Main Artifacts

- Feature contract: `feature.md`
- Architecture: `architecture.md`
- Technical design: `tech-design.md`
- Implementation plan: `slices.yaml`
- ADRs: `adrs/`
- Contracts: `contracts/`
- Evidence: `evidence/`
- Reviews: `reviews/`
- Execution log: `execution.md`
- Machine events: `events.yaml`

## Current Status

See `state.yaml`.

## Next Action

See `execution.md`.
"""


def render_execution(title: str, feature_key: str, stop_point: str) -> str:
    now = utc_now()
    return f"""# Execution Log: {feature_key}

## User Request

{title}

## Run Plan

Mode: planning autorun
Stop point: {stop_point}
Implementation allowed: no

Planned steps:

1. Context discovery
2. Feature contract
3. Architecture
4. Technical design
5. Slicing
6. Readiness summary

## Non-Delegable Checkpoints

Stop and ask user before:

- destructive command
- production data migration
- new production dependency
- public API breaking change
- security model change
- credential/secret handling
- paid external service
- license-impacting dependency

## Clarifying Questions

None currently recorded.

## Assumptions

None currently recorded.

## Docs Consulted

None yet.

## Event Log

- {now} event_type=run_initialized step=context next=nfp-01-context

## History

- Initial current step: context
- Initial next step: nfp-01-context

## Current Run State

Current step: context
Next recommended skill: nfp-01-context
Blocking issues: none
Last updated: {now}
"""
