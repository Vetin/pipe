# Feature: Codex E2E Runner Hardening

## Intent

Make the reproducible Codex showcase runner production-grade enough to prove
native feature-building behavior without relying only on mocks. The runner must
support safe reruns, portable committed artifacts, fixture-backed source repos,
and a bounded real Codex completion smoke case.

## Motivation

The showcase runner is now part of the evidence layer for judging whether this
repo's own Native Feature Pipeline works in real feature-building workflows. If
it silently deletes worktrees, commits local-only paths, or only proves fake
Codex execution, later pipeline improvements can look validated while missing
important operational failure modes.

## Actors

- Pipeline maintainer running local debug cases.
- Codex agent implementing features inside generated worktrees.
- Reviewer comparing committed showcase outputs against the plan and vision.
- Future CI job or scheduled validation runner.

## Problem

The current debug pipeline can demonstrate prompt construction and artifact
validation with a fake Codex binary, but it has four gaps:

- existing worktrees and branches are forcefully removed without an explicit
  replacement flag
- committed debug artifacts preserve machine-local absolute paths
- stable cases require an existing git checkout instead of a tracked fixture
  that can be materialized into a fresh source repo
- real Codex mode has diagnostic coverage but no small completion-oriented
  smoke path that can finish end to end

## Goals

- Make destructive reruns explicit.
- Make committed debug artifacts portable across machines.
- Make at least one stable case self-contained through a tracked fixture.
- Make real-mode completion validation possible without running the full ten
  external showcase repos.
- Keep nested prompts aligned with the native prompt rule in `AGENTS.md`.

## Non-Goals

- No change to the Native Feature Pipeline gate model.
- No replacement of the existing ten large codebase showcase definitions.
- No requirement that the bounded real smoke case implements all ten external
  showcase features.

## Related Existing Features

- `pipeline/real-codex-showcase-debug-runner`
- `pipeline/random-feature-stress-lab`
- `project-init`

## Functional Requirements

- FR-001: `run_codex_e2e_case.py` must refuse to replace an existing target
  worktree or branch unless an explicit replacement option is passed.
- FR-002: The debug runner must expose a portable-output mode that rewrites
  committed reports away from machine-local absolute paths after validation.
- FR-003: Case files must support tracked template repositories that are
  materialized into temporary git repos for stable E2E tests.
- FR-004: The E2E runner must support at least two prompt profiles: the existing
  full native pipeline profile and a bounded outcome smoke profile for real
  Codex completion checks.
- FR-005: Debug validation must accept both prompt profiles while continuing to
  reject direct internal `nfp-*` skill invocation prompts.
- FR-006: Tests must cover replacement refusal, explicit replacement, template
  repo materialization, prompt profile selection, portable-output rewriting, and
  a real-mode executable path that can complete artifacts.
- FR-007: Showcase outputs must be regenerated and pass the deterministic
  pipeline goal validator.

## Non-Functional Requirements

- NFR-001: Existing mock and dry-run behavior must remain fast enough for local
  unit tests.
- NFR-002: Error messages must make rerun, source materialization, and prompt
  profile failures actionable.
- NFR-003: Portable normalization must not run before validation consumes real
  filesystem paths.
- NFR-004: No new production dependency is introduced.

## Acceptance Criteria

- AC-001: Running the focused test files passes:
  - `python -m pytest tests/feature_pipeline/test_codex_e2e_runner.py`
  - `python -m pytest tests/feature_pipeline/test_codex_debug_runner.py`
  - `python -m pytest tests/feature_pipeline/test_pipeline_goal_validation.py`
- AC-002: A committed debug showcase can be regenerated with portable paths and still
  validates with `validate_pipeline_goals.py`.
- AC-003: A fixture-backed smoke case can be run without any pre-cloned external repo.
- AC-004: A repeated run against the same branch/worktree fails fast unless replacement
  is explicitly requested.

## Product Risks

- Portable normalization could hide a path that future validation needs. The
  design mitigates this by rewriting only after validation and by keeping tests
  focused on the committed artifact contract.
- A short real smoke prompt could be mistaken for full showcase validation. The
  run metadata records prompt profile and mode explicitly.

## Assumptions

- The local `codex` binary may be unavailable or slow in CI, so unit tests use a
  non-fake executable shim for the real-mode code path and the manually captured
  real diagnostic records the actual local attempt.
- The portable-output rewrite is applied only after deterministic validation has
  consumed real filesystem paths.

## Open Questions

- Should the real-smoke case later become a CI job when a Codex execution
  environment is available?
