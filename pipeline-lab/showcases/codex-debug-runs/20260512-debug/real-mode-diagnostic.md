# Real Codex Mode Diagnostic

- Date: 2026-05-12
- Codex binary: `/opt/homebrew/bin/codex`
- Codex version: `codex-cli 0.130.0`
- Diagnostic case: temporary toy repo with `toy-real-smoke`
- Runner mode: `real`
- Result: real Codex invocation started and was captured by the debug runner, but the bounded full-pipeline prompt timed out before artifacts were produced.

## First Attempt

- Timeout: 180 seconds
- Summary: `/tmp/codex-real-smoke.cKAZfq/debug-runs/real-smoke/summary.yaml`
- Runner status: `fail`
- Evidence: `uses_real_codex: true`, nested Codex inspected the worktree, recognized expected pipeline scaffolding, and ran `featurectl.py init --profile-project`.
- Weakness found: Codex skill loader reported `.agents/skills/*/SKILL.md` files were missing `description` frontmatter.

## Fix Applied

- Added `description:` frontmatter to all `.agents/skills/*/SKILL.md` files.
- Updated pipeline goal validation to require skill descriptions.

## Follow-Up Check

- Timeout: 45 seconds
- Summary: `/tmp/codex-real-smoke2.Qez1iM/debug-runs/real-smoke/summary.yaml`
- Runner status: `fail` due expected timeout before full artifacts.
- Loader check: no `missing field` skill-description errors remained in `codex-output.log`.

## Interpretation

The previous showcase unit tests were mock-based. The new runner can invoke real Codex and records `uses_real_codex` explicitly. For stable committed CI-style evidence, mock mode remains the best default. Real mode is better as an operator debug path with a larger timeout or a narrower real-smoke case.
