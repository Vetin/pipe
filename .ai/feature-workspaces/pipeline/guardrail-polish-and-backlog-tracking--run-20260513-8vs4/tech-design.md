# Technical Design: Guardrail Polish And Backlog Tracking

## Change Delta

Add guardrail coverage and small control-plane refinements to existing modules.
No new command replaces the current workflow.

## Implementation Summary

The implementation will:

- Add a GitHub Actions guardrail for wrappers, compile checks, formatting tests,
  and public raw line counts.
- Add tests that reject repeated blank lines in canonical YAML.
- Add top-level `additionalProperties: false` to `events.schema.json` and match
  it in validator behavior.
- Make `execution.md` summaries less field-by-field while preserving exact
  records in `events.yaml`.
- Extract selected validation helpers into focused validator modules.
- Add `.ai/knowledge/pipeline-backlog.md` and reference it from shared
  knowledge and feature finish artifacts.

## Modules And Responsibilities

- `.github/workflows/pipeline-guardrails.yml`: permanent CI guardrail.
- `featurectl_core/formatting.py`: readable YAML writer remains the source of
  truth for block-style YAML.
- `featurectl_core/events.py`: converts exact events into human summaries.
- `featurectl_core/validators/events.py`: validates top-level and event-level
  event sidecar fields.
- `featurectl_core/validators/gates.py`: state shape and gate vocabulary.
- `featurectl_core/validators/worktree.py`: worktree and readiness checks.
- `featurectl_core/validation.py`: orchestrates validators.
- `tests/feature_pipeline`: regression tests for schema, formatting, events,
  CI file presence, and module split.

## Dependency And Ownership Plan

The change uses only Python standard library, PyYAML already required by
featurectl, and pytest already used in tests. No production dependency is
introduced.

## Contracts

The `events.yaml` contract remains:

- top-level `artifact_contract_version`
- top-level `feature_key`
- top-level `events`
- event entries with timestamp, event type, feature key, and type-specific
  fields

The contract now rejects unknown top-level keys.

## API/Event/Schema Details

`feature_promoted` stays MVP-compatible with `canonical_path`. Future
`source_workspace` and `promotion_mode` fields are tracked in backlog rather
than added as required fields now, because historical canonical events do not
contain them.

## Core Code Sketches

```python
def summarize_event_record(event):
    if event["event_type"] == "gate_status_changed":
        return "- Updated pipeline gate progress; exact fields are in `events.yaml`."
```

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["artifact_contract_version", "feature_key", "events"]
}
```

## Data Model

No persistent runtime data is added. The new backlog is Markdown under
`.ai/knowledge/pipeline-backlog.md`. Event sidecars keep the same YAML shape
with stricter validation.

## Error Handling

Validation errors should continue returning actionable blocker messages such as
`events.yaml has unexpected top-level field debug`. CI should fail with the
underlying command output when wrappers, compile checks, tests, or raw line
counts fail.

## Security Considerations

The public raw guardrail fetches raw text and counts newlines only. It does not
execute remote content. The workflow should avoid secrets and run on checked-out
repository code.

## Test Strategy

- Unit tests for top-level event schema and validator rejection.
- Unit tests for concise narrative execution summaries.
- Artifact formatting tests for repeated YAML blank lines.
- CI workflow content test to keep raw checks permanent.
- Full `tests/feature_pipeline` after implementation.

## Migration Plan

No migration is required. The central backlog records any historical execution
log migration as deferred work.

## Rollback Plan

Revert individual slice commits. The only externally visible addition is the
CI workflow; removing it restores current local-only validation behavior.

## Integration Notes

GitHub Actions integrates with the pushed repository by using raw URLs based on
`${{ github.repository }}` and `${{ github.sha }}`. Local tests avoid network
dependency.

## Decision Traceability

- FR-001 maps to CI workflow and public raw tests.
- FR-002 maps to artifact formatting tests.
- FR-003 maps to `events.py` summary changes.
- FR-004 maps to schema and event validator changes.
- FR-005 maps to validator extraction.
- FR-006 maps to `.ai/knowledge/pipeline-backlog.md`.
