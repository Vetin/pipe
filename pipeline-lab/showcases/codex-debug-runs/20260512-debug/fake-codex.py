#!/usr/bin/env python3
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

case_match = re.search(r"Case id:\s*([^\n]+)", prompt)
branch_match = re.search(r"Target branch name:\s*([^\n]+)", prompt)
case_id = (case_match.group(1).strip() if case_match else "mock-feature").replace("/", "-")
branch = branch_match.group(1).strip() if branch_match else "mock-branch"
workspace = repo / ".ai" / "feature-workspaces" / "debug" / case_id
workspace.mkdir(parents=True, exist_ok=True)

artifacts = {
    "feature.md": f"# Feature: {case_id}\n\n## Intent\n\nImplement the requested debug feature through the native pipeline.\n",
    "architecture.md": f"# Architecture: {case_id}\n\n## Feature Topology\n\n```mermaid\ngraph TD\n  User[User feature request] --> Codex[Codex worker]\n  Codex --> Pipeline[Native Feature Pipeline]\n  Pipeline --> Artifacts[Generated artifacts]\n```\n",
    "tech-design.md": f"# Technical Design: {case_id}\n\n## Implementation Summary\n\nThe mock worker proves prompt, context, artifact, and commit handling.\n",
    "slices.yaml": "slices:\n  - id: S-001\n    title: Mock debug implementation\n    status: complete\n",
    "feature-card.md": f"# Feature Card: {case_id}\n\n- Status: complete\n- Evidence: fake Codex debug run\n",
}
for name, content in artifacts.items():
    (workspace / name).write_text(content, encoding="utf-8")

(repo / "README.codex-debug.md").write_text(
    f"# Codex Debug Implementation\n\nCase `{case_id}` was implemented by the mock Codex debug worker.\n",
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
    f"branch: {branch}\ncommit: {commit}\nchanged files: .ai/feature-workspaces/debug/{case_id}, README.codex-debug.md\n",
    encoding="utf-8",
)
print(json.dumps({
    "repo": str(repo),
    "branch": branch,
    "commit": commit,
    "has_native_pipeline": "normal user feature request" in prompt and "Progress through these outcomes" in prompt,
    "no_direct_skill_invocations": "nfp-00-intake" not in prompt and "nfp-12-promote" not in prompt,
    "fresh_worktree": "fresh feature worktree" in prompt and "do not implement in the base checkout" in prompt,
    "generated_artifacts": sorted(artifacts),
}))
