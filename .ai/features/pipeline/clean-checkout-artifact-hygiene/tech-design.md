# Technical Design: Clean Checkout Artifact Hygiene

## Change Delta

Update profile rendering, signal rendering, evidence manifest metadata, CLI
module layout, tests, and current generated artifacts.

## Implementation Summary

- Move current top-level CLI implementations to core modules and replace the
  top-level files with wrappers.
- Add profile compaction helpers that strip verbose example arrays from
  `project-index.yaml` and write them to `profile-examples.yaml`.
- Render discovered signals in two readable sections.
- Add default evidence completion identity policy metadata and backfill current
  manifests with change-label-only slices.
- Update tests to cover generated promote readability and wrapper/core layout.

## Modules And Responsibilities

- `.agents/pipeline-core/scripts/featurectl.py`: stable CLI wrapper.
- `.agents/pipeline-core/scripts/featurectl_core/cli.py`: existing featurectl
  implementation and profile rendering logic.
- `.agents/pipeline-core/scripts/pipelinebench.py`: stable benchmark wrapper.
- `.agents/pipeline-core/scripts/pipelinebench_core/cli.py`: existing benchmark
  implementation.
- `tests/feature_pipeline/test_artifact_formatting.py`: readability and wrapper
  layout guards.
- `tests/feature_pipeline/test_featurectl_core.py`: profile split and signal
  rendering checks.

## Dependency And Ownership Plan

No new dependencies. `black` remains optional because it is not installed in the
current environment.

## Contracts

Public CLI contracts remain:

- `python .agents/pipeline-core/scripts/featurectl.py ...`
- `python .agents/pipeline-core/scripts/pipelinebench.py ...`

## API/Event/Schema Details

`project-index.yaml` remains YAML but no longer stores verbose `*_examples`
arrays. `profile-examples.yaml` stores those arrays under the same keys.

Evidence manifests add:

```yaml
completion_identity_policy:
  diff_hash: hexadecimal git diff or commit-derived hash when available
  change_label: semantic label when a real diff hash is unavailable
```

Legacy manifests may add:

```yaml
legacy_tolerance:
  missing_diff_hash_when_change_label_present: true
```

## Core Code Sketches

```python
def project_index_profile(profile):
    return {k: v for k, v in profile.items() if k not in EXAMPLE_KEYS}
```

```python
from featurectl_core.cli import main
raise SystemExit(main())
```

## Data Model

Verbose example keys:

- `source_examples`
- `test_examples`
- `doc_examples`
- `contract_examples`
- `integration_examples`

## Error Handling

Wrapper import failures should fail fast with Python import errors. Validation
continues to report deterministic blocker strings.

## Security Considerations

No network, credentials, or secret handling changes.

## Test Strategy

- Focused red/green tests for profile split and signal formatting.
- Wrapper smoke tests for both CLIs.
- Formatting tests for root artifacts and generated init/new/promote artifacts.
- Full `tests/feature_pipeline` suite.

## Migration Plan

Run `featurectl.py init --profile-project` with the new renderer, then backfill
current evidence manifests with policy metadata.

## Rollback Plan

Restore the previous monolithic script files and project profile format. Remove
`profile-examples.yaml` if rollback is required.

## Integration Notes

Context skill documentation must mention `profile-examples.yaml` and strict
`lab_signal` consumption rules.

## Decision Traceability

- FR-001 maps to artifact formatting tests.
- FR-002 and FR-003 map to profile renderer/tests.
- FR-004 maps to discovered signal renderer/tests.
- FR-005 maps to evidence manifest defaults/backfill.
- FR-006 maps to wrapper smoke tests.
- FR-007 maps to context skill docs.
