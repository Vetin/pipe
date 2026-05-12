# Technical Design: Portable Artifact Consistency

## Implementation Summary

Add source-truth validators, portable profile output, catalog row labels,
structured event-log validation, semantic label handling in evidence manifests,
and source readability tests. Migrate checked-in artifacts to the new contracts.

## Change Delta

This is a compatibility hardening change over existing artifacts and tests.

## Modules And Responsibilities

- `featurectl.py`: profile rendering, promotion sync, validation, evidence, and
  event helpers.
- `tests/feature_pipeline`: regression coverage.
- `.ai/knowledge`: synchronized retrieval memory.

## Dependency And Ownership Plan

Source-truth changes land before event/evidence migration. Readability guards
land after migrations.

## API/Event/Schema Details

No public API is added. Internal event schema requires structured
`event_type=slice_completed` and `event_type=slice_retry_completed` entries.

## Core Code Sketches

`complete-slice` stores non-hex `--diff-hash` values as `change_label` and
validation accepts commit, real diff hash, or change label.

## Data Model

`project.root` is `"."`; canonical feature keys appear in both feature memory
and project index; evidence manifests can contain `change_label`.

## Error Handling

Validation returns deterministic blockers for missing canonical keys,
unstructured slice events, and invalid evidence metadata.

## Security Considerations

No secrets are read or written. Removing absolute paths improves portability and
reduces machine-local leakage.

## Test Strategy

Focused tests cover profile portability, knowledge sync, event schema, evidence
metadata, and source readability; full pipeline tests validate integration.

## Migration Plan

Run mechanical migrations over `.ai/features`, `.ai/feature-workspaces`, and
`.ai/knowledge`, then validate every feature workspace.

## Rollback Plan

Revert commits if validation blocks unrelated urgent work.

## Integration Notes

Promotion calls the canonical memory sync helper after feature index refresh.

## Decision Traceability

FR-001 through FR-003 map to S-001; FR-004, FR-005, and FR-007 map to S-002;
FR-006 maps to S-003.

## Touchpoints

- `.agents/pipeline-core/scripts/featurectl.py`
- `tests/feature_pipeline/test_artifact_formatting.py`
- `tests/feature_pipeline/test_featurectl_core.py`
- `tests/feature_pipeline/test_finish_promote.py`
- `tests/feature_pipeline/test_gates_and_evidence.py`
- `.ai/features/**/execution.md`
- `.ai/feature-workspaces/**/execution.md`
- `.ai/**/evidence/manifest.yaml`
- `.ai/knowledge/*`

## Contracts

- `project.root` is always `"."` in shared knowledge.
- `change_label` stores non-hash completion labels.
- `diff_hash` is reserved for hexadecimal hashes.
- Event log slice completions use:

```text
event_type=slice_completed slice=S-001 attempt=1 reason=initial
event_type=slice_retry_completed slice=S-001 attempt=2 reason=historical-retry supersedes=attempt-1
```

## Validation

Validation checks canonical memory synchronization, event schema consistency,
and evidence metadata shape. Formatting tests guard source-controlled artifact
readability.
