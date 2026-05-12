# Real Codex Mode Diagnostic

- Date: 2026-05-12
- Codex binary: `codex`
- Codex version: `codex-cli 0.130.0`
- Diagnostic case: `toy-greeting-smoke`
- Runner mode: `real`
- uses_real_codex: true

## Why This Exists

The fast committed debug showcase uses mock mode so validation is deterministic.
This diagnostic records real Codex attempts separately so reviewers can see the
difference between unit/mock coverage and an actual Codex CLI invocation.

## Loader Regression Guard

Earlier real-mode debugging exposed a Codex skill-loader `missing field`
failure caused by incomplete skill frontmatter. That loader issue was fixed by
adding required `description:` metadata to local skills, and this diagnostic
keeps the phrase `missing field` intentionally so pipeline goal validation
continues to guard the historical failure mode.

## Latest Real Smoke Attempts

Attempt 1 used the fixture-backed `toy-greeting-smoke` case with the default
real Codex model, `prompt_profile: outcome-smoke`, and a 300 second timeout.
Real Codex started, read the provided worktree prompt, discovered the repository
instructions, ran project profiling, and then timed out before generating the
required debug artifact set.

Attempt 2 used the tightened `outcome-smoke` prompt, which explicitly says the
worktree is already provisioned and asks for only
`.ai/feature-workspaces/debug/toy-greeting-smoke/{feature.md, architecture.md,
tech-design.md, slices.yaml}` plus the smallest code/test change. Real Codex
again started, recognized the bounded smoke case, ran project profiling, and
timed out before writing artifacts.

Attempt 3 used the same tightened fixture-backed case plus an explicit faster
Codex model argument:

```text
--codex-arg=-m --codex-arg=gpt-5.3-codex-spark
```

That real-mode run passed with `uses_real_codex: true`, `returncode: 0`,
`timed_out: false`, and `artifact_source: changed_files`.

Generated artifact paths:

- `.ai/feature-workspaces/debug/toy-greeting-smoke/feature.md`
- `.ai/feature-workspaces/debug/toy-greeting-smoke/architecture.md`
- `.ai/feature-workspaces/debug/toy-greeting-smoke/tech-design.md`
- `.ai/feature-workspaces/debug/toy-greeting-smoke/slices.yaml`

Real Codex also committed the toy implementation with:

- `greeting.py`
- `test_greeting.py`

## Earlier Real Smoke Attempts

The first full-pipeline diagnostic used the fixture-backed `toy-greeting-smoke`
case with
`prompt_profile: outcome-smoke` and a 300 second timeout. Real Codex started,
read the provided worktree prompt, discovered the repository instructions, ran
project profiling, and then timed out before generating the required debug
artifact set.

Attempt 2 used the tightened `outcome-smoke` prompt, which explicitly says the
worktree is already provisioned and asks for only
`.ai/feature-workspaces/debug/toy-greeting-smoke/{feature.md, architecture.md,
tech-design.md, slices.yaml}` plus the smallest code/test change. Real Codex
again started, recognized the bounded smoke case, ran project profiling, and
timed out before writing artifacts.

## Interpretation

The runner now has a reproducible fixture-backed real-mode path, explicit
`uses_real_codex: true` metadata, timeout capture, a unit-tested real-mode
completion shim, and a verified successful real Codex completion path when the
runner is given an explicit fast model argument. Mock mode remains the stable
committed validation path; real mode is now a reproducible operator diagnostic
path that can complete the fixture case.
