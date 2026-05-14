# Technical Design: Guardrail Status And Summary Polish

## Change Delta

Implement four compatible changes: add a guardrail status knowledge document,
compact promoted execution summaries from `events.yaml`, extract review
validation helpers, and harden formatting tests for generated YAML and backlog
readability.

## Implementation Summary

The implementation keeps existing CLI contracts stable. `featurectl.py promote`
will compact the canonical `execution.md` event section after writing the
`feature_promoted` sidecar record. Review validation moves into
`featurectl_core/validators/review.py`. Artifact tests gain hard checks for the
guardrail status document and blank-line-free generated YAML.

## Modules And Responsibilities

- `featurectl_core/events.py`: render compact event summaries and rewrite only
  the `## Event Log` section.
- `featurectl_core/cli.py`: call summary compaction during promotion.
- `featurectl_core/validators/review.py`: validate review YAML artifacts and
  critical blocker semantics.
- `featurectl_core/validation.py`: import review validation and remain the
  orchestration layer.
- `tests/feature_pipeline/test_artifact_formatting.py`: enforce status,
  readability, backlog, and modularity invariants.
- `tests/feature_pipeline/test_finish_promote.py`: prove promotion summary
  compaction preserves `events.yaml`.

## Dependency And Ownership Plan

No new dependency is required. Ownership remains within the pipeline control
plane and generated knowledge layer. The implementation touches only pipeline
scripts, tests, and `.ai/knowledge` docs.

## Contracts

- `events.yaml` remains the exact machine event source of truth.
- `execution.md` remains a human journal and grouped narrative summary.
- `featurectl.py promote` keeps its existing CLI contract and stdout shape.
- `featurectl.py validate --review` keeps existing review blocker wording.

## API/Event/Schema Details

No public command arguments change. `events.yaml` remains unchanged as the
machine event contract. `execution.md` output changes only in promoted canonical
features, where the event log becomes a grouped human summary.

## Core Code Sketches

```python
events = read_events_sidecar(workspace).get("events", [])
summary = render_compact_event_summary(events)
replace_execution_event_log(workspace, summary)
```

Review validation moves without changing callers:

```python
from .validators.review import validate_review_minimum
```

## Data Model

Add `.ai/knowledge/pipeline-guardrails-status.md` with sections for raw checks,
wrapper checks, compile checks, artifact formatting, workflow visibility, and
latest local verification. No existing YAML schema changes are required.

## Security Considerations

Public raw checks fetch text and count lines only. They do not execute remote
content. No secrets or credentials are introduced.

## Error Handling

If `events.yaml` is missing or malformed, summary compaction leaves the current
execution log in place and validation reports the sidecar issue. Review
validation continues returning file-relative blocker messages.

## Test Strategy

- Red/green artifact formatting test for missing guardrail status and YAML blank
  line noise.
- Promotion test proving compact canonical event summary and exact sidecar
  preservation.
- Review and formatting tests proving validator extraction and stable blockers.
- Final full `tests/feature_pipeline` suite, public raw check, compileall, and
  `git diff --check`.

## Migration Plan

No migration is required. New promotions use compact summaries. Historical
canonical execution logs remain valid and are tracked as future backlog work.

## Rollback Plan

Revert slices in reverse order. Summary compaction can be disabled by removing
the promotion call while preserving exact sidecar events. Review validation can
move back into `validation.py` without artifact migration.

## Integration Notes

`pipelinebench.py check-public-raw` remains the durable raw guardrail. GitHub
Actions continues to run wrapper help, compileall, artifact formatting, and
public raw checks.

## Decision Traceability

- FR-001, FR-002, and FR-006 map to status docs, formatting tests, and knowledge
  updates.
- FR-003 and FR-004 map to event summary compaction.
- FR-005 maps to `validators/review.py`.
