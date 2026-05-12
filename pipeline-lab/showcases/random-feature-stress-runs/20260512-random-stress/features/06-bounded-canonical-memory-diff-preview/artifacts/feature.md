# Feature: Bounded Canonical memory diff preview

## Intent
Add bounded canonical memory diff preview to preview canonical feature memory changes before promote copies a workspace into .ai/features.

## Motivation
Generated artifacts must identify touched modules, state transitions, tests, review focus, rollback guidance, and shared knowledge impact.

## Actors
- Pipeline maintainer
- Nested Codex worker
- Future agent reusing feature memory

## Goals
- `FR-001` Implement the requested behavior in `promotion`.
- `FR-002` Preserve evidence, rollback guidance, and review findings.
- `FR-003` Document shared knowledge decisions for future reuse.

## Acceptance Criteria
- `AC-001` Generated artifacts describe changed parts and tests.
- `AC-002` Architecture includes a readable Mermaid topology.
- `AC-003` Feature card includes the shared knowledge decision table.

## Changed Parts
- `feature-card.md`
- `.ai/features-archive`
- `.ai/features`

## Product Risks
- memory overwrite
- lost archived variant
