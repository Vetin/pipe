# Technical Design: Artifact Readability And Execution Semantics

## Change Delta
Add formatting helpers and tests, restructure `execution.md` rendering/appending/validation, require retry attempt and reason, add `lab_signal` profile category, add manual soft-score input to `pipelinebench.py`, and update ADR/knowledge docs.

## Implementation Summary
`featurectl.py` will write Markdown through explicit templates and YAML through a single readable dump helper. Event writers will target `## Event Log`; current-state writing will rewrite `## Current Run State`. Retry events will include attempt and reason. `pipelinebench.py` will parse a soft-score YAML file and render a score summary.

## Modules And Responsibilities
- `.agents/pipeline-core/scripts/featurectl.py`: formatting helper, execution event writer, retry semantics, profile categories, validation rules.
- `.agents/pipeline-core/scripts/pipelinebench.py`: manual soft-score parsing and reporting.
- `tests/feature_pipeline/test_artifact_formatting.py`: generated artifact readability checks.
- `tests/feature_pipeline/test_finish_promote.py`: execution structure and retry validation.
- `tests/feature_pipeline/test_gates_and_evidence.py`: complete-slice retry CLI behavior.
- `tests/feature_pipeline/test_featurectl_core.py`: `lab_signal` and discovered-signals rendering.
- `tests/feature_pipeline/test_pipelinebench.py`: soft-score input/reporting.
- `.ai/knowledge/*`: promoted architecture/ADR memory.

## Dependency And Ownership Plan
Formatting helpers land first because all later artifact rewrites depend on readable output. Execution structure and retry semantics land together. Profile category and benchmark scoring are independent. Knowledge/ADR updates land after implementation validation.

## Contracts
`execution.md` structure:

```markdown
## Current Run State

Current step:
Next recommended skill:
Blocking issues:
Last updated:

## Event Log

- timestamp event_type=... key=value ...

## History
```

Retry event shape:

```text
event_type=slice_retry_completed slice=S-001 attempt=2 reason=<text>
```

Manual soft score shape:

```yaml
architecture_clarity: 4
module_communication_quality: 5
adr_usefulness: 3
reuse_quality: 4
review_quality: 4
comments: "Good module communication, but rollback detail is thin."
```

## API/Event/Schema Details
`complete-slice --append-retry` gains `--retry-reason`. The CLI fails if retry is requested without a non-empty reason. The manifest records retry attempts; `execution.md` records the retry event.

## Core Code Sketches
Use `execution_section_bounds(content, heading)` to replace or validate sections. `append_execution_event` inserts under `## Event Log` before `## History`. `write_current_run_state` rewrites the current state section. `pipelinebench score-run` reads soft-score YAML and writes a Markdown table plus aggregate.

## Data Model
Profile catalog entries may use `kind: canonical`, `kind: detected`, or `kind: lab_signal`. `lab_signal` entries are only preferred when working on `pipeline-lab` or benchmark infrastructure.

## Error Handling
Validation emits blockers for missing current state fields, missing event log, gate/slice events outside event log, retry events without attempt/reason, and collapsed generated artifacts.

## Security Considerations
Manual score YAML is parsed as data only with `yaml.safe_load`; comments are rendered as text.

## Test Strategy
Focused tests per slice plus full `python -m pytest tests/feature_pipeline`. Add goal validation updates only if the new contracts affect hard-check expectations.

## Migration Plan
Normalize current pipeline execution logs, add attempt/reason to existing retry lines, regenerate knowledge, and add ADR index entries.

## Rollback Plan
Revert feature branch commits. If partial rollback is needed, keep formatting helpers and disable only the stricter execution validators.

## Integration Notes
No external dependencies are introduced. The existing PyYAML dependency is reused.

## Decision Traceability
FR-001 and FR-002 map to formatting helpers/tests. FR-003 through FR-006 map to execution and retry semantics. FR-007 and FR-008 map to profile rendering. FR-009 maps to `pipelinebench.py`. FR-010 maps to ADR/knowledge docs.
