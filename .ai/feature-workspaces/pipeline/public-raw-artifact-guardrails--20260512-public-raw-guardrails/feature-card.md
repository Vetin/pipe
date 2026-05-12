# Feature Card: pipeline/public-raw-artifact-guardrails

## Intent

Make stale public raw findings and artifact-readability regressions impossible
to miss from a clean checkout. The feature guards wrapper execution, readable
source-controlled artifacts, compact project memory, profile signal ownership,
and structured execution events.

Source revision: `1126b05`.

## Requirements

- FR-001: wrapper tests execute `featurectl.py` and `pipelinebench.py` commands.
- FR-002: source-controlled canonical YAML, Markdown, `.gitignore`, and Python
  files are scanned for collapsed files and long lines.
- FR-003: raw evidence command/output logs remain exempt from curated-document
  readability rules.
- FR-004: `project-index.yaml` stays compact and excludes discovered signals and
  catalog entries.
- FR-005: discovered feature signals and catalog entries live in
  `discovered-signals.md`.
- FR-006: new gate, stale, slice, retry, archive, and promotion events use
  `event_type=` records.
- FR-007: architecture knowledge uses `evidence/`, not `evidence//`.

## Architecture

The public CLIs remain stable wrappers. Behavior lives behind
`featurectl_core.cli` and `pipelinebench_core.cli`. The profile contract now
separates first-pass project memory from source leads:

- `project-index.yaml`: compact repo metadata, counts, modules, scripts,
  package manifests, and canonical features.
- `profile-examples.yaml`: representative file examples.
- `discovered-signals.md`: low-confidence source, doc, and lab signals.

`run_init_profile_showcases.py` was updated to read that split contract so
stable init profiling validates the same artifact boundaries that normal
context discovery uses.

## Contracts

- `featurectl.py --help` must print command help.
- `pipelinebench.py --help` and `pipelinebench.py list-scenarios` must print
  benchmark output.
- New execution events use key-value records with `event_type=<type>`.
- Slice retries must include an attempt number, reason, and superseded attempt.
- `project-index.yaml` must not contain `feature_signals` or
  `feature_catalog`.

## Slices

- S-001: added executable wrapper, `.gitignore`, Python source, and curated
  artifact readability guards.
- S-002: compacted project-index output and updated both goal validation and
  init-profile showcase validation to consume `discovered-signals.md`.
- S-003: generated structured event records for gates, stale markers,
  promotion, archive-as-variant, slice completion, and retries.

## Tests And Evidence

- `python -m pytest tests/feature_pipeline/test_artifact_formatting.py -q`
- `python -m pytest tests/feature_pipeline/test_featurectl_core.py tests/feature_pipeline/test_pipeline_goal_validation.py -q`
- `python -m pytest tests/feature_pipeline/test_gates_and_evidence.py tests/feature_pipeline/test_finish_promote.py -q`
- `python -m pytest tests/feature_pipeline/test_init_profile_showcases.py tests/feature_pipeline/test_pipeline_goal_validation.py tests/feature_pipeline/test_featurectl_core.py -q`
- `python -m unittest discover -s tests/feature_pipeline`
- `python -m pytest tests/feature_pipeline -q`
- `python pipeline-lab/showcases/scripts/validate_pipeline_goals.py --passes 3 --report /tmp/pipeline-goal-validation-public-raw.md`
- `git diff --check`

Raw final verification output is stored in
`evidence/final-verification-output.log`.

## Manual Validation

- Wrapper smoke tests printed real help and scenario output.
- Full `unittest` discovery passed with 149 tests.
- Full pytest passed with 149 tests and 228 subtests.
- Pipeline goal validation passed three times with zero failures.
- `git diff --check` passed.

## Reviews

- Strict review found no blocking findings.
- The review specifically checked stale public raw claims, wrapper execution,
  line-based `.gitignore`, profile memory separation, and event-type records.
- A verification-loop failure in the init-profile showcase runner was fixed,
  rechecked, and recorded as S-002 retry attempt 2.

## Verification Debt

- `python -m black --check .agents tests pipeline-lab` was not run because
  `black` is not installed locally.
- Accepted residual risk: no-dependency readability tests compile Python files,
  execute wrappers, guard curated artifacts, and enforce line-length limits.

## Claim Provenance

| Claim | Evidence |
| --- | --- |
| Wrappers are executable and not no-op files. | `test_pipeline_cli_wrappers_execute_real_commands` plus final wrapper smoke commands. |
| `.gitignore` is line-based. | `test_gitignore_is_line_based`. |
| Curated artifacts are readable. | `test_canonical_and_knowledge_artifacts_are_readable`. |
| Python sources are readable and compile. | `test_source_controlled_python_files_are_readable`. |
| Project index is compact. | `test_project_index_profile_is_compact`. |
| Discovered signals own catalog data. | `test_profile_generation_writes_compact_index_and_signal_sidecar`. |
| Showcase init profiling follows the split contract. | `test_runner_profiles_repositories_three_times_and_compares_outputs`. |
| New execution records are structured. | `test_gates_and_evidence.py` and `test_finish_promote.py`. |

## Rollback Guidance

Revert this feature branch or the promoted canonical feature commits. Rollback
restores the previous profile shape and event rendering while leaving earlier
canonical feature memory intact. After rollback, run
`python .agents/pipeline-core/scripts/featurectl.py init --profile-project` to
regenerate knowledge with the restored profile contract.

## Shared Knowledge Updates

- `.ai/knowledge/architecture-overview.md` now documents compact project memory
  and public raw readability guardrails.
- `.ai/knowledge/module-map.md` now records the init-profile showcase runner as
  a profile contract consumer.
- `.ai/knowledge/integration-map.md` now shows the split between compact
  project profile data and discovered signal data for showcase validation.

### Shared Knowledge Decision Table

| Knowledge file | Decision | Evidence | Future reuse |
| --- | --- | --- | --- |
| `.ai/knowledge/features-overview.md` | deferred until promotion | Promotion updates canonical feature memory. | Future agents should find this feature after `nfp-12-promote`. |
| `.ai/knowledge/architecture-overview.md` | updated | Added compact profile and public raw guardrail sections. | Context discovery can separate source truth from signal leads. |
| `.ai/knowledge/module-map.md` | updated | Added `run_init_profile_showcases.py` as a profile contract consumer. | Showcase changes can find the runner ownership boundary. |
| `.ai/knowledge/integration-map.md` | updated | Added project profile to init showcase runner integration. | Future profile contract changes must update both consumers. |

## Plan Drift

- The public wrapper and `.gitignore` findings were stale locally, so the
  implementation added executable regression tests instead of only rewriting
  those files.
- Final verification exposed an additional caller drift in
  `run_init_profile_showcases.py`; S-002 received a retry instead of hiding the
  failure.
- Event logs remain key-value Markdown lines. A future feature can move them to
  a full YAML event block if needed.

## Known Risks

- `featurectl_core.cli` remains large. This feature strengthens guards but does
  not finish decomposing it into domain modules.
- Markdown signal parsing in the init-profile showcase runner is intentionally
  simple and tied to the generated `discovered-signals.md` heading shape.

## Future Modification Notes

- Any project-profile contract change must update `featurectl_core.cli`,
  `validate_pipeline_goals.py`, `run_init_profile_showcases.py`, and the profile
  tests together.
- Any event-rendering change must preserve retry attempt and reason metadata.
