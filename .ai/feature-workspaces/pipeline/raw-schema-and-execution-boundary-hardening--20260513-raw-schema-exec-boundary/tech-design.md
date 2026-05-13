# Technical Design: Raw Schema And Execution Boundary Hardening

## Change Delta

Fix formatting helper correctness, add event schema validation, and backfill
canonical artifacts that consume the event sidecar.

## Implementation Summary

- Import `FeatureCtlError` in `featurectl_core.formatting`.
- Change YAML writer to `allow_unicode=True`.
- Add raw-byte and formatting-helper tests.
- Add `events.schema.json`.
- Add `validate_events_sidecar()` and call it from workspace validation.
- Update apex generation and affected canonical apex artifacts to include
  `events.yaml`.
- Normalize completed implementation gates in affected canonical state.

## Modules And Responsibilities

- `featurectl_core/formatting.py`: YAML and text IO behavior.
- `featurectl_core/events.py`: event sidecar read/write parsing helpers.
- `featurectl_core/validation.py`: event sidecar validation orchestration.
- `featurectl_core/profile.py`: apex template rendering.
- `tests/feature_pipeline/test_artifact_formatting.py`: raw-byte, formatting,
  and compile guardrails.
- `tests/feature_pipeline/test_gates_and_evidence.py`: event validation tests.
- `tests/feature_pipeline/test_methodology_contract.py`: schema presence and
  skill/source-of-truth contract checks.

## Dependency And Ownership Plan

No new dependency is introduced. Tests use Python stdlib plus existing PyYAML.
The implementation keeps wrappers stable and only changes internal modules and
machine-readable artifacts.

## Contracts

`events.schema.json` defines:

- top-level `artifact_contract_version`, `feature_key`, and `events`
- event record `timestamp`, `event_type`, and `feature_key`
- conditional requirements for gate, slice, retry, archive, and promotion
  events

## API/Event/Schema Details

Event records remain mappings in `events.yaml`. `event_type` decides additional
required fields. Unknown event types are allowed only when they still include the
base required fields, preserving forward compatibility.

## Core Code Sketches

```python
def validate_events_sidecar(workspace: Path) -> list[str]:
    data = read_yaml(workspace / "events.yaml")
    for event in data.get("events") or []:
        validate_event_record(event)
```

## Data Model

No database changes. The only persisted data model change is the new schema file
and stricter validation of existing YAML sidecars.

## Error Handling

Formatting helper errors must raise `FeatureCtlError`. Event validation should
return blockers through `featurectl.py validate`, not raise unexpected runtime
exceptions.

## Security Considerations

No external data is executed. Schema files and YAML are parsed as data.

## Test Strategy

- Red tests for missing `FeatureCtlError` import and Unicode escaping.
- Red tests for missing event schema and invalid event sidecar.
- Red tests for apex read-order omission and implementation gate lifecycle.
- Full `tests/feature_pipeline` before promotion.

## Migration Plan

Backfill current canonical `core-modularity-and-readable-events` artifacts and
ensure newly generated apex files include `events.yaml`.

## Rollback Plan

Revert changes to formatting, validation, schema, tests, and canonical
backfills. Existing wrappers and command names are unaffected.

## Integration Notes

The normal suite remains offline. Public raw verification is recorded as manual
evidence and is mirrored by local byte-level tests.

## Decision Traceability

- FR-001, FR-002 -> S-001 formatting helper fixes.
- FR-003 -> S-001 raw-byte guardrails.
- FR-004, FR-005, FR-006 -> S-002 event schema validation.
- FR-007, FR-008, FR-009 -> S-003 artifact boundary backfill.
