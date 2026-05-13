# Technical Design: Core Modularity And Readable Events

## Change Delta

Split helper ownership out of two oversized CLI core modules and add tests for
module boundaries, curated Markdown readability, context-signal rules, and
parseable event sidecars.

## Implementation Summary

The implementation proceeds in small mechanical slices. First, tests define the
new module and readability expectations. Then `featurectl_core` helpers are
extracted by responsibility. Next, `pipelinebench_core` helpers are extracted.
Finally, event sidecar writing and context/knowledge audits are added.

## Modules And Responsibilities

- `featurectl_core.cli`: argument parsing, command functions, and dispatch.
- `featurectl_core.formatting`: `read_yaml`, `write_yaml`, `write_text`,
  Markdown section helpers, and event-value formatting primitives.
- `featurectl_core.events`: `append_execution_event`,
  `render_execution_event`, `render_slice_completion_event`, and `events.yaml`
  sidecar writing.
- `featurectl_core.profile`: project file scanning, feature signal collection,
  canonical feature collection, and knowledge document rendering.
- `featurectl_core.validation`: workspace, artifact, execution, review,
  finish, and source-truth validation helpers.
- `featurectl_core.evidence`: evidence manifest helpers, phase files,
  red/green ordering, and slice completion metadata.
- `featurectl_core.promotion`: feature index regeneration, feature memory
  overview rendering, and status updates.
- `pipelinebench_core.scenarios`: scenario definitions and lab initialization
  document factories.
- `pipelinebench_core.score`: workspace scoring, hard checks, and soft score
  parsing.
- `pipelinebench_core.report`: benchmark and showcase Markdown report rendering.
- `pipelinebench_core.candidates`: candidate quarantine path validation.
- `pipelinebench_core.showcases`: showcase loading and step scoring.

## Dependency And Ownership Plan

The new modules should avoid importing `cli.py`. Shared constants stay in the
module that owns the behavior or in a small common module if needed. Tests own
the boundary expectations.

## Contracts

- `featurectl.py` CLI output and command names remain unchanged.
- `pipelinebench.py` CLI output and command names remain unchanged.
- `events.yaml` is a list of mappings with at least:
  - `timestamp`
  - `event_type`
- Legacy workspaces without `events.yaml` remain valid unless they are active
  workspaces created after this feature.

## API/Event/Schema Details

Example event sidecar:

```yaml
artifact_contract_version: 0.1.0
feature_key: pipeline/example
events:
  - timestamp: '2026-05-13T00:00:00Z'
    event_type: gate_status_changed
    gate: feature_contract
    old_status: pending
    new_status: approved
```

## Core Code Sketches

```python
def append_execution_event(workspace: Path, section: str, line: str) -> None:
    write_event_markdown(workspace / "execution.md", section, line)
    append_events_yaml(workspace, parse_event_line(line))
```

## Data Model

- Existing `execution.md` remains human-readable.
- New `events.yaml` stores parseable event records for new/active workspaces.
- Knowledge docs remain Markdown and YAML under `.ai/knowledge`.

## Error Handling

- If an event line cannot be parsed, write the Markdown event and skip sidecar
  update only for legacy compatibility, then validation should catch missing
  sidecar records for new workspaces.
- CLI command failures continue to raise existing expected error types.

## Security Considerations

No sensitive data is added. Public raw verification only reads public GitHub
content.

## Test Strategy

- Red tests for module existence and line-count thresholds.
- Red tests for strict curated Markdown line lengths and knowledge typo audit.
- Red tests for context skill canonical-versus-signal rules.
- Red tests for `events.yaml` generation and validation.
- Full existing feature-pipeline suite after each major slice.

## Migration Plan

Create `events.yaml` for this feature workspace and any new workspaces created
by `featurectl.py new`. Do not backfill historical canonical features in this
change.

## Rollback Plan

Revert the feature branch. Existing public wrapper and readability fixes remain
in prior canonical features if not reverted.

## Integration Notes

`run_init_profile_showcases.py` and `validate_pipeline_goals.py` already follow
the compact profile split and should continue to pass.

## Decision Traceability

- FR-001 and FR-002 are verified by one-time evidence and final verification.
- FR-003 and FR-004 are verified by module-boundary tests.
- FR-006 and FR-007 are verified by artifact formatting tests.
- FR-008 is verified by context skill tests.
- FR-009 is verified by gate/evidence and promotion tests.
