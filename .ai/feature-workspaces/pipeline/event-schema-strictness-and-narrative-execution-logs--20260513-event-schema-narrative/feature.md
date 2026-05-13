# Feature Contract: Event Schema Strictness And Narrative Execution Logs

## Intent

Harden the pipeline event contract so `events.yaml` is strict and parseable, while
`execution.md` reads as a human narrative rather than a duplicated machine log.

## Motivation

The previous feature established `events.yaml` as the machine-readable event
source of truth. The latest review correctly identified that the schema is still
too permissive and that execution logs can still look like machine event streams.

The review also raised public raw and formatting concerns. Those did not
reproduce on current `main`: raw line counts are correct, `FeatureCtlError` is
imported, `allow_unicode=True`, and compile checks pass. The remaining work is to
make those checks reusable and prevent drift.

## Actors

- Pipeline users reading `execution.md`.
- Future agents parsing `events.yaml`.
- Maintainers reviewing event schema and validation changes.
- Benchmark users verifying public raw artifact accessibility.

## Goals

- FR-001: Restrict `events.yaml` event types to a documented enum.
- FR-002: Reject unknown event fields in `events.yaml`.
- FR-003: Require UTC date-time event timestamps.
- FR-004: Keep detailed machine events in `events.yaml`.
- FR-005: Make generated `execution.md` entries narrative summaries.
- FR-006: Record run-plan transition when implementation becomes allowed.
- FR-007: Add a reusable public raw line-count check to `pipelinebench`.
- FR-008: Preserve current wrapper, formatting, validation, and benchmark behavior.

## Non-Goals

- Do not add external runtime dependencies.
- Do not require networked public raw checks in normal unit tests.
- Do not split `pipelinebench_core/showcases.py` in this feature.
- Do not rewrite all historical canonical execution logs.

## Functional Requirements

- FR-001: `events.schema.json` must enumerate known event types.
- FR-002: `featurectl validate` must reject unknown event types.
- FR-003: `featurectl validate` must reject unexpected event fields.
- FR-004: `featurectl validate` must reject malformed UTC timestamps.
- FR-005: New execution log entries must summarize events without `event_type=`
  machine fields.
- FR-006: New execution logs must add `## Run Plan Updates` when implementation
  becomes allowed after planning gates.
- FR-007: `pipelinebench.py check-public-raw` must verify remote or file-backed
  raw artifacts by physical newline counts.
- FR-008: Public raw and formatting helper concerns must stay covered by tests.

## Non-Functional Requirements

- No new third-party dependency.
- Tests must run offline.
- Generated Markdown line lengths must remain reviewable.
- Validation failure messages must identify the event index and field.

## Acceptance Criteria

- AC-001: Invalid `events.yaml` event types fail validation.
- AC-002: Extra event fields fail validation.
- AC-003: Non-UTC or malformed timestamps fail validation.
- AC-004: Gate, stale, slice, and promotion commands still append parseable
  `events.yaml` records.
- AC-005: New `execution.md` event entries are narrative summaries.
- AC-006: Implementation gate approval writes a run-plan update.
- AC-007: `pipelinebench.py check-public-raw` passes for file-backed fixtures.
- AC-008: Full `tests/feature_pipeline` passes.

## Assumptions

- Existing historical execution logs may remain as legacy records unless touched.
- `events.yaml` is present for new workspaces.
- Tests should avoid live GitHub dependencies and use local file-backed raw URLs.

## Open Questions

- Whether to migrate every historical canonical `execution.md` to narrative-only
  logs is deferred.

