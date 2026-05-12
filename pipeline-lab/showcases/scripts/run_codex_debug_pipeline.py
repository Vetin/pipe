#!/usr/bin/env python3
"""Run Codex showcase cases with explicit mock, dry-run, or real execution."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[3]
E2E_RUNNER = ROOT / "pipeline-lab/showcases/scripts/run_codex_e2e_case.py"
DEFAULT_CONFIG = ROOT / "pipeline-lab/showcases/codex-e2e-cases.yaml"
DEFAULT_OUTPUT_DIR = ROOT / "pipeline-lab/showcases/codex-debug-runs"
REQUIRED_CONTEXT_PATHS = (
    "AGENTS.md",
    ".agents/pipeline-core",
    ".ai/pipeline-docs",
    "skills/native-feature-pipeline/references",
)
REQUIRED_ARTIFACT_NAMES = ("feature.md", "architecture.md", "tech-design.md", "slices.yaml")
FORBIDDEN_PROMPT_TOKENS = (
    "Read and follow every NFP skill doc in order",
    "nfp-00-intake",
    "nfp-12-promote",
)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def resolve_output_dir(path: str) -> Path:
    output_dir = Path(path).expanduser()
    if not output_dir.is_absolute():
        output_dir = (ROOT / output_dir).resolve()
    return output_dir


def ensure_real_codex(codex_bin: str) -> str:
    if os.sep in codex_bin or (os.altsep and os.altsep in codex_bin):
        candidate = Path(codex_bin).expanduser()
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
        raise RuntimeError(f"real Codex executable is missing or not executable: {candidate}")
    resolved = shutil.which(codex_bin)
    if not resolved:
        raise RuntimeError(f"real Codex executable is missing from PATH: {codex_bin}")
    return resolved


def write_fake_codex(path: Path) -> None:
    script = """#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path

args = sys.argv[1:]
if not args or args[0] != "exec":
    raise SystemExit("fake codex only supports `exec`")
repo = Path(args[args.index("-C") + 1])
out = Path(args[args.index("-o") + 1])
prompt = args[-1]

case_match = re.search(r"Case id:\\s*([^\\n]+)", prompt)
branch_match = re.search(r"Target branch name:\\s*([^\\n]+)", prompt)
case_id = (case_match.group(1).strip() if case_match else "mock-feature").replace("/", "-")
branch = branch_match.group(1).strip() if branch_match else "mock-branch"
workspace = repo / ".ai" / "feature-workspaces" / "debug" / case_id
workspace.mkdir(parents=True, exist_ok=True)

artifacts = {
    "feature.md": f"# Feature: {case_id}\\n\\n## Intent\\n\\nImplement the requested debug feature through the native pipeline.\\n",
    "architecture.md": f"# Architecture: {case_id}\\n\\n## Feature Topology\\n\\n```mermaid\\ngraph TD\\n  User[User feature request] --> Codex[Codex worker]\\n  Codex --> Pipeline[Native Feature Pipeline]\\n  Pipeline --> Artifacts[Generated artifacts]\\n```\\n",
    "tech-design.md": f"# Technical Design: {case_id}\\n\\n## Implementation Summary\\n\\nThe mock worker proves prompt, context, artifact, and commit handling.\\n",
    "slices.yaml": "slices:\\n  - id: S-001\\n    title: Mock debug implementation\\n    status: complete\\n",
    "feature-card.md": f"# Feature Card: {case_id}\\n\\n- Status: complete\\n- Evidence: fake Codex debug run\\n",
}
for name, content in artifacts.items():
    (workspace / name).write_text(content, encoding="utf-8")

(repo / "README.codex-debug.md").write_text(
    f"# Codex Debug Implementation\\n\\nCase `{case_id}` was implemented by the mock Codex debug worker.\\n",
    encoding="utf-8",
)

subprocess.run(["git", "add", "."], cwd=repo, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
subprocess.run(
    ["git", "commit", "-m", f"Implement {case_id} via mock Codex debug"],
    cwd=repo,
    check=False,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)
commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout.strip()

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(
    f"branch: {branch}\\ncommit: {commit}\\nchanged files: .ai/feature-workspaces/debug/{case_id}, README.codex-debug.md\\n",
    encoding="utf-8",
)
print(json.dumps({
    "repo": str(repo),
    "branch": branch,
    "commit": commit,
    "has_native_pipeline": "normal user feature request" in prompt and ("Progress through these outcomes" in prompt or "bounded completion smoke case" in prompt),
    "no_direct_skill_invocations": "nfp-00-intake" not in prompt and "nfp-12-promote" not in prompt,
    "fresh_worktree": "fresh feature worktree" in prompt and "do not implement in the base checkout" in prompt,
    "generated_artifacts": sorted(artifacts),
}))
"""
    write_text(path, script)
    path.chmod(0o755)


def e2e_command(args: argparse.Namespace, run_dir: Path, codex_bin: str) -> list[str]:
    e2e_output = run_dir / "e2e"
    cmd = [
        sys.executable,
        str(E2E_RUNNER),
        "--config",
        str(Path(args.config).expanduser().resolve()),
        "--output-dir",
        str(e2e_output),
        "--run-id",
        args.run_id,
        "--codex-bin",
        codex_bin,
        "--execution-mode",
        args.mode,
        "--timeout-seconds",
        str(args.timeout_seconds),
    ]
    if args.all:
        cmd.append("--all")
    for case in args.case or []:
        cmd.extend(["--case", case])
    for codex_arg in args.codex_arg or []:
        cmd.extend(["--codex-arg", codex_arg])
    if args.allow_dirty:
        cmd.append("--allow-dirty")
    if args.reset_to_base:
        cmd.append("--reset-to-base")
    if args.prompt_profile:
        cmd.extend(["--prompt-profile", args.prompt_profile])
    if args.replace_existing_worktree or args.clean:
        cmd.append("--replace-existing-worktree")
    if args.mode == "dry-run":
        cmd.append("--dry-run")
    return cmd


def load_json_array(path: Path) -> list[str]:
    return json.loads(path.read_text(encoding="utf-8"))


def changed_files(repo: Path, before_head: str | None, after_head: str | None) -> list[str]:
    if not before_head or not after_head or before_head == after_head:
        return []
    result = run(["git", "diff", "--name-only", before_head, after_head], repo)
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def collect_pipeline_artifacts(repo: Path, before_head: str | None, after_head: str | None) -> tuple[dict[str, list[str]], str]:
    feature_root = repo / ".ai/feature-workspaces"
    artifacts: dict[str, list[str]] = {name: [] for name in REQUIRED_ARTIFACT_NAMES}
    changed = changed_files(repo, before_head, after_head)
    changed_artifacts: dict[str, list[str]] = {name: [] for name in REQUIRED_ARTIFACT_NAMES}
    for rel_path in changed:
        path = Path(rel_path)
        if not rel_path.startswith(".ai/feature-workspaces/"):
            continue
        for name in REQUIRED_ARTIFACT_NAMES:
            if path.name == name:
                changed_artifacts[name].append(str(repo / path))
    if any(changed_artifacts.values()):
        return changed_artifacts, "changed_files"

    if not feature_root.exists():
        return artifacts, "missing_feature_root"
    for name in REQUIRED_ARTIFACT_NAMES:
        matches = sorted(path for path in feature_root.rglob(name) if path.is_file())
        artifacts[name] = [str(path) for path in matches[:20]]
    return artifacts, "workspace_scan_fallback"


def validate_run(manifest: dict[str, Any], expected_mode: str) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    prompt_path = Path(manifest["prompt"])
    command_path = Path(manifest["command"])
    output_path = Path(manifest["output"])
    repo = Path(manifest["repo"])
    prompt = prompt_path.read_text(encoding="utf-8", errors="replace") if prompt_path.exists() else ""
    command = load_json_array(command_path) if command_path.exists() else []
    output = output_path.read_text(encoding="utf-8", errors="replace") if output_path.exists() else ""
    artifacts, artifact_source = collect_pipeline_artifacts(repo, manifest.get("before_head"), manifest.get("after_head"))

    if manifest.get("execution_mode") != expected_mode:
        failures.append(f"execution_mode is {manifest.get('execution_mode')}, expected {expected_mode}")
    if bool(manifest.get("uses_real_codex")) != (expected_mode == "real"):
        failures.append("uses_real_codex flag does not match requested mode")
    if int(manifest.get("returncode") or 0) != 0:
        failures.append(f"Codex return code is {manifest.get('returncode')}")
    if manifest.get("timed_out"):
        failures.append("Codex invocation timed out")
    prompt_profile = manifest.get("prompt_profile")
    if prompt_profile not in {"full-native", "outcome-smoke"}:
        failures.append(f"prompt_profile is {prompt_profile}, expected full-native or outcome-smoke")
    if "normal user feature request" not in prompt:
        failures.append("prompt does not emulate a native user feature request")
    if prompt_profile == "full-native" and "Progress through these outcomes" not in prompt:
        failures.append("full-native prompt is missing native outcome progression")
    if prompt_profile == "outcome-smoke" and "bounded completion smoke case" not in prompt:
        failures.append("outcome-smoke prompt is missing bounded smoke framing")
    forbidden = [token for token in FORBIDDEN_PROMPT_TOKENS if token in prompt]
    if forbidden:
        failures.append("prompt contains direct internal skill invocation tokens: " + ", ".join(forbidden))
    missing_context = [rel for rel in REQUIRED_CONTEXT_PATHS if not (repo / rel).exists()]
    if missing_context:
        failures.append("worktree is missing installed pipeline context: " + ", ".join(missing_context))
    if "--dangerously-bypass-approvals-and-sandbox" not in command or "-C" not in command:
        failures.append("codex command is missing required workspace/sandbox arguments")
    if expected_mode == "mock" and '"has_native_pipeline": true' not in output:
        failures.append("mock run did not prove native pipeline prompt detection")
    if expected_mode == "real" and "fake" in str(manifest.get("codex_bin", "")).lower():
        failures.append("real mode is using a fake Codex binary")
    if expected_mode != "dry-run":
        missing_artifacts = [name for name, paths in artifacts.items() if not paths]
        if missing_artifacts:
            failures.append("missing generated pipeline artifacts: " + ", ".join(missing_artifacts))
    else:
        warnings.append("dry-run validates prompt and command only; no implementation artifacts are expected")
    if expected_mode != "dry-run" and artifact_source == "workspace_scan_fallback":
        warnings.append("pipeline artifacts were found by workspace scan because no artifact changes were visible between before_head and after_head")

    return {
        "case": manifest["case"],
        "mode": expected_mode,
        "status": "fail" if failures else "pass",
        "uses_real_codex": bool(manifest.get("uses_real_codex")),
        "returncode": manifest.get("returncode"),
        "timed_out": bool(manifest.get("timed_out")),
        "repo": manifest["repo"],
        "target_branch": manifest["target_branch"],
        "after_head": manifest["after_head"],
        "after_status": manifest["after_status"],
        "artifact_source": artifact_source,
        "artifacts": artifacts,
        "failures": failures,
        "warnings": warnings,
        "source_repo": manifest.get("source_repo"),
    }


def compare_with_current_tests() -> dict[str, Any]:
    test_path = ROOT / "tests/feature_pipeline/test_codex_e2e_runner.py"
    content = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
    current_uses_fake = "write_fake_codex" in content and "--codex-bin" in content
    return {
        "current_unit_test_path": str(test_path),
        "current_unit_tests_use_fake_codex": current_uses_fake,
        "new_runner_advantage": "explicit execution_mode, real Codex preflight, timeout metadata, generated artifact validation, and comparison report",
        "recommendation": "Keep fast mock unit tests, and use this debug runner for scalable real Codex smoke runs and artifact-quality review.",
    }


def render_validation_md(summary: dict[str, Any]) -> str:
    lines = [
        "# Codex Debug Pipeline Validation",
        "",
        f"- Run id: `{summary['run_id']}`",
        f"- Mode: `{summary['mode']}`",
        f"- Uses real Codex: `{str(summary['uses_real_codex']).lower()}`",
        f"- Status: `{summary['status']}`",
        "",
        "## Case Results",
        "",
        "| Case | Mode | Real Codex | Return | Status | Artifacts |",
        "| --- | --- | --- | ---: | --- | ---: |",
    ]
    for result in summary["results"]:
        artifact_count = sum(1 for paths in result["artifacts"].values() if paths)
        lines.append(
            f"| `{result['case']}` | `{result['mode']}` | `{str(result['uses_real_codex']).lower()}` | "
            f"{result['returncode']} | `{result['status']}` | {artifact_count}/{len(REQUIRED_ARTIFACT_NAMES)} |"
        )
    lines.extend(["", "## Findings", ""])
    findings = summary.get("weaknesses") or ["No weaknesses detected by deterministic validation."]
    for finding in findings:
        lines.append(f"- {finding}")
    return "\n".join(lines) + "\n"


def render_comparison_md(summary: dict[str, Any]) -> str:
    comparison = summary["comparison"]
    lines = [
        "# Codex E2E Runner Comparison",
        "",
        "## Current Tests",
        "",
        f"- Unit test path: `{comparison['current_unit_test_path']}`",
        f"- Uses fake Codex: `{str(comparison['current_unit_tests_use_fake_codex']).lower()}`",
        "",
        "## Selected Debug Runner",
        "",
        f"- Mode: `{summary['mode']}`",
        f"- Case count: `{summary['case_count']}`",
        f"- Advantage: {comparison['new_runner_advantage']}",
        f"- Recommendation: {comparison['recommendation']}",
    ]
    return "\n".join(lines) + "\n"


def render_commands(cmd: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in cmd) + "\n"


def portable_replacements(run_dir: Path, summary: dict[str, Any]) -> list[tuple[str, str]]:
    work_paths: list[Path] = []
    for result in summary.get("results") or []:
        for key in ("repo", "source_repo"):
            value = result.get(key)
            if value:
                work_paths.append(Path(value).expanduser())
        for paths in (result.get("artifacts") or {}).values():
            work_paths.extend(Path(value).expanduser() for value in paths)

    work_root: Path | None = None
    if work_paths:
        try:
            work_root = Path(os.path.commonpath([str(path) for path in work_paths]))
        except ValueError:
            work_root = None
        if work_root and work_root.is_file():
            work_root = work_root.parent

    replacements = [
        (str(run_dir), "$RUN_DIR"),
        (str(run_dir.resolve()), "$RUN_DIR"),
        (str(ROOT), "$ROOT"),
        (str(ROOT.resolve()), "$ROOT"),
    ]
    if work_root:
        replacements.extend(
            [
                (str(work_root), "$WORK_ROOT"),
                (str(work_root.resolve()), "$WORK_ROOT"),
            ]
        )
    replacements = sorted(set(replacements), key=lambda item: len(item[0]), reverse=True)
    return [(actual, token) for actual, token in replacements if actual and actual != "/"]


def normalize_value(value: Any, replacements: list[tuple[str, str]]) -> Any:
    if isinstance(value, str):
        for actual, token in replacements:
            value = value.replace(actual, token)
        return value
    if isinstance(value, list):
        return [normalize_value(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: normalize_value(item, replacements) for key, item in value.items()}
    return value


def normalize_text_artifacts(run_dir: Path, replacements: list[tuple[str, str]]) -> None:
    suffixes = {".json", ".log", ".md", ".sh", ".txt", ".yaml", ".yml"}
    for path in sorted(run_dir.rglob("*")):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        normalized = normalize_value(text, replacements)
        if normalized != text:
            path.write_text(normalized, encoding="utf-8")


def run_debug(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = resolve_output_dir(args.output_dir)
    run_dir = output_dir / args.run_id
    if args.clean and run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    codex_bin = args.codex_bin
    if args.mode == "mock":
        codex_bin = str(run_dir / "fake-codex.py")
        write_fake_codex(Path(codex_bin))
    elif args.mode == "real":
        codex_bin = ensure_real_codex(args.codex_bin)

    cmd = e2e_command(args, run_dir, codex_bin)
    write_text(run_dir / "debug-command.sh", render_commands(cmd))
    result = run(cmd, ROOT)
    write_text(run_dir / "debug-output.log", result.stdout)
    e2e_summary_path = run_dir / "e2e" / f"summary-{args.run_id}.yaml"
    if not e2e_summary_path.exists():
        raise RuntimeError(f"E2E runner did not produce summary: {e2e_summary_path}\n{result.stdout}")
    e2e_summary = read_yaml(e2e_summary_path)
    results = [validate_run(manifest, args.mode) for manifest in e2e_summary.get("runs") or []]
    weaknesses = [
        f"{item['case']}: {message}"
        for item in results
        for message in (item.get("failures") or item.get("warnings") or [])
    ]
    summary = {
        "artifact_contract_version": "0.1.0",
        "run_id": args.run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "path_mode": "actual",
        "uses_real_codex": args.mode == "real",
        "codex_bin": codex_bin,
        "case_count": len(results),
        "status": "fail" if result.returncode != 0 or any(item["status"] == "fail" for item in results) else "pass",
        "e2e_returncode": result.returncode,
        "e2e_summary": str(e2e_summary_path),
        "comparison": compare_with_current_tests(),
        "results": results,
        "weaknesses": weaknesses,
    }
    if args.portable_output:
        replacements = portable_replacements(run_dir, summary)
        summary = normalize_value(summary, replacements)
        summary["path_mode"] = "portable"
    write_text(run_dir / "summary.yaml", yaml.safe_dump(summary, sort_keys=False))
    write_text(run_dir / "validation.md", render_validation_md(summary))
    write_text(run_dir / "comparison.md", render_comparison_md(summary))
    if args.portable_output:
        normalize_text_artifacts(run_dir, replacements)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="YAML case file")
    parser.add_argument("--case", action="append", help="Case id to run; repeat for multiple cases")
    parser.add_argument("--all", action="store_true", help="Run all cases in config order")
    parser.add_argument("--mode", choices=("mock", "dry-run", "real"), default="mock", help="Execution mode")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for debug run artifacts")
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"), help="Stable run id")
    parser.add_argument("--codex-bin", default=os.environ.get("CODEX_BIN", "codex"), help="Codex executable for real mode")
    parser.add_argument("--codex-arg", action="append", default=[], help="Extra argument passed to codex exec")
    parser.add_argument("--timeout-seconds", type=int, default=1800, help="Codex invocation timeout")
    parser.add_argument("--allow-dirty", action="store_true", help="Allow dirty source repositories")
    parser.add_argument("--reset-to-base", action="store_true", help="Reset source repository to case base_ref first")
    parser.add_argument("--clean", action="store_true", help="Remove existing debug run directory before running")
    parser.add_argument("--replace-existing-worktree", action="store_true", help="Forward replacement permission to the E2E runner")
    parser.add_argument("--prompt-profile", choices=("full-native", "outcome-smoke"), default=None, help="Forward prompt profile to the E2E runner")
    parser.add_argument("--portable-output", action="store_true", help="Normalize generated text artifacts with stable path tokens")
    args = parser.parse_args(argv)

    try:
        summary = run_debug(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"summary: {resolve_output_dir(args.output_dir) / args.run_id / 'summary.yaml'}")
    print(f"mode: {summary['mode']}")
    print(f"uses_real_codex: {str(summary['uses_real_codex']).lower()}")
    print(f"status: {summary['status']}")
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
