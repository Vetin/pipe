# Feature: Guided Shared knowledge coverage gate

## Intent
Add guided shared knowledge coverage gate to fail validation when architecture or feature cards omit knowledge update decisions.

## Motivation
Generated artifacts must identify touched modules, state transitions, tests, review focus, rollback guidance, and shared knowledge impact.

## Actors
- Pipeline maintainer
- Nested Codex worker
- Future agent reusing feature memory

## Goals
- `FR-001` Implement the requested behavior in `validators`.
- `FR-002` Preserve evidence, rollback guidance, and review findings.
- `FR-003` Document shared knowledge decisions for future reuse.

## Acceptance Criteria
- `AC-001` Generated artifacts describe changed parts and tests.
- `AC-002` Architecture includes a readable Mermaid topology.
- `AC-003` Feature card includes the shared knowledge decision table.

## Changed Parts
- `validate_pipeline_goals.py`
- `architecture.md`
- `feature-card.md`

## Product Risks
- generic knowledge bullets
- future agent confusion
