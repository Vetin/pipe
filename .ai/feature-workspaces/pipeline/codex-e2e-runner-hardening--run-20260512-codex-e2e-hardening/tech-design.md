# Technical Design: Codex E2E Runner Hardening

## Runner Contracts

### Source Repository Resolution

`case_repo(case, config_path, output_dir, run_id)` returns a git repository.

- If `original_codebase.repo_path` is present, resolve it as today.
- If `original_codebase.template_path` is present, copy the template into
  `<output_dir>/_source-repos/<case-id>/<run-id>`, initialize git, configure a
  local test identity, add files, and create an initial commit.
- `repo_path` and `template_path` are mutually exclusive for a case.

### Worktree Safety

`prepare_worktree(..., replace_existing=False)` refuses to remove either:

- an existing prepared worktree path
- an existing target branch

The caller must pass `--replace-existing-worktree` to opt into the previous
destructive rerun behavior. `run_codex_debug_pipeline.py --clean` forwards this
flag because the user explicitly requested a clean rerun artifact.

### Prompt Profiles

The default `full-native` profile preserves the existing full pipeline outcomes.
The new `outcome-smoke` profile is shorter and describes the requested result
in plain language while still pointing Codex to `AGENTS.md`, `.agents`,
`.ai/pipeline-docs`, and local docs.

### Portable Output

`run_codex_debug_pipeline.py --portable-output` runs validation against actual
paths, writes summaries, then normalizes markdown, yaml, json, log, txt, and sh
files under the debug run directory. Replacements use stable tokens:

- repository root -> `$ROOT`
- run directory -> `$RUN_DIR`
- parent work root -> `$WORK_ROOT`

Validation must not depend on portable paths after this phase.

## Test Strategy

- E2E runner unit tests:
  - fixture template materialization
  - prompt profile choice
  - default rejection of existing branch/worktree
  - explicit replacement success
- Debug runner unit tests:
  - existing mock validation still passes
  - real mode executable shim can complete smoke artifacts
  - portable output removes local paths from committed artifacts
- Goal validator tests:
  - committed debug run fails when local absolute paths leak
  - real diagnostic remains required

## Error Handling

- Invalid case source definitions raise a clear `RuntimeError`.
- Existing branch/worktree without replacement raises a clear `RuntimeError`.
- Unsupported prompt profiles raise a clear `RuntimeError`.
- Portable normalization is best-effort over text artifact extensions and does
  not mutate non-text files.

## Verification Commands

- `python -m pytest tests/feature_pipeline/test_codex_e2e_runner.py`
- `python -m pytest tests/feature_pipeline/test_codex_debug_runner.py`
- `python -m pytest tests/feature_pipeline/test_pipeline_goal_validation.py`
- `python pipeline-lab/showcases/scripts/run_codex_debug_pipeline.py --config pipeline-lab/showcases/codex-e2e-cases.yaml --case harness-codex-debug-smoke --run-id 20260512-debug --output-dir pipeline-lab/showcases/codex-debug-runs --mode mock --clean --portable-output`
- `python pipeline-lab/showcases/scripts/validate_pipeline_goals.py --passes 3`

