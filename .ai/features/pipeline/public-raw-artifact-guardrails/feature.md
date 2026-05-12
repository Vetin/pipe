# Feature: Public Raw Artifact Guardrails

## Intent

Harden the Native Feature Pipeline against stale or public-raw readability
regressions by making wrapper execution, source formatting, project-profile
separation, and execution-event semantics independently testable from a clean
checkout.

## Motivation

The latest external review reported several stale findings that the current
local tree already disproves, including no-op wrappers and a one-line
`.gitignore`. The same review also exposed real gaps: guards are not broad
enough, `project-index.yaml` still carries low-confidence signal data, and event
logs are structured inconsistently across gate, slice, retry, and promotion
events.

## Actors

- Codex agents using `.ai/knowledge` as retrieval memory.
- Pipeline maintainers reviewing public raw files.
- Human reviewers checking clean-checkout behavior.

## Goals

- Prove wrapper scripts execute real CLI behavior, not only contain expected
  text.
- Scan source-controlled canonical YAML and Markdown artifacts broadly for
  readability.
- Keep `.gitignore` and Python source formatting guarded without requiring
  `black`.
- Move discovered feature signals and catalog details out of
  `project-index.yaml`.
- Standardize generated event log lines for gate, scope, slice, archive, and
  promotion events.

## Non-Goals

- Fully decomposing `featurectl_core.cli` into domain modules.
- Rewriting historical evidence logs or command-output files.
- Changing public command names or featurectl/pipelinebench CLI contracts.

## Functional Requirements

- FR-001: Wrapper tests must execute `featurectl.py --help`,
  `pipelinebench.py --help`, and `pipelinebench.py list-scenarios` and assert
  non-empty command output.
- FR-002: Artifact readability tests must scan source-controlled canonical
  feature YAML/Markdown, knowledge YAML/Markdown, `.gitignore`, and Python
  sources for collapsed files and long lines.
- FR-003: One-line evidence command or output files may be exempt, but
  feature-card, execution, state, feature, and manifest artifacts may not be
  collapsed.
- FR-004: `project-index.yaml` must keep repo metadata, counts, modules,
  package manifests, scripts, and canonical feature references only.
- FR-005: Discovered signals and feature catalog entries must live in
  `.ai/knowledge/discovered-signals.md`, not in `project-index.yaml`.
- FR-006: New generated execution events must use a consistent
  `event_type=<type>` key-value shape.
- FR-007: Architecture knowledge must not contain the `evidence//` typo.

## Non-Functional Requirements

- NFR-001: Existing CLI commands remain backward-compatible.
- NFR-002: Validation must run without network access.
- NFR-003: Source formatting checks must work without installing `black`.
- NFR-004: Generated Markdown must keep one heading per line and normal section
  spacing.

## Acceptance Criteria

- AC-001: `python -m pytest tests/feature_pipeline/test_artifact_formatting.py`
  catches no-op wrappers and collapsed canonical artifacts.
- AC-002: `python -m pytest tests/feature_pipeline/test_featurectl_core.py`
  proves the compact project index excludes discovered signals and catalog
  entries.
- AC-003: `python -m pytest tests/feature_pipeline/test_gates_and_evidence.py`
  proves new gate/slice/promotion events use consistent `event_type=` entries.
- AC-004: `python -m pytest tests/feature_pipeline/test_pipeline_goal_validation.py`
  passes after profile compaction changes.
- AC-005: `python -m pytest tests/feature_pipeline -q` passes.
- AC-006: `git diff --check` passes.

## Assumptions

- The public raw one-line wrapper and `.gitignore` reports are stale relative to
  local `main` at `a5d736f`.
- Evidence command/output logs may remain one-line because they are raw
  captured command artifacts, not curated documentation.

## Open Questions

- Should a later feature convert event logs from key-value Markdown lines to
  full YAML event blocks?
