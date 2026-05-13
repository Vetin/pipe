# Feature: Guardrail Polish And Backlog Tracking

## Intent

Make the recently added pipeline guardrails permanent, easier to read, and
easier to maintain without changing the core Native Feature Pipeline workflow.

## Motivation

The latest review found that the architecture is solid, but remaining quality
issues could regress quietly: public raw checks need a permanent execution path,
YAML/Markdown readability needs tighter guardrails, `execution.md` should avoid
becoming a second machine event stream, event sidecars need stricter top-level
schema validation, validation code should continue moving into focused modules,
and verification debt needs a central retrieval point.

## Actors

- Pipeline users who rely on readable feature memory.
- Codex agents that consume `.ai/knowledge`, `execution.md`, and `events.yaml`.
- Maintainers who need focused validator modules and stable CI guardrails.

## Problem

The pipeline currently has working public raw checks and structured event
sidecars, but those protections are not yet fully anchored as permanent
regression coverage. `execution.md` still records too much event detail for a
human journal, event schema top-level fields are not locked down, and backlog
items remain buried inside feature cards.

## Goals

- Keep public raw and wrapper execution checks as a committed guardrail.
- Prevent excessive blank lines in generated YAML and core artifacts.
- Keep detailed machine events in `events.yaml` and concise narrative summaries
  in `execution.md`.
- Make `events.schema.json` reject unexpected top-level fields.
- Reduce `validation.py` responsibility by moving focused checks into validator
  modules.
- Create a central pipeline backlog for accepted verification debt.

## Non-Goals

- No rewrite of the Native Feature Pipeline skill sequence.
- No migration of every historical canonical `execution.md`.
- No new runtime service, database, or external dependency.
- No split of `pipelinebench_core/showcases.py` in this slice unless required
  by tests.

## Related Existing Features

- `pipeline/public-raw-artifact-guardrails`
- `pipeline/raw-schema-and-execution-boundary-hardening`
- `pipeline/event-schema-strictness-and-narrative-execution-logs`
- `pipeline/core-modularity-and-readable-events`

## Functional Requirements

- FR-001: The repository shall include a permanent guardrail command or CI path
  that runs wrapper help, compile checks, and public raw line-count checks.
- FR-002: Generated YAML and source-controlled YAML shall not contain excessive
  blank-line spacing between ordinary fields.
- FR-003: New `execution.md` event entries shall be concise human summaries,
  while exact event fields remain in `events.yaml`.
- FR-004: `events.schema.json` shall reject unexpected top-level fields in
  `events.yaml`.
- FR-005: Validation responsibilities shall be split further out of
  `featurectl_core/validation.py` into focused validator modules.
- FR-006: Accepted verification debt shall be tracked in a central backlog file
  referenced by shared knowledge.

## Non-Functional Requirements

- NFR-001: Existing featurectl and pipelinebench CLI contracts must stay
  backward compatible.
- NFR-002: All new checks must be deterministic in local tests; network raw
  checks may remain explicit command or CI checks.
- NFR-003: Formatting changes must keep source files under current line-length
  guardrails.
- NFR-004: Validation blocker messages must remain actionable.

## Acceptance Criteria

- AC-001: `python .agents/pipeline-core/scripts/pipelinebench.py
  check-public-raw --min-lines 5` remains available and is exercised by a
  committed guardrail.
- AC-002: Tests fail if checked-in YAML has repeated blank lines or collapsed
  one-line formatting.
- AC-003: New gate and slice updates append concise prose to `execution.md` and
  write exact records to `events.yaml`.
- AC-004: Validation fails for an `events.yaml` file with an unexpected
  top-level field.
- AC-005: `validation.py` is reduced by moving at least state/worktree or
  evidence/review checks into focused validator modules.
- AC-006: `.ai/knowledge/pipeline-backlog.md` exists and records deferred
  migration/showcase responsibilities.
- AC-007: Full feature-pipeline tests and clean public raw checks pass after
  promotion.

## Product Risks

- Over-tightening event schema could reject legitimate future event metadata.
- Over-compressing `execution.md` could remove useful human context.
- CI public raw checks can be flaky if they depend on network availability;
  local tests should still verify physical file bytes.

## Assumptions

- The public raw discrepancy from earlier reviews is now resolved in current
  raw bytes, and this work is about preventing recurrence.
- GitHub Actions is acceptable for a main-branch guardrail because this repo is
  already hosted on GitHub.
- Historical feature cards can keep their own verification debt, but durable
  backlog items should also be centralized.

## Open Questions

- Should showcase/demo code be moved out of `pipelinebench_core` now or tracked
  as backlog? Current scope tracks it as backlog.
