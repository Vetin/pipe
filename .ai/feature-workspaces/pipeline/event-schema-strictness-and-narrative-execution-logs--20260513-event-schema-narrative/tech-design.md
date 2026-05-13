# Technical Design: Event Schema Strictness And Narrative Execution Logs

## Change Delta

Tighten `events.yaml` validation, change new `execution.md` event entries to
narrative summaries, add run-plan transition recording, and add an explicit
public raw check command to `pipelinebench.py`.

## Implementation Summary

The implementation changes are scoped to event schema/validation/rendering,
pipelinebench command wiring, and regression tests.

## Modules And Responsibilities

- `featurectl_core/events.py`: parse machine event lines, write `events.yaml`,
  and render human summaries in `execution.md`.
- `featurectl_core/validators/events.py`: enforce strict event type and field
  rules.
- `featurectl_core/profile.py`: render new workspaces with narrative event
  summary and initialize `events.yaml`.
- `featurectl_core/cli.py`: record run-plan update on implementation gate
  approval.
- `pipelinebench_core/raw_checks.py`: fetch raw content and verify newline
  counts.
- `pipelinebench_core/cli.py` and `commands.py`: expose `check-public-raw`.

## Dependency And Ownership Plan

No new dependency is added. Network behavior uses Python standard library and is
only invoked by the explicit benchmark command.

## Contracts

- `.agents/pipeline-core/scripts/schemas/events.schema.json`
- `events.yaml` generated beside each feature workspace.
- `pipelinebench.py check-public-raw --base-url <url> --path <path>`

## API/Event/Schema Details

Event types:

- `run_initialized`
- `gate_status_changed`
- `slice_completed`
- `slice_retry_completed`
- `feature_promoted`
- `incoming_variant_archived`
- `artifact_marked_stale`
- `public_raw_verified`
- `verification_completed`
- `review_completed`

Unknown event types and fields are invalid. Timestamps must be UTC strings that
end in `Z`.

## Core Code Sketches

`append_execution_event()` should parse the rendered machine event, write it to
`events.yaml`, and append a human summary to `execution.md`.

`validate_event_record()` should compare event fields against a base field set
and type-specific field set.

## Data Model

`events.yaml` remains:

```yaml
artifact_contract_version: 0.1.0
feature_key: pipeline/example
events:
  - timestamp: "2026-05-13T16:00:00Z"
    event_type: run_initialized
    feature_key: pipeline/example
```

## Error Handling

Validation returns precise blocker messages. Public raw checks raise a benchmark
error when a URL cannot be fetched or a path has too few lines.

## Security Considerations

The raw check command fetches only user-provided URLs. It does not execute remote
content.

## Test Strategy

- Unit-style CLI tests for invalid event type, unknown fields, and timestamps.
- Existing gate/slice/promotion tests updated to assert `events.yaml` details and
  narrative `execution.md` summaries.
- Pipelinebench test using `file://` fixtures for raw checks.
- Full `tests/feature_pipeline` verification before promotion.

## Migration Plan

New workspaces use narrative execution entries. The latest canonical feature may
be backfilled where useful, but broad historical migration is out of scope.

## Rollback Plan

Revert this feature branch or the promoted canonical commit.

## Integration Notes

The raw check command is independent of score-run and report generation. It can
be used manually or in CI later.

## Decision Traceability

- FR-001 through FR-004 map to strict schema and validator changes.
- FR-005 and FR-006 map to execution narrative and run-plan transition changes.
- FR-007 maps to the public raw benchmark command.

