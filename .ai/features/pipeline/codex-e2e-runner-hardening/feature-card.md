# Feature Card: pipeline/codex-e2e-runner-hardening

## Intent

Make the reproducible Codex showcase runner safe and useful for real pipeline
debugging, not just fake Codex unit tests.

## Requirements

- FR-001: Existing worktrees and branches are protected unless replacement is explicit.
- FR-002: Debug runs can be normalized into portable committed artifacts.
- FR-003: Stable cases can materialize tracked template repos into clean git repos.
- FR-004: Full native and bounded outcome-smoke prompt profiles are supported.
- FR-005: Prompt validation accepts both profiles and rejects direct internal skill prompts.
- FR-006: Tests cover safety, fixture, prompt, portability, and real-mode shim paths.
- FR-007: The committed debug showcase and pipeline goal report are regenerated.

## Architecture

The E2E runner resolves source repos, prepares guarded worktrees, installs the
pipeline context, builds a prompt profile, invokes Codex, and writes runtime
manifests. The debug runner validates actual paths first, then optionally
rewrites committed reports with `$ROOT`, `$RUN_DIR`, and `$WORK_ROOT` tokens.

## Contracts

- `original_codebase.repo_path` and `original_codebase.template_path` are
  mutually exclusive.
- Worktree replacement requires `--replace-existing-worktree`, or debug
  `--clean`.
- `prompt_profile` is either `full-native` or `outcome-smoke`.
- `--portable-output` is post-validation normalization only.

## Slices

- S-001: E2E source, worktree, prompt profile, fixture, and smoke-case support.
- S-002: Debug wrapper validation, portable output, real-mode shim, and goal validator checks.
- S-003: Regenerated portable debug showcase, real diagnostic, and final validation evidence.

## Tests And Evidence

- `python -m pytest tests/feature_pipeline/test_codex_e2e_runner.py tests/feature_pipeline/test_codex_debug_runner.py tests/feature_pipeline/test_pipeline_goal_validation.py`
- `python pipeline-lab/showcases/scripts/validate_pipeline_goals.py --passes 3 --report pipeline-lab/showcases/pipeline-goal-validation-report.md`
- `python .agents/pipeline-core/scripts/featurectl.py validate --workspace ... --implementation`

## Manual Validation

- Regenerated `pipeline-lab/showcases/codex-debug-runs/20260512-debug` in mock mode with `--portable-output`; no local absolute paths remain in text artifacts.
- Ran real Codex fixture smoke with fast model arguments.
- The run completed with `uses_real_codex: true`, `returncode: 0`,
  `timed_out: false`, and all four debug artifacts present.

## Reviews

- `reviews/REV-001.yaml`: non-blocking strict review note, all requirements and slices covered.

## Verification Debt

No blocking verification debt. Default-model real Codex still timed out on the
fixture smoke, so the successful real diagnostic records the explicit fast model
argument needed for reliable local completion.

## Claim Provenance

- S-001 commit: `18ca2456cfccebde4c451fa1e28c85c27f49c3e5`
- S-002 commit: `4d96b52ee0c31a52f07fead679e798389b4d1ff1`
- Outcome-smoke tightening commit: `2b6534e`
- Regenerated debug showcase commit: `1ddad95`
- Completion evidence commit: `3291fa9`

## Rollback Guidance

Revert the hardening branch commits. Existing case files using `repo_path` and
default `full-native` profile remain compatible, so rollback is localized to
runner behavior and committed showcase output.

## Shared Knowledge Updates

### Shared Knowledge Decision Table

| Knowledge file | Decision | Evidence | Future reuse |
| --- | --- | --- | --- |
| `.ai/knowledge/features-overview.md` | updated | This feature card and promoted memory. | Future agents can find the hardened Codex E2E/debug runner capability. |
| `.ai/knowledge/architecture-overview.md` | updated | Architecture topology and regenerated debug artifacts. | Reuse source resolver, worktree guard, prompt profile, and portable writer topology. |
| `.ai/knowledge/module-map.md` | updated | Changed files and tests under `pipeline-lab/showcases/scripts` and `tests/feature_pipeline`. | Future runner work can identify ownership quickly. |
| `.ai/knowledge/integration-map.md` | updated | Real-mode diagnostic and Codex CLI invocation contracts. | Future validation can distinguish mock, dry-run, real shim, and real Codex runs. |

## Plan Drift

One additional implementation bug was found during real-mode validation:
`--codex-arg=-m` was not forwarded safely through the debug runner. It was fixed
and covered by `test_clean_rerun_forwards_replacement_and_prompt_profile`.

## Known Risks

- Real Codex completion depends on local model availability and can time out
  with the default model.
- The committed debug showcase remains mock-based for deterministic validation.

## Future Modification Notes

- Consider a documented `--real-smoke-fast` wrapper profile if real-mode smoke
  becomes part of CI.
- Keep portable-output validation enabled for committed debug artifacts.
