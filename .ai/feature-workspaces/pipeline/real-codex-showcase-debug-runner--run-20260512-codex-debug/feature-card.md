# Feature Card: pipeline/real-codex-showcase-debug-runner

## Intent

Make showcase E2E execution explicit about whether it uses mock, dry-run, or real Codex, and add a reproducible debug runner that validates generated native-pipeline artifacts.

## Requirements

- Report `execution_mode`, `uses_real_codex`, timeout, and timeout result in each E2E run manifest.
- Provide a wrapper that can run the existing E2E case runner in `mock`, `dry-run`, or `real` mode.
- Validate prompt style, installed pipeline context, command shape, generated artifacts, and comparison against the current fake-Codex unit path.
- Commit a stable generated showcase run and document real-mode diagnostic behavior.

## Architecture

`run_codex_debug_pipeline.py` wraps `run_codex_e2e_case.py`. The E2E runner prepares a fresh worktree and installs `AGENTS.md`, `.agents`, `.ai/pipeline-docs`, and `skills`. The debug runner selects mock/dry-run/real mode, executes E2E, then validates prompt, command, mode metadata, context files, and artifacts changed between `before_head` and `after_head`.

## Contracts

- `run.yaml`: adds `execution_mode`, `uses_real_codex`, `codex_bin`, `timeout_seconds`, and `timed_out`.
- `summary.yaml`: records mode, real-Codex flag, comparison, validation status, and per-case artifact evidence.
- `comparison.md`: states the current unit path uses fake Codex and recommends when to use the new debug runner.
- `real-mode-diagnostic.md`: records bounded real Codex attempts and residual runtime limits.

## Slices

- `S-001`: E2E mode and timeout metadata.
- `S-002`: debug wrapper and focused tests.
- `S-003`: stable generated showcase, real-mode diagnostic, skill metadata fix, and goal validation.

## Tests And Evidence

- `python -m unittest tests.feature_pipeline.test_codex_e2e_runner tests.feature_pipeline.test_codex_debug_runner tests.feature_pipeline.test_pipeline_goal_validation`
- `python -m unittest discover tests/feature_pipeline`
- `python pipeline-lab/showcases/scripts/validate_pipeline_goals.py --passes 3 --report /tmp/pipeline-goal-validation-codex-debug.md`
- `python pipeline-lab/showcases/scripts/run_codex_debug_pipeline.py --config pipeline-lab/showcases/codex-debug-cases.yaml --case harness-codex-debug-smoke --run-id 20260512-debug --output-dir pipeline-lab/showcases/codex-debug-runs --mode mock --clean --allow-dirty`

## Manual Validation

- Confirmed current tests use `write_fake_codex`, so the prior stable test path was mock-based.
- Confirmed `/opt/homebrew/bin/codex` exists and reports `codex-cli 0.130.0`.
- Confirmed real mode invokes Codex and records `uses_real_codex: true` in temporary diagnostics.
- Confirmed generated mock artifacts are counted from changed files, not from pre-existing feature workspaces.

## Reviews

- `reviews/debug-runner-review.yaml` records a non-blocking note: real full-pipeline smoke is timeout-sensitive and should remain an operator diagnostic unless a narrower real case is introduced.
- `reviews/verification-review.md` records final manual validation and verification debt.

## Verification Debt

- Real mode did not complete a full feature within the bounded 180-second and 45-second diagnostics. The committed run remains mock mode for deterministic repeatability.
- A future real-mode acceptance suite should use longer operator timeout or a minimal target prompt specifically shaped for completion.

## Claim Provenance

- Mode metadata is proven by `run.yaml` and `summary.yaml` under `pipeline-lab/showcases/codex-debug-runs/20260512-debug/`.
- Existing fake-test behavior is proven by `tests/feature_pipeline/test_codex_e2e_runner.py` and `comparison.md`.
- Real invocation is proven by `real-mode-diagnostic.md` and temporary real summaries referenced there.
- Skill loader fix is proven by absence of `missing field` errors in the second real diagnostic and validation requiring `description:` frontmatter.

## Rollback Guidance

- Revert commits `d9df54c`, `af4b209`, and `6a0720c` to remove the debug runner, generated showcase artifacts, and skill metadata changes.
- Remove external temporary real diagnostic directories under `/tmp/codex-real-smoke*` if they are no longer needed.

## Shared Knowledge Updates

The promoted memory should update `.ai/knowledge/features-overview.md`, `.ai/knowledge/module-map.md`, and `.ai/knowledge/integration-map.md` so future agents know that Codex showcase tests have both a fast mock path and an explicit real-mode operator diagnostic path.

### Shared Knowledge Decision Table

| Knowledge file | Decision | Evidence | Future reuse |
| --- | --- | --- | --- |
| `.ai/knowledge/features-overview.md` | updated | This feature adds the Codex debug runner and stable debug run. | Helps future agents understand how showcase execution is validated. |
| `.ai/knowledge/architecture-overview.md` | confirmed unchanged | Architecture is a runner/test-lab addition, not a core pipeline architecture rewrite. | Use feature card and module map for implementation details. |
| `.ai/knowledge/module-map.md` | updated | New `run_codex_debug_pipeline.py` and `codex-debug-cases.yaml` are reusable modules. | Helps locate debug runner entrypoints. |
| `.ai/knowledge/integration-map.md` | updated | Real Codex CLI integration and mock runner comparison are now explicit. | Helps operators choose mock, dry-run, or real mode. |

## Plan Drift

- Added skill `description:` frontmatter after real Codex exposed loader errors. This was not in the initial scope but directly affected real-mode integration quality.

## Known Risks

- Real mode is slower, can time out, and can be affected by local Codex authentication, plugin sync noise, or model/runtime settings.
- Output artifacts contain absolute paths because they are diagnostic run records.

## Future Modification Notes

- Add a narrow real-mode acceptance case if CI or scheduled operator runs need a completed real Codex implementation within a strict time budget.
- Consider moving committed debug output generation outside the source repo or automatically allowing the runner output directory when the source repo is the harness itself.
