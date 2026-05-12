# Technical Design: Codex E2E Runner Hardening

## Change Delta

Add safe rerun contracts, fixture source materialization, prompt profiles,
portable debug output, and validator/test coverage for those behaviors.

## Implementation Summary

`run_codex_e2e_case.py` becomes responsible for deterministic source repo
materialization and non-destructive worktree preparation. `run_codex_debug_pipeline.py`
becomes responsible for validating real paths and optionally converting output
artifacts into portable committed reports.

## Modules And Responsibilities

- `run_codex_e2e_case.py`: resolve case source repos, prepare guarded worktrees,
  install pipeline context, build prompt profiles, invoke Codex, and write
  runtime manifests.
- `run_codex_debug_pipeline.py`: choose mock/dry-run/real mode, run E2E cases,
  validate generated artifacts, compare current tests, write reports, and
  optionally normalize paths.
- `validate_pipeline_goals.py`: reject debug outputs that fail status, artifact,
  real diagnostic, or portability checks.
- `tests/feature_pipeline/test_codex_e2e_runner.py`: verify E2E runner contracts.
- `tests/feature_pipeline/test_codex_debug_runner.py`: verify debug wrapper
  contracts.
- `tests/feature_pipeline/test_pipeline_goal_validation.py`: verify goal
  validator checks.

## Dependency And Ownership Plan

No new third-party dependencies. Ownership remains in `pipeline-lab/showcases`
and `tests/feature_pipeline`. Fixture source files live under
`pipeline-lab/showcases/fixtures`.

## Contracts

### Source Repository Resolution

`case_repo(case, config_path, output_dir, run_id, case_id)` returns a clean git
repository.

- `original_codebase.repo_path`: resolve as today.
- `original_codebase.template_path`: copy into
  `<output_dir>/_source-repos/<case-id>/<run-id>`, run `git init`, configure a
  local identity, add files, and commit.
- Defining both source types is invalid.
- Defining neither source type is invalid.

### Worktree Safety

`prepare_worktree(..., replace_existing=False)` refuses to remove an existing
worktree path or branch. The caller must pass `--replace-existing-worktree` to
opt into removal. Debug `--clean` forwards that flag because it explicitly
requests a clean rerun.

### Prompt Profiles

- `full-native`: the current full pipeline outcome prompt.
- `outcome-smoke`: a shorter native prompt that describes the feature outcome,
  points at repository instructions, and asks for a bounded completion.

### Portable Output

`--portable-output` normalizes text artifacts under the debug run directory
after validation. It replaces local prefixes with `$ROOT`, `$RUN_DIR`, and
`$WORK_ROOT`, then records `path_mode: portable`.

## API/Event/Schema Details

- E2E CLI adds:
  - `--replace-existing-worktree`
  - `--prompt-profile {full-native,outcome-smoke}`
- Debug CLI adds:
  - `--replace-existing-worktree`
  - `--prompt-profile {full-native,outcome-smoke}`
  - `--portable-output`
- Case YAML adds optional `original_codebase.template_path` and optional
  `prompt_profile`.

## Core Code Sketches

```python
if repo_path and template_path:
    raise RuntimeError("case source must define only one of repo_path or template_path")

if worktree.exists() and not replace_existing:
    raise RuntimeError("worktree already exists; rerun with --replace-existing-worktree")

if prompt_profile == "outcome-smoke":
    prompt = build_outcome_smoke_prompt(...)
```

## Data Model

Per-case manifests add:

- `source_repo_kind`: `repo_path` or `template_path`
- `prompt_profile`: selected profile
- `path_mode`: `actual` in E2E runtime manifests and `portable` in normalized
  debug output

## Error Handling

- Invalid case source definitions raise a clear `RuntimeError`.
- Existing branch/worktree without replacement raises a clear `RuntimeError`.
- Unsupported prompt profiles raise a clear `RuntimeError`.
- Portable normalization skips non-text files and records path mode.

## Security Considerations

- The Codex bypass flag remains explicit and visible.
- Template materialization copies tracked fixture files only.
- No secrets, tokens, external services, or network calls are added.
- Non-destructive defaults reduce accidental data loss.

## Test Strategy

- E2E runner unit tests cover fixture materialization, prompt profile choice,
  default replacement refusal, and explicit replacement.
- Debug runner unit tests cover portable output, real-mode executable shim
  completion, and existing mock validation.
- Goal validator tests cover committed artifact portability.

## Migration Plan

Existing `repo_path` cases and default CLI behavior keep using `full-native`.
Any scripts that rely on implicit replacement must add
`--replace-existing-worktree` or run debug mode with `--clean`.

## Rollback Plan

Revert the implementation commit. Existing generated artifacts remain readable,
and old case files remain compatible.

## Integration Notes

The only external integration is local `codex exec`. Debug mode can use mock,
dry-run, or real mode. Unit tests do not require the real Codex binary.

## Decision Traceability

- FR-001 -> guarded `prepare_worktree` and E2E tests.
- FR-002 -> `--portable-output` and validator/tests.
- FR-003 -> `template_path` materialization and fixture case/tests.
- FR-004 -> prompt profiles and prompt tests.
- FR-005 -> debug validation prompt acceptance and forbidden-token checks.
- FR-006 -> focused test files.
- FR-007 -> regenerated showcase output and pipeline goal validation.

