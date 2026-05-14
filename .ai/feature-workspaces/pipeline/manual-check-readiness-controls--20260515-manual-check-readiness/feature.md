# Feature: Manual Check Readiness Controls

## Intent

Make the pipeline ready for meaningful manual checking by closing the control
plane gaps that still allow ambiguous state transitions, planning-only
validation failures, weak docs-consulted proof, and mock-only Codex confidence.

## Motivation

The repository is structurally aligned with the Native Feature Pipeline plan,
but manual checking should not start until the system can prove that planning
packages validate without implementation permission, state transitions happen
through `featurectl.py`, scope changes are operational, docs-consulted entries
prove real usage, and real Codex behavioral tests are available as explicit
opt-in checks.

## Actors

- Pipeline maintainers preparing manual checking.
- Codex agents following `AGENTS.md` and the `nfp-*` skills.
- Reviewers validating feature workspaces and real e2e behavior.

## Problem

Current tests cover mechanics and mock runner behavior. The control plane lacks
first-class commands for step transitions and scope changes. Readiness
validation requires approvals even for planning-only workflows. Docs-consulted
validation only checks marker strings. Real Codex e2e behavior exists only as a
future/manual concept, not an opt-in test scaffold.

## Goals

- Add `featurectl.py step set` for legal state transitions.
- Add `featurectl.py validate --planning-package` separate from
  implementation readiness.
- Add `featurectl.py scope-change` for returning to earlier steps and marking
  stale artifacts.
- Strengthen docs-consulted validation so sections contain existing paths and
  non-empty usage explanations.
- Document `events.yaml`, review artifact types, project profile artifacts, and
  TDD subagent fallback in official skills/docs.
- Add optional real Codex behavioral e2e tests gated by environment variables.
- Add a manual-check preflight script and test matrix documentation.
- Add uniform skill contract tests for all `nfp-*` skills.

## Non-Goals

- No requirement to run real Codex e2e in default CI.
- No removal of existing mock e2e runner tests.
- No migration of every historical canonical execution journal.
- No broad rewrite of featurectl or pipelinebench architecture.

## Functional Requirements

- FR-001: `featurectl.py step set` shall update `state.yaml.current_step`,
  validate the target step, append a structured event, update `events.yaml`, and
  print the next recommended skill.
- FR-002: `validate --planning-package` shall validate complete planning
  artifacts without requiring planning gates to be approved or delegated.
- FR-003: `validate --implementation` shall continue requiring approved or
  delegated planning gates before code work.
- FR-004: `featurectl.py scope-change` shall write `scope-change.md`, update
  `current_step`, mark selected artifacts stale, and record an event.
- FR-005: Docs-consulted validation shall require each relevant section to
  reference at least one existing path and include a non-empty usage statement.
- FR-006: Review docs shall clearly distinguish machine-readable YAML findings
  from Markdown review summaries.
- FR-007: `nfp-08` shall explicitly document subagent availability and fallback
  evidence.
- FR-008: Optional real Codex e2e tests shall be skipped unless
  `RUN_REAL_CODEX_E2E=1` is set.
- FR-009: Skill contract tests shall assert required metadata and operational
  sections for every `nfp-*` skill.
- FR-010: Manual-check preflight shall be executable and documented.

## Non-Functional Requirements

- NFR-001: Default tests must remain deterministic and offline.
- NFR-002: New commands must preserve existing `featurectl.py` command behavior.
- NFR-003: Real Codex e2e tests must store prompt, output, status, validation,
  and git diff evidence.
- NFR-004: Validation errors must name the failing artifact and explain the fix.
- NFR-005: Generated and handwritten docs must stay below current line-length
  guardrails.

## Acceptance Criteria

- AC-001: Step-transition tests cover valid transition, invalid step, execution
  event, and `events.yaml` update.
- AC-002: Planning-package validation passes with drafted planning gates, while
  implementation validation fails until gates are approved or delegated.
- AC-003: Scope-change tests prove stale flags, return step, scope-change file,
  and implementation blocking.
- AC-004: Docs-consulted tests reject marker-only sections and missing paths,
  then pass for existing paths with usage explanations.
- AC-005: Optional real Codex e2e tests are skipped by default and document the
  required `RUN_REAL_CODEX_E2E=1 CODEX_BIN=codex` invocation.
- AC-006: Skill contract tests pass for all `nfp-*` skills.
- AC-007: Manual-check preflight exists and validates status, workspace, worktree
  readiness, planning-package mode, implementation mode, and tests.
- AC-008: Full feature-pipeline tests, public raw checks, compile checks, and
  `git diff --check` pass before promotion.

## Assumptions

- `events.yaml` stays as the official machine event log and will be documented
  rather than removed.
- Real Codex e2e should remain opt-in because it can be slow, costly, or
  unavailable in CI.
- Scope-change support can be implemented as a focused control-plane command
  without changing the whole skill sequence.

## Open Questions

- Should a future CI job run real Codex e2e on a scheduled/manual trigger, or
  should it remain local-only until the harness is more mature?
