# Feature: Guided Scenario score drift detector

## Intent
Add guided scenario score drift detector to compare repeated benchmark runs and flag score drift by skill and scenario.

## Motivation
Generated artifacts must identify touched modules, state transitions, tests, review focus, rollback guidance, and shared knowledge impact.

## Actors
- Pipeline maintainer
- Nested Codex worker
- Future agent reusing feature memory

## Goals
- `FR-001` Implement the requested behavior in `pipelinebench`.
- `FR-002` Preserve evidence, rollback guidance, and review findings.
- `FR-003` Document shared knowledge decisions for future reuse.

## Acceptance Criteria
- `AC-001` Generated artifacts describe changed parts and tests.
- `AC-002` Architecture includes a readable Mermaid topology.
- `AC-003` Feature card includes the shared knowledge decision table.

## Changed Parts
- `scorecards`
- `showcase-summary.yaml`
- `showcase-report.md`

## Product Risks
- false positive drift
- unstable baselines
