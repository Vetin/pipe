# Codex E2E Case: harness-codex-debug-smoke

- Title: Harness Codex Debug Smoke
- Repo: `$WORK_ROOT/worktrees/codex-harness-codex-debug-smoke-20260512-debug`
- Target branch: `nfp/harness-codex-debug-smoke`
- Base ref: `HEAD`
- Run id: `20260512-debug`
- Execution mode: `mock`
- Uses real Codex: `false`
- Timeout seconds: `1800`
- Timed out: `false`
- Dry run: `false`
- Return code: `0`
- Before HEAD: `4d96b52ee0c31a52f07fead679e798389b4d1ff1`
- After HEAD: `7ca19ea697daf848b1f09330dbaaa721df104df1`
- Before status: `clean`
- After status: `clean`

## Feature Request

Add a stable Codex debug smoke feature that proves the native feature pipeline can be discovered, artifacts can be generated, and implementation output can be validated from a normal feature request.

## Expected Result

The run must produce feature, architecture, technical design, slices, comparison, validation, and final output artifacts while explicitly reporting whether Codex execution was mock, dry-run, or real.

## Codex Final

```text
branch: nfp/harness-codex-debug-smoke
commit: 7ca19ea697daf848b1f09330dbaaa721df104df1
changed files: .ai/feature-workspaces/debug/harness-codex-debug-smoke, README.codex-debug.md
```

## Codex Output

```text
{"repo": "$WORK_ROOT/worktrees/codex-harness-codex-debug-smoke-20260512-debug", "branch": "nfp/harness-codex-debug-smoke", "commit": "7ca19ea697daf848b1f09330dbaaa721df104df1", "has_native_pipeline": true, "no_direct_skill_invocations": true, "fresh_worktree": true, "generated_artifacts": ["architecture.md", "feature-card.md", "feature.md", "slices.yaml", "tech-design.md"]}
```

