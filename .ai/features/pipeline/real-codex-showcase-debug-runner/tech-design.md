# Technical Design: Real Codex Showcase Debug Runner

## Change Delta

- Add `run_codex_debug_pipeline.py`.
- Extend `run_codex_e2e_case.py` with `execution_mode` and timeout metadata.
- Add unit tests for mock mode, real-mode preflight, and current-test
  comparison.
- Generate a stable debug run in mock mode for committed comparison artifacts.

## Implementation Summary

The new debug runner is a thin orchestration layer around the existing E2E
runner. It creates a fake executable for deterministic mock mode, requires
`codex` for real mode, delegates case execution to the existing runner, then
validates and reports the output.

## Modules And Responsibilities

- `run_codex_e2e_case.py`: worktree setup, prompt construction, Codex command
  execution, timeout capture, and run manifest.
- `run_codex_debug_pipeline.py`: mode handling, fake executable creation,
  delegation, validation, comparison report, and stable summary.
- `tests/feature_pipeline/test_codex_debug_runner.py`: deterministic coverage
  for the new runner and current-test comparison.

## Dependency And Ownership Plan

No new dependencies. The runner uses Python standard library plus PyYAML, which
is already required by pipeline scripts.

## Contracts

Debug summary fields: `execution_mode`, `uses_real_codex`, `run_id`,
`case_count`, `validation_status`, `comparison.recommendation`, and `runs[]`.

Validation fields: `checks[]`, `failures[]`, and `status`.

## API/Event/Schema Details

CLI:

- `--mode {mock,dry-run,real}`
- `--config`
- `--case`
- `--all`
- `--run-id`
- `--output-dir`
- `--codex-bin`
- `--timeout-seconds`
- `--reset-to-base`

## Core Code Sketches

1. Resolve selected cases.
2. If `mode=mock`, write a fake Codex executable under the run directory.
3. If `mode=real`, require `shutil.which(codex_bin)`.
4. Invoke existing `run_codex_e2e_case.py` with mode and timeout.
5. Read generated manifests, prompt, command, output, and final text.
6. Validate prompt style, worktree context, command mode, and artifacts.
7. Write comparison and summary.

## Data Model

No persisted application data. Debug artifacts are YAML, Markdown, text logs,
and replay shell commands.

## Error Handling

Missing real Codex, dirty target repos, E2E runner failure, timeout, and
validation failures return non-zero. Mock mode stays deterministic and offline.

## Security Considerations

Real mode is explicit because it executes a local Codex agent with write
permissions in a prepared worktree. Commands and outputs are recorded for audit.

## Test Strategy

- Unit tests run mock mode against a temp git repo.
- Unit tests assert real mode fails early when the binary is missing.
- Unit tests assert the existing test suite uses a fake executable and the new
  comparison recommends mock tests plus real debug runs.

## Migration Plan

No migration.

## Rollback Plan

Remove the new runner/test, revert the E2E runner metadata changes, and delete
`codex-debug-runs`.

## Integration Notes

The debug runner should become the preferred live reproduction path. Existing
unit tests remain fast regressions, not proof of real agent behavior.

## Decision Traceability

- FR-001/FR-002: execution mode and real/fake handling.
- FR-003: validation artifacts.
- FR-004: comparison report.
- FR-005: stable debug run output.
