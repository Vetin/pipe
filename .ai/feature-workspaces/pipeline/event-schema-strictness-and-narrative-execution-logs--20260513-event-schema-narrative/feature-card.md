# Feature Card: Event Schema Strictness And Narrative Execution Logs

## Summary

This feature applies the remaining confirmed review findings after verifying
that the raw-wrapper and `formatting.py` concerns were already fixed on `main`.

## Implementation

- Tightened `events.schema.json` with an event type enum.
- Added strict `events.yaml` validation for unknown event types, unexpected
  fields, malformed UTC timestamps, and duplicate slice completion events.
- Changed new `execution.md` event entries into human narrative summaries.
- Added `## Run Plan Updates` when implementation becomes allowed.
- Added `pipelinebench.py check-public-raw` for explicit public raw line checks.

## Manual Validation

- `pipelinebench.py check-public-raw --min-lines 5` passed against current
  GitHub raw URLs.
- Generated execution logs were inspected to confirm narrative summaries.
- `events.yaml` was inspected to confirm machine event records remain complete.

## Verification Debt

- Historical canonical execution logs were not globally migrated.
- Showcase/demo logic still remains inside `pipelinebench_core/showcases.py`.

## Claim Provenance

- Event strictness is backed by `tests/feature_pipeline/test_gates_and_evidence.py`.
- Narrative execution behavior is backed by `test_featurectl_core.py`,
  `test_gates_and_evidence.py`, and `test_finish_promote.py`.
- Public raw checks are backed by `tests/feature_pipeline/test_pipelinebench.py`.
- Full verification passed with `167 passed, 328 subtests passed`.

## Shared Knowledge Updates

- `.ai/knowledge/architecture-overview.md` should describe strict event sidecar
  validation and narrative execution summaries.
- `.ai/knowledge/module-map.md` should mention `pipelinebench_core/raw_checks.py`.
- `.ai/knowledge/integration-map.md` should mention the public raw check command.
- `.ai/knowledge/adr-index.md` should reference ADR-007 after promotion.

## Rollback Guidance

Revert this feature branch before promotion or revert the promoted canonical
feature commit on `main`.

