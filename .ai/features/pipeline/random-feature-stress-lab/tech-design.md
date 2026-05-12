# Technical Design: Random Feature Stress Lab

## Change Delta

- Add a deterministic Python CLI under `pipeline-lab/showcases/scripts`.
- Add unit tests under `tests/feature_pipeline`.
- Update NFP architecture and finish skills/templates with shared-knowledge
  decision-table requirements.

## Implementation Summary

The runner generates a seeded set of ten harness feature specs, writes a
reviewable feature list, evaluates every feature for ten iterations, materializes
final artifacts, and renders comparison/report files. Tests run the CLI in a
temporary directory and inspect machine-readable summaries plus representative
artifacts.

## Modules And Responsibilities

- `run_random_feature_stress.py`: feature generation, artifact writing,
  scoring, reports, and validation.
- `tests/feature_pipeline/test_random_feature_stress.py`: regression tests for
  generated feature count, iteration count, scorecards, and shared knowledge.
- `.agents/skills/nfp-03-architecture/SKILL.md`: architecture-time shared
  knowledge decision requirements.
- `.agents/skills/nfp-11-finish/SKILL.md`: finish-time shared knowledge update
  requirements.
- Generated templates: make the expected table visible in new workspaces.

## Dependency And Ownership Plan

The script depends only on the standard library and PyYAML, matching existing
pipeline scripts. Tests own temp output creation and avoid modifying committed
run artifacts.

## Contracts

Summary YAML includes `artifact_contract_version`, `seed`, `feature_count`,
`iterations`, `total_feature_runs`, `features`, `iteration_results`,
`common_mistakes`, `applied_improvements`, `open_improvements`, and `status`.

## API/Event/Schema Details

No public API or runtime event schema. CLI options are:

- `--output-dir`
- `--run-id`
- `--seed`
- `--feature-count`
- `--iterations`
- `--clean`

## Core Code Sketches

The CLI flow is:

1. validate minimum counts
2. generate feature specs
3. write feature list
4. loop iterations and features to score outputs
5. materialize final artifacts
6. write reports and summary
7. fail if final open improvements remain

## Data Model

Feature spec fields include id, title, repository area, complexity, changed
parts, risk profile, shared pattern key, and expected artifacts. Scorecards
record iteration, feature id, status, dimensions, mistakes, and final score.

## Error Handling

The runner exits non-zero for too few features, too few iterations, missing
output directory permissions, or final open improvements.

## Security Considerations

No generated command is executed. The runner does not read secrets, call the
network, or mutate cloned repositories.

## Test Strategy

Focused tests execute the CLI with deterministic parameters, inspect summary
YAML and reports, ensure 100 scorecards exist, and verify representative
architecture/feature-card artifacts contain the shared-knowledge decision table.

## Migration Plan

No migration.

## Rollback Plan

Remove the new script, tests, skill/template wording, and generated run
directory if the lab proves noisy. No external repositories need reset.

## Integration Notes

The goal validator can later read the committed stress summary, but this change
keeps validation local to avoid making every goal run depend on generated output.

## Decision Traceability

- FR-001, FR-002: feature generator and iteration evaluator.
- FR-003: artifact writer and tests.
- FR-004: skill/template changes and artifact checks.
- FR-005, FR-006: summary/report rendering and test assertions.
