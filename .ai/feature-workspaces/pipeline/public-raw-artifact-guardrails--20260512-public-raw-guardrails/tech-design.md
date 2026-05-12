# Technical Design: Public Raw Artifact Guardrails

## Change Delta

Add tests and generator changes for wrapper execution, broad artifact
readability, compact project memory, and consistent event rendering.

## Implementation Summary

- Add wrapper smoke tests that execute the actual scripts.
- Add curated/canonical artifact scans for YAML/Markdown readability.
- Add Python source readability and compile checks without a `black`
  dependency.
- Change `compact_project_index_profile` to remove `feature_signals` and
  `feature_catalog`.
- Update goal validation to read signal counts from `discovered-signals.md`
  rather than `project-index.yaml`.
- Render gate, stale, archive, and promotion events with `event_type=...`.

## Modules And Responsibilities

- `.agents/pipeline-core/scripts/featurectl_core/cli.py`: profile compaction,
  event rendering, and promotion event generation.
- `.agents/pipeline-core/scripts/featurectl.py`: stable wrapper validated by
  executed smoke tests.
- `.agents/pipeline-core/scripts/pipelinebench.py`: stable wrapper validated by
  executed smoke tests.
- `tests/feature_pipeline/test_artifact_formatting.py`: broad source and
  artifact readability checks.
- `tests/feature_pipeline/test_featurectl_core.py`: compact profile and
  discovered signal checks.
- `tests/feature_pipeline/test_gates_and_evidence.py`: event-shape checks.
- `pipeline-lab/showcases/scripts/validate_pipeline_goals.py`: goal validation
  aligned with the new profile split.

## Dependency And Ownership Plan

No new dependency is added. Formatting enforcement uses line-length checks,
script execution, and Python compilation.

## Contracts

Public commands stay unchanged:

- `python .agents/pipeline-core/scripts/featurectl.py --help`
- `python .agents/pipeline-core/scripts/pipelinebench.py --help`
- `python .agents/pipeline-core/scripts/pipelinebench.py list-scenarios`

## API/Event/Schema Details

Generated event log entries use this key-value shape:

```text
- <timestamp> event_type=<type> key=value key=value
```

Event types include:

- `gate_status_changed`
- `artifact_marked_stale`
- `slice_completed`
- `slice_retry_completed`
- `incoming_variant_archived`
- `feature_promoted`

`project-index.yaml` no longer includes:

- `feature_signals`
- `feature_catalog`
- `source_examples`
- `test_examples`
- `doc_examples`
- `contract_examples`
- `integration_examples`

## Core Code Sketches

```python
def compact_project_index_profile(profile):
    compact = copy.deepcopy(profile)
    for key in PROFILE_EXAMPLE_KEYS | {"feature_signals", "feature_catalog"}:
        compact.pop(key, None)
    return compact
```

```python
append_execution_event(
    workspace,
    "Gate Events",
    render_key_value_event("gate_status_changed", gate=..., old_status=...)
)
```

## Data Model

`discovered-signals.md` remains the source for low-confidence detected and lab
signals. `project-index.yaml` remains the first-pass machine-readable map for
repo identity, counts, modules, scripts, and canonical features.

## Error Handling

Validation continues to report deterministic blocker strings. Wrapper tests
fail if commands exit non-zero or produce empty help/scenario output.

## Security Considerations

The feature does not execute untrusted input. Manual soft-score YAML remains
data-only and unrelated to this change.

## Test Strategy

- Red tests for wrapper execution and project-index compaction.
- Green tests for artifact readability and event rendering.
- Full feature-pipeline suite.
- Goal validation three-pass check.

## Migration Plan

Run `featurectl.py init --profile-project` after the generator change. Promote
the feature to update canonical and knowledge memory.

## Rollback Plan

Revert the feature commits. If only profile compaction is problematic, restore
`feature_signals` and `feature_catalog` in `compact_project_index_profile` and
goal validation.

## Integration Notes

The context skill already reads `features-overview.md` before
`discovered-signals.md`; this change reinforces that order by removing
low-confidence signals from `project-index.yaml`.

## Decision Traceability

- FR-001 maps to wrapper smoke tests.
- FR-002 and FR-003 map to artifact readability scans.
- FR-004 and FR-005 map to profile compaction and goal validation changes.
- FR-006 maps to featurectl event rendering and event tests.
- FR-007 maps to architecture knowledge scans.
