# Feature: Real Codex Showcase Debug Runner

## Intent

Make the showcase E2E path explicit about what is mocked and what can run a real
Codex CLI session, then provide a reusable debug runner that starts from a
normal feature request in a target repository and validates the resulting
pipeline artifacts.

## Motivation

Current unit tests verify `run_codex_e2e_case.py` with a fake Codex executable.
That is useful for deterministic command/prompt regression, but it does not
prove a real Codex agent can live in a worktree, discover `AGENTS.md`, and drive
the Native Feature Pipeline from user intent.

## Actors

- Pipeline maintainer debugging showcase quality.
- Local Codex CLI acting as the implementation agent.
- Reproducible test suite using a fake Codex executable for fast regression.

## Goals

- FR-001: Clearly report whether a showcase debug run used fake, dry-run, or
  real Codex execution.
- FR-002: Add a real-Codex-capable debug runner that accepts a case file,
  target repository path, feature request, and timeout.
- FR-003: Validate run artifacts after execution: prompt style, policy context,
  worktree isolation, command/final/output logs, status, and pipeline artifacts
  when implementation completed.
- FR-004: Compare the new runner with current tests and preserve the best
  parts: fast mock tests plus optional real CLI debug runs.
- FR-005: Regenerate a stable debug run and report weaknesses with a concrete
  improvement plan.

## Non-Goals

- Do not require CI to invoke the real Codex CLI.
- Do not remove the existing fake-Codex regression test.
- Do not mutate cloned OSS showcase repositories during unit tests.

## Functional Requirements

- FR-001: `run_codex_e2e_case.py` supports bounded execution timeout metadata.
- FR-002: `run_codex_debug_pipeline.py` supports `mock`, `dry-run`, and `real`
  modes.
- FR-003: Debug reports identify current test mode, recommended mode, and why.
- FR-004: Validator checks prompt, command, worktree, final response, and
  generated artifact paths.
- FR-005: Tests prove mock mode is deterministic and real mode is represented
  without requiring a real Codex call.

## Non-Functional Requirements

- NFR-001: Fast tests remain deterministic and offline.
- NFR-002: Real mode fails early when `codex` is missing unless another mode is
  selected.
- NFR-003: Timeout failures are recorded as verification debt, not success.

## Acceptance Criteria

- AC-001: Given the existing fake-Codex test, when it runs, then the report
  explicitly identifies `execution_mode: mock`.
- AC-002: Given a debug config and fake Codex, when the new debug runner runs,
  then it produces summary, comparison, validation, and replay command artifacts.
- AC-003: Given `--mode real`, when no real Codex binary is available, then the
  runner fails before preparing a target worktree.
- AC-004: Given the final stable debug run, when validation runs, then no
  prompt directly scripts `nfp-00` through `nfp-12`, and the report recommends
  keeping mock tests plus real debug runs.

## Assumptions

- `codex exec` remains the local CLI entrypoint for real agent execution.
- The deterministic unit test can use a fake executable to avoid consuming real
  model time.

## Open Questions

- None blocking. Live OSS repo execution can be run manually with `--mode real`
  after this feature lands.
