# Feature: Bounded Gate autoresume hints

## Intent
Add bounded gate autoresume hints to show the next safe pipeline action after each gate transition without adding next_skill to state.

## Motivation
Generated artifacts must identify touched modules, state transitions, tests, review focus, rollback guidance, and shared knowledge impact.

## Actors
- Pipeline maintainer
- Nested Codex worker
- Future agent reusing feature memory

## Goals
- `FR-001` Implement the requested behavior in `skills`.
- `FR-002` Preserve evidence, rollback guidance, and review findings.
- `FR-003` Document shared knowledge decisions for future reuse.

## Acceptance Criteria
- `AC-001` Generated artifacts describe changed parts and tests.
- `AC-002` Architecture includes a readable Mermaid topology.
- `AC-003` Feature card includes the shared knowledge decision table.

## Changed Parts
- `nfp skills`
- `state.yaml`
- `execution.md`

## Product Risks
- state contract regression
- skipped gate
