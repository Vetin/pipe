import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
FEATURECTL = ROOT / ".agents/pipeline-core/scripts/featurectl.py"
BENCH = ROOT / ".agents/pipeline-core/scripts/pipelinebench.py"
PYTHON = sys.executable


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def ignore_generated_pipeline_lab(_src, names):
    ignored = {
        "runs",
        "repos",
        "real-runs",
        "implementation-runs",
        "materialized-runs",
        "nfp-real-runs",
        "codex-e2e-runs",
        "codex-debug-runs",
    }
    return [name for name in names if name in ignored]


def make_repo(tempdir):
    repo = Path(tempdir) / "repo"
    repo.mkdir()
    run(["git", "init", "-b", "main"], repo)
    run(["git", "config", "user.email", "test@example.com"], repo)
    run(["git", "config", "user.name", "Test User"], repo)
    (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    run(["git", "add", "README.md"], repo)
    run(["git", "commit", "-m", "initial"], repo)
    return repo


def create_workspace(tempdir, repo, run_id="run-plan-contract", domain="auth", title="Reset Password"):
    run(
        [
            PYTHON,
            str(FEATURECTL),
            "new",
            "--domain",
            domain,
            "--title",
            title,
            "--run-id",
            run_id,
        ],
        repo,
    )
    slug = slugify(title)
    return Path(tempdir) / f"worktrees/{domain}-{slug}-{run_id}/.ai/feature-workspaces/{domain}/{slug}--{run_id}"


def slugify(value):
    import re

    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-{2,}", "-", value).strip("-")


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def write_planning_artifacts(workspace):
    try:
        from test_planning_readiness import write_planning_artifacts as write
    except ModuleNotFoundError:
        from tests.feature_pipeline.test_planning_readiness import write_planning_artifacts as write

    write(workspace)


def approve_planning(workspace, current_step="readiness"):
    state_path = Path(workspace) / "state.yaml"
    state = load_yaml(state_path)
    state["current_step"] = current_step
    state["gates"]["feature_contract"] = "approved"
    state["gates"]["architecture"] = "approved"
    state["gates"]["tech_design"] = "approved"
    state["gates"]["slicing_readiness"] = "delegated"
    state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
    execution_path = Path(workspace) / "execution.md"
    if execution_path.exists():
        execution = execution_path.read_text(encoding="utf-8")
        execution = execution.replace("Current step: context", f"Current step: {current_step}")
        execution = execution.replace("Next recommended skill: nfp-01-context", "Next recommended skill: nfp-06-readiness")
        execution_path.write_text(execution, encoding="utf-8")
    return state


def record_full_evidence(repo, workspace, red_ts="2026-05-11T09:00:00Z", green_ts="2026-05-11T10:00:00Z"):
    commands = [
        ("red", "python -m unittest tests.test_password_reset", "expected failure", red_ts),
        ("green", "python -m unittest tests.test_password_reset", "ok", green_ts),
        ("verification", "python -m unittest discover -s tests", "ok", "2026-05-11T11:00:00Z"),
        ("review", "", "No critical findings.", "2026-05-11T12:00:00Z"),
    ]
    for phase, command, output, timestamp in commands:
        cmd = [
            PYTHON,
            str(FEATURECTL),
            "record-evidence",
            "--workspace",
            str(workspace),
            "--slice",
            "S-001",
            "--phase",
            phase,
            "--output",
            output,
            "--timestamp",
            timestamp,
        ]
        if command:
            cmd.extend(["--command", command])
        if phase in {"red", "green"}:
            cmd.extend(["--git-state", "## feature branch\n"])
        run(cmd, repo)
