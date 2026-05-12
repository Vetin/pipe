#!/usr/bin/env python3
"""Run stable Codex E2E feature implementation cases in fresh worktrees."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = ROOT / "pipeline-lab/showcases/codex-e2e-cases.yaml"
DEFAULT_OUTPUT_DIR = ROOT / "pipeline-lab/showcases/codex-e2e-runs"
EXECUTION_MODES = {"mock", "dry-run", "real"}
PROMPT_PROFILES = {"full-native", "outcome-smoke"}
NATIVE_PHASES = [
    "intake and repository context discovery",
    "feature contract with measurable requirements and acceptance criteria",
    "architecture grounded in inspected modules and system boundaries",
    "technical design covering contracts, data, errors, flags, and tests",
    "dependency-aware implementation slices",
    "readiness gates for destructive, security, data, and public API risks",
    "test-first implementation with red/green evidence",
    "adversarial review and fix verification",
    "final verification, feature memory, promotion, and commit",
]


def run(cmd: list[str], cwd: Path, check: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed in {cwd}\n{result.stdout}")
    return result


def load_config(path: Path) -> dict[str, Any]:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or not isinstance(config.get("cases"), dict):
        raise RuntimeError(f"{path} must contain a cases mapping")
    return config


def resolve_path(path: str, config_path: Path) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate
    config_relative = config_path.parent / candidate
    if config_relative.exists():
        return config_relative.resolve()
    return (ROOT / candidate).resolve()


def case_source_spec(case: dict[str, Any]) -> tuple[str, str]:
    codebase = case.get("original_codebase") or {}
    repo_path = codebase.get("repo_path") or case.get("repo_path")
    template_path = codebase.get("template_path") or case.get("template_path")
    if bool(repo_path) == bool(template_path):
        raise RuntimeError("case must define exactly one of original_codebase.repo_path or original_codebase.template_path")
    if repo_path:
        return "repo_path", str(repo_path)
    return "template_path", str(template_path)


def init_template_repo(template_path: Path, source_repo: Path, replace_existing: bool) -> None:
    if source_repo.exists():
        if not replace_existing:
            raise RuntimeError(
                f"materialized source repo already exists: {source_repo}; "
                "rerun with --replace-existing-worktree"
            )
        shutil.rmtree(source_repo)
    source_repo.parent.mkdir(parents=True, exist_ok=True)
    ignore = shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache")
    shutil.copytree(template_path, source_repo, ignore=ignore)
    run(["git", "init", "-b", "main"], source_repo, check=True)
    run(["git", "config", "user.email", "codex-e2e@example.invalid"], source_repo, check=True)
    run(["git", "config", "user.name", "Codex E2E Runner"], source_repo, check=True)
    run(["git", "add", "."], source_repo, check=True)
    status = git_status(source_repo)
    if status:
        run(["git", "commit", "-m", "seed template source"], source_repo, check=True)
    else:
        run(["git", "commit", "--allow-empty", "-m", "seed template source"], source_repo, check=True)


def case_repo(
    case_id: str,
    case: dict[str, Any],
    config_path: Path,
    output_dir: Path,
    run_id: str,
    replace_existing: bool,
) -> tuple[Path, str]:
    source_kind, source_path = case_source_spec(case)
    if source_kind == "repo_path":
        return resolve_path(source_path, config_path), source_kind
    template_path = resolve_path(source_path, config_path)
    if not template_path.is_dir():
        raise RuntimeError(f"missing template source directory: {template_path}")
    source_repo = output_dir / "_source-repos" / case_id / run_id
    init_template_repo(template_path, source_repo, replace_existing=replace_existing)
    return source_repo.resolve(), source_kind


def case_base_ref(case: dict[str, Any]) -> str | None:
    codebase = case.get("original_codebase") or {}
    return codebase.get("base_ref") or case.get("base_ref")


def ensure_git_repo(repo: Path) -> None:
    if not (repo / ".git").exists():
        raise RuntimeError(f"missing git repository: {repo}")


def git_status(repo: Path) -> str:
    return run(["git", "status", "--short"], repo, check=True).stdout.strip()


def git_head(repo: Path) -> str:
    return run(["git", "rev-parse", "HEAD"], repo, check=True).stdout.strip()


def ensure_clean_repo(repo: Path, allow_dirty: bool) -> None:
    status = git_status(repo)
    if status and not allow_dirty:
        raise RuntimeError(
            "repository is not clean; rerun with --allow-dirty if this is intentional\n"
            f"repo: {repo}\n"
            f"{status}"
        )


def reset_to_base(repo: Path, base_ref: str | None) -> None:
    if not base_ref:
        raise RuntimeError("case has no base_ref to reset to")
    run(["git", "reset", "--hard"], repo, check=True)
    run(["git", "clean", "-fd"], repo, check=True)
    run(["git", "checkout", "--detach", base_ref], repo, check=True)
    run(["git", "reset", "--hard", base_ref], repo, check=True)
    run(["git", "clean", "-fd"], repo, check=True)


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._/-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-") or "case"


def prepared_branch(case_id: str, case: dict[str, Any], run_id: str) -> str:
    target_branch = str(case.get("target_branch") or f"nfp/{case_id}")
    return target_branch


def prepared_worktree_path(repo: Path, case_id: str, run_id: str) -> Path:
    name = slugify(f"codex-{case_id}-{run_id}").replace("/", "-")
    return repo.parent / "worktrees" / name


def branch_exists(repo: Path, branch: str) -> bool:
    return bool(run(["git", "branch", "--list", branch], repo, check=True).stdout.strip())


def prepare_worktree(
    repo: Path,
    case_id: str,
    case: dict[str, Any],
    run_id: str,
    replace_existing: bool = False,
) -> tuple[Path, str]:
    base_ref = case_base_ref(case) or "HEAD"
    branch = prepared_branch(case_id, case, run_id)
    worktree = prepared_worktree_path(repo, case_id, run_id)
    worktree.parent.mkdir(parents=True, exist_ok=True)
    if worktree.exists() and not replace_existing:
        raise RuntimeError(f"target worktree already exists: {worktree}; rerun with --replace-existing-worktree")
    if branch_exists(repo, branch) and not replace_existing:
        raise RuntimeError(f"target branch already exists: {branch}; rerun with --replace-existing-worktree")
    if worktree.exists():
        run(["git", "worktree", "remove", "--force", str(worktree)], repo)
    if worktree.exists():
        shutil.rmtree(worktree)
    run(["git", "worktree", "prune"], repo)
    if branch_exists(repo, branch):
        run(["git", "branch", "-D", branch], repo)
    run(["git", "worktree", "add", "-b", branch, str(worktree), base_ref], repo, check=True)
    return worktree.resolve(), branch


def install_pipeline_context(worktree: Path) -> None:
    shutil.copy2(ROOT / "AGENTS.md", worktree / "AGENTS.md")
    for dirname in (".agents", "skills"):
        dest = worktree / dirname
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(ROOT / dirname, dest)
    (worktree / ".ai").mkdir(exist_ok=True)
    pipeline_docs = worktree / ".ai/pipeline-docs"
    if pipeline_docs.exists():
        shutil.rmtree(pipeline_docs)
    shutil.copytree(ROOT / ".ai/pipeline-docs", pipeline_docs)
    shutil.copy2(ROOT / ".ai/constitution.md", worktree / ".ai/constitution.md")


def selected_prompt_profile(case: dict[str, Any], override: str | None) -> str:
    profile = override or case.get("prompt_profile") or "full-native"
    if profile not in PROMPT_PROFILES:
        raise RuntimeError(f"unknown prompt profile: {profile}")
    return profile


def build_prompt(
    case_id: str,
    case: dict[str, Any],
    source_repo: Path,
    worktree: Path,
    branch: str,
    config_path: Path,
    prompt_profile: str,
) -> str:
    if prompt_profile == "outcome-smoke":
        return build_outcome_smoke_prompt(case_id, case, source_repo, worktree, branch, config_path)
    return build_full_native_prompt(case_id, case, source_repo, worktree, branch, config_path)


def build_full_native_prompt(case_id: str, case: dict[str, Any], source_repo: Path, worktree: Path, branch: str, config_path: Path) -> str:
    phases = case.get("workflow_phases") or NATIVE_PHASES
    phase_list = "\n".join(f"  - {phase}" for phase in phases)
    codebase = case.get("original_codebase") or {}
    base_ref = case_base_ref(case) or "current HEAD"
    expected_result = case.get("expected_result", "Implement the requested feature with artifacts, tests, verification, and a final summary.")
    title = case.get("title", case_id)
    feature_request = case.get("feature_request")
    if not feature_request:
        raise RuntimeError(f"case {case_id} is missing feature_request")

    return f"""You are a nested Codex worker running as a reproducible E2E feature implementation case.

Repository ownership:
- Work only inside this fresh feature worktree: {worktree}
- Original codebase checkout: {source_repo}
- This repository represents the original codebase from case file: {config_path}
- Original codebase base ref: {base_ref}
- Target branch name: {branch}
- Do not modify sibling repositories or harness files.
- The worktree already exists; do not implement in the base checkout.
- Preserve unrelated user changes. If unexpected dirty files are present, stop and report them.

Case:
- Case id: {case_id}
- Title: {title}
- Domain: {case.get('domain', 'unknown')}
- Feature request: {feature_request}
- Expected result: {expected_result}

Native Feature Pipeline:
- If `AGENTS.md`, `.agents/pipeline-core`, `.agents/skills`, `.ai/pipeline-docs`, or `skills` are missing, copy/install them from {ROOT / 'AGENTS.md'}, {ROOT / '.agents'}, {ROOT / '.ai' / 'pipeline-docs'}, and {ROOT / 'skills'} into this worktree before continuing.
- Treat this as a normal user feature request. Discover the repository's native pipeline instructions from `AGENTS.md`, `.agents`, `.ai/pipeline-docs`, and local docs; do not ask the user to invoke individual internal skills by name.
- Progress through these outcomes in order:
{phase_list}
- Use local helper commands where the discovered pipeline docs point you, especially for scaffolding, validation, gate state, evidence, review, finish, and promotion.
- Use `apex.md`, `feature.yaml`, `state.yaml`, and `execution.md` to navigate and record work.
- Do not create `approvals.yaml` or `handoff.md`; approval history belongs in `execution.md`, machine gate state belongs in `state.yaml`.

Implementation expectations:
- Complete artifacts, architecture, technical design, slices, TDD implementation, review, verification, finish, promote, and commit.
- Use focused tests first, then broader validation where feasible.
- Record red/green evidence and any blocked validation with exact commands and reasons.
- Commit the finished implementation on `{branch}`.
- Final response must include branch, commit, changed files, NFP artifact paths, tests run, and known limitations.
"""


def build_outcome_smoke_prompt(case_id: str, case: dict[str, Any], source_repo: Path, worktree: Path, branch: str, config_path: Path) -> str:
    base_ref = case_base_ref(case) or "current HEAD"
    expected_result = case.get("expected_result", "Implement the requested feature with focused evidence and a final summary.")
    title = case.get("title", case_id)
    feature_request = case.get("feature_request")
    if not feature_request:
        raise RuntimeError(f"case {case_id} is missing feature_request")

    return f"""You are a nested Codex worker running a bounded completion smoke case.

Repository ownership:
- Work only inside this fresh feature worktree: {worktree}
- Original codebase checkout: {source_repo}
- This repository represents the original codebase from case file: {config_path}
- Original codebase base ref: {base_ref}
- Target branch name: {branch}
- Do not modify sibling repositories or harness files.
- The worktree already exists; do not implement in the base checkout.
- Preserve unrelated user changes. If unexpected dirty files are present, stop and report them.

Case:
- Case id: {case_id}
- Title: {title}
- Domain: {case.get('domain', 'unknown')}
- Feature request: {feature_request}
- Expected result: {expected_result}

Native pipeline expectations:
- Treat this as a normal user feature request and discover local instructions from `AGENTS.md`, `.agents`, `.ai/pipeline-docs`, `skills`, and repository docs.
- Do not ask the user to manually invoke internal pipeline skills by name.
- This current worktree is already provisioned for the bounded completion smoke case; do not create another worktree and do not perform exhaustive pipeline expansion.
- Keep the pipeline work minimal: produce a debug artifact set under `.ai/feature-workspaces/debug/{case_id}` with `feature.md`, `architecture.md`, `tech-design.md`, and `slices.yaml`.
- Implement the smallest code and test change that satisfies the feature request.
- Run focused validation for that change, or explain blocked validation with the exact command and reason.
- Commit the result on `{branch}`.
- Record concise decisions and evidence in the debug artifacts and final response.
- Final response must include branch, commit, changed files, artifact paths, tests run, and known limitations.
"""


def codex_command(codex_bin: str, repo: Path, final_path: Path, prompt: str, extra_args: list[str]) -> list[str]:
    return [
        codex_bin,
        "exec",
        *extra_args,
        "--dangerously-bypass-approvals-and-sandbox",
        "-C",
        str(repo),
        "-o",
        str(final_path),
        prompt,
    ]


def infer_execution_mode(codex_bin: str, dry_run: bool, requested_mode: str | None) -> str:
    if requested_mode:
        if requested_mode not in EXECUTION_MODES:
            raise RuntimeError(f"unknown execution mode: {requested_mode}")
        if dry_run and requested_mode != "dry-run":
            raise RuntimeError("--dry-run requires --execution-mode dry-run")
        return requested_mode
    if dry_run:
        return "dry-run"
    codex_name = Path(codex_bin).name.lower()
    if "fake" in codex_name or "mock" in codex_name:
        return "mock"
    return "real"


def normalize_timeout(seconds: int | None) -> int | None:
    if seconds is None or seconds <= 0:
        return None
    return seconds


def timeout_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_case(
    case_id: str,
    case: dict[str, Any],
    config_path: Path,
    output_dir: Path,
    codex_bin: str,
    extra_args: list[str],
    run_id: str,
    allow_dirty: bool,
    dry_run: bool,
    execution_mode: str,
    timeout_seconds: int | None,
    reset_base: bool,
    replace_existing_worktree: bool,
    prompt_profile_override: str | None,
) -> dict[str, Any]:
    prompt_profile = selected_prompt_profile(case, prompt_profile_override)
    source_repo, source_repo_kind = case_repo(
        case_id,
        case,
        config_path,
        output_dir,
        run_id,
        replace_existing=replace_existing_worktree,
    )
    ensure_git_repo(source_repo)
    if reset_base:
        reset_to_base(source_repo, case_base_ref(case))
    ensure_clean_repo(source_repo, allow_dirty=allow_dirty)
    worktree, branch = prepare_worktree(
        source_repo,
        case_id,
        case,
        run_id,
        replace_existing=replace_existing_worktree,
    )
    install_pipeline_context(worktree)

    run_dir = output_dir / case_id / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    final_path = run_dir / "codex-final.txt"
    prompt = build_prompt(case_id, case, source_repo, worktree, branch, config_path, prompt_profile)
    command = codex_command(codex_bin, worktree, final_path, prompt, extra_args)
    started_at = datetime.now(timezone.utc).isoformat()

    write_text(run_dir / "prompt.md", prompt)
    write_text(run_dir / "codex-command.json", json.dumps(command, indent=2) + "\n")

    before_head = git_head(worktree)
    before_status = git_status(worktree)
    if dry_run:
        returncode = 0
        stdout = "dry run: codex was not invoked\n"
        timed_out = False
    else:
        try:
            result = subprocess.run(
                command,
                cwd=worktree,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=timeout_seconds,
            )
            returncode = result.returncode
            stdout = result.stdout
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            returncode = 124
            timed_out = True
            stdout = (
                timeout_output(exc.stdout)
                + timeout_output(exc.stderr)
                + f"\nTimed out after {timeout_seconds} seconds while running Codex.\n"
            )
    finished_at = datetime.now(timezone.utc).isoformat()

    after_head = git_head(worktree)
    after_status = git_status(worktree)
    write_text(run_dir / "codex-output.log", stdout)
    final_text = final_path.read_text(encoding="utf-8", errors="replace") if final_path.exists() else ""
    manifest = {
        "case": case_id,
        "title": case.get("title", case_id),
        "repo": str(worktree),
        "source_repo": str(source_repo),
        "source_repo_kind": source_repo_kind,
        "prompt_profile": prompt_profile,
        "path_mode": "actual",
        "feature_request": case.get("feature_request", ""),
        "expected_result": case.get("expected_result", ""),
        "target_branch": branch,
        "base_ref": case_base_ref(case),
        "run_id": run_id,
        "dry_run": dry_run,
        "execution_mode": execution_mode,
        "uses_real_codex": execution_mode == "real",
        "codex_bin": codex_bin,
        "timeout_seconds": timeout_seconds,
        "timed_out": timed_out,
        "returncode": returncode,
        "started_at": started_at,
        "finished_at": finished_at,
        "before_head": before_head,
        "after_head": after_head,
        "before_status": before_status or "clean",
        "after_status": after_status or "clean",
        "prompt": str(run_dir / "prompt.md"),
        "command": str(run_dir / "codex-command.json"),
        "output": str(run_dir / "codex-output.log"),
        "final": str(final_path),
    }
    write_text(run_dir / "run.yaml", yaml.safe_dump(manifest, sort_keys=False))
    write_text(run_dir / "report.md", render_report(manifest, final_text, stdout))
    print(f"case: {case_id}")
    print(f"run_dir: {run_dir}")
    print(f"returncode: {returncode}")
    return manifest


def render_report(manifest: dict[str, Any], final_text: str, stdout: str) -> str:
    lines = [
        f"# Codex E2E Case: {manifest['case']}",
        "",
        f"- Title: {manifest['title']}",
        f"- Repo: `{manifest['repo']}`",
        f"- Target branch: `{manifest['target_branch']}`",
        f"- Base ref: `{manifest.get('base_ref') or 'current HEAD'}`",
        f"- Run id: `{manifest['run_id']}`",
        f"- Execution mode: `{manifest['execution_mode']}`",
        f"- Uses real Codex: `{str(manifest['uses_real_codex']).lower()}`",
        f"- Timeout seconds: `{manifest.get('timeout_seconds') or 'none'}`",
        f"- Timed out: `{str(manifest.get('timed_out')).lower()}`",
        f"- Dry run: `{str(manifest['dry_run']).lower()}`",
        f"- Return code: `{manifest['returncode']}`",
        f"- Before HEAD: `{manifest['before_head']}`",
        f"- After HEAD: `{manifest['after_head']}`",
        f"- Before status: `{manifest['before_status']}`",
        f"- After status: `{manifest['after_status']}`",
        "",
        "## Feature Request",
        "",
        manifest["feature_request"],
        "",
        "## Expected Result",
        "",
        manifest["expected_result"],
        "",
        "## Codex Final",
        "",
        "```text",
        final_text.strip() or "missing",
        "```",
        "",
        "## Codex Output",
        "",
        "```text",
        stdout.strip() or "empty",
        "```",
        "",
    ]
    return "\n".join(line.rstrip() for line in lines) + "\n"


def selected_cases(config: dict[str, Any], case_names: list[str] | None, all_cases: bool) -> list[tuple[str, dict[str, Any]]]:
    cases = config["cases"]
    if all_cases:
        return list(cases.items())
    if not case_names:
        raise RuntimeError("use --case CASE or --all")
    selected = []
    for case_name in case_names:
        if case_name not in cases:
            raise RuntimeError(f"unknown case: {case_name}")
        selected.append((case_name, cases[case_name]))
    return selected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="YAML case file")
    parser.add_argument("--case", action="append", help="Case id to run; repeat for multiple cases")
    parser.add_argument("--all", action="store_true", help="Run all cases in config order")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for run artifacts")
    parser.add_argument("--run-id", default=None, help="Stable run id. Defaults to UTC timestamp")
    parser.add_argument("--codex-bin", default=os.environ.get("CODEX_BIN", "codex"), help="Codex executable")
    parser.add_argument("--codex-arg", action="append", default=[], help="Extra argument passed to codex exec before sandbox flags")
    parser.add_argument("--execution-mode", choices=sorted(EXECUTION_MODES), default=None, help="Label this run as mock, dry-run, or real")
    parser.add_argument("--timeout-seconds", type=int, default=1800, help="Codex invocation timeout; use 0 to disable")
    parser.add_argument("--allow-dirty", action="store_true", help="Allow running when target repo has a dirty working tree")
    parser.add_argument("--dry-run", action="store_true", help="Write prompt/command/report without invoking codex")
    parser.add_argument("--reset-to-base", action="store_true", help="Reset target repo to case base_ref before running")
    parser.add_argument(
        "--replace-existing-worktree",
        action="store_true",
        help="Allow removing an existing target worktree or branch before preparing the run",
    )
    parser.add_argument("--prompt-profile", choices=sorted(PROMPT_PROFILES), default=None, help="Override case prompt profile")
    args = parser.parse_args(argv)

    config_path = Path(args.config).expanduser().resolve()
    config = load_config(config_path)
    output_dir = Path(args.output_dir).expanduser()
    if not output_dir.is_absolute():
        output_dir = (ROOT / output_dir).resolve()
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    execution_mode = infer_execution_mode(args.codex_bin, dry_run=args.dry_run, requested_mode=args.execution_mode)
    timeout_seconds = normalize_timeout(args.timeout_seconds)

    try:
        manifests = [
            run_case(
                case_id=case_id,
                case=case,
                config_path=config_path,
                output_dir=output_dir,
                codex_bin=args.codex_bin,
                extra_args=args.codex_arg,
                run_id=run_id,
                allow_dirty=args.allow_dirty,
                dry_run=args.dry_run,
                execution_mode=execution_mode,
                timeout_seconds=timeout_seconds,
                reset_base=args.reset_to_base,
                replace_existing_worktree=args.replace_existing_worktree,
                prompt_profile_override=args.prompt_profile,
            )
            for case_id, case in selected_cases(config, args.case, args.all)
        ]
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    summary_path = output_dir / f"summary-{run_id}.yaml"
    write_text(
        summary_path,
        yaml.safe_dump(
            {
                "run_id": run_id,
                "execution_modes": sorted({manifest["execution_mode"] for manifest in manifests}),
                "uses_real_codex": any(manifest["uses_real_codex"] for manifest in manifests),
                "runs": manifests,
            },
            sort_keys=False,
        ),
    )
    shell_commands = [
        " ".join(shlex.quote(part) for part in json.loads(Path(manifest["command"]).read_text(encoding="utf-8")))
        for manifest in manifests
    ]
    write_text(output_dir / f"commands-{run_id}.sh", "\n".join(shell_commands) + "\n")
    print(f"summary: {summary_path}")
    return 0 if all(manifest["returncode"] == 0 for manifest in manifests) else 1


if __name__ == "__main__":
    raise SystemExit(main())
