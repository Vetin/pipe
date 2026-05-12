# Feature: Random Feature Stress Lab

## Intent

Add a deterministic stress lab that generates ten varied feature requests for
the harness repository, rebuilds and scores them across at least ten repeated
iterations, and compares how shared knowledge and feature memory are documented.

## Motivation

The pipeline already validates curated showcase cases, but it does not exercise
randomized daily-use feature shapes inside this repository. We need a reusable
way to detect recurring artifact mistakes, especially generic shared-knowledge
updates that do not say what changed, what stayed unchanged, and how a future
agent should reuse the result.

## Actors

- Pipeline maintainer validating skill quality.
- Nested Codex or local runner simulating real feature-building work.
- Future agent reading `.ai/knowledge` and promoted feature cards.

## Goals

- FR-001: Generate ten deterministic random feature requests across different
  harness modules, complexity levels, changed surfaces, and risk profiles.
- FR-002: Rebuild and score all ten generated features for at least ten
  iterations while preserving side-by-side comparison artifacts.
- FR-003: Validate feature artifacts, architecture topology, feature cards,
  shared-knowledge documentation, rollback notes, and common-mistake patterns.
- FR-004: Apply any discovered pipeline skill improvement and prove the final
  run has no open improvement recommendations.

## Non-Goals

- Do not mutate external showcase repositories in this lab run.
- Do not invoke a remote LLM judge; keep local validation deterministic.
- Do not replace the existing real-repository Codex E2E runner.

## Functional Requirements

- FR-001: The runner creates a stable list of ten feature requests from a seed.
- FR-002: The runner executes at least ten evaluation iterations and records
  100 feature-run scorecards for ten features.
- FR-003: Each generated feature includes feature contract, repository context,
  architecture, technical design, slices, feature card, evidence, and review
  artifacts.
- FR-004: Each architecture and feature card includes a shared-knowledge
  decision table covering `.ai/knowledge/features-overview.md`,
  `.ai/knowledge/architecture-overview.md`, `.ai/knowledge/module-map.md`, and
  `.ai/knowledge/integration-map.md`.
- FR-005: The run produces a side-by-side report, improvement plan, rollback
  plan, and machine-readable summary.
- FR-006: The final summary reports zero open improvements after the applied
  skill/template changes.

## Non-Functional Requirements

- NFR-001: Output must be deterministic for the same seed.
- NFR-002: The lab must not require network access or production dependencies.
- NFR-003: Validation should fail fast when iterations are fewer than ten or
  feature count is fewer than ten.
- NFR-004: Generated reports must be small enough to commit and review.

## Acceptance Criteria

- AC-001: Given a fixed seed, when the stress runner runs with ten features and
  ten iterations, then it writes a feature list, 100 scorecards, final artifacts,
  side-by-side comparison, improvement plan, rollback plan, and summary.
- AC-002: Given generated artifacts, when validation runs, then every feature
  has a Mermaid topology and shared-knowledge decision table in architecture and
  feature-card outputs.
- AC-003: Given the common mistake pattern from early review, when skills are
  inspected, then architecture and finish instructions require decision/status,
  evidence, and future-reuse fields for shared knowledge.
- AC-004: Given the final stress run, when tests inspect the summary, then
  `open_improvements` is empty and all ten iterations pass.

## Assumptions

- The stress lab is scoped to `harness-pipeline` modules and does not need to
  edit cloned OSS repositories.
- Existing native emulation and Codex E2E runners remain the source of real
  repository integration testing.

## Open Questions

- None blocking. A future extension can add a mode that drives the ten cloned
  showcase repositories with local Codex CLI sessions.
