# Feature: Raw Schema And Execution Boundary Hardening

## Intent

Resolve the remaining review findings around raw-byte reliability, formatting
helper correctness, event sidecar schemas, execution-log boundaries, apex read
order, and implementation gate lifecycle.

## Motivation

The previous feature fixed most public artifact concerns, but the review still
identified real reliability gaps: `formatting.py` can raise `NameError` instead
of `FeatureCtlError`, Unicode YAML output is escaped, `events.yaml` has no
schema, and canonical feature artifacts do not fully document the new event
sidecar boundary.

## Actors

- Pipeline users running `featurectl.py` and `pipelinebench.py`.
- Future Codex agents reading `.ai/knowledge` and canonical feature memory.
- Reviewers inspecting raw public files from a clean checkout.

## Goals

- Make formatting helpers correct and Unicode-friendly.
- Add deterministic tests for raw-like bytes read from disk.
- Add an `events.schema.json` contract and validation for `events.yaml`.
- Make `events.yaml` the machine-readable event source and `execution.md` the
  human-readable journal.
- Add `events.yaml` to apex read order.
- Normalize completed implementation gates to `complete`.

## Non-Goals

- Do not replace `execution.md`; it remains the human-readable run journal.
- Do not add a network-dependent GitHub raw test to the normal test suite.
- Do not perform the larger validator package split unless required to land
  this fix safely.
- Do not separate `showcases.py` out of `pipelinebench_core` in this feature.

## Functional Requirements

- FR-001: `read_yaml()` must raise `FeatureCtlError` for missing paths and
  non-mapping YAML.
- FR-002: `write_yaml()` must emit block-style YAML with `allow_unicode=True`.
- FR-003: source-controlled wrapper, `.gitignore`, canonical index, and
  canonical `events.yaml` files must be checked from disk for real newline
  counts.
- FR-004: the repository must include
  `.agents/pipeline-core/scripts/schemas/events.schema.json`.
- FR-005: `featurectl.py validate --workspace <workspace>` must validate
  active or canonical `events.yaml` files when present.
- FR-006: event validation must require `timestamp`, `event_type`, and
  `feature_key`; event-specific fields must be validated for gate, slice,
  retry, archive, and promotion events.
- FR-007: new and promoted apex artifacts must list `events.yaml` before the
  evidence manifest.
- FR-008: canonical completed features with completed slices must use
  `implementation: complete`, not `implementation: approved`.
- FR-009: final feature memory must explain that `events.yaml` is the machine
  event source while `execution.md` is narrative.

## Non-Functional Requirements

- NFR-001: The normal test suite must stay offline and deterministic.
- NFR-002: No new production dependency is allowed.
- NFR-003: Existing wrapper command names and arguments must remain stable.
- NFR-004: Generated YAML and Markdown must remain readable from raw bytes.

## Acceptance Criteria

- AC-001: Tests prove `read_yaml()` raises `FeatureCtlError`, not `NameError`.
- AC-002: Tests prove Unicode YAML values are written unescaped.
- AC-003: Tests prove source-controlled raw-byte artifacts are physically
  multi-line.
- AC-004: Tests prove `events.schema.json` exists and has required event rules.
- AC-005: Tests prove invalid `events.yaml` is rejected by workspace
  validation.
- AC-006: Canonical `core-modularity-and-readable-events` has
  `implementation: complete` and apex includes `events.yaml`.
- AC-007: Full `tests/feature_pipeline` passes before promotion.

## Assumptions

- The review’s one-line public raw results are a cache/tooling inconsistency
  when curl from this machine reports correct multi-line raw files.
- It is acceptable to keep human-readable event summaries in `execution.md`
  while treating `events.yaml` as the machine event source.

## Open Questions

- Whether to enforce `events.yaml` for all legacy canonical features or only
  features created after the sidecar was introduced. For this feature, enforce
  validation when the file exists and require it for new workspaces.
