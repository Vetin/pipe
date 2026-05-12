# Feature: Auditable Mermaid topology coverage report

## Intent
Add auditable mermaid topology coverage report to audit generated architecture files for topology actors, services, persistence, and communication arrows.

## Motivation
Generated artifacts must identify touched modules, state transitions, tests, review focus, rollback guidance, and shared knowledge impact.

## Actors
- Pipeline maintainer
- Nested Codex worker
- Future agent reusing feature memory

## Goals
- `FR-001` Implement the requested behavior in `architecture`.
- `FR-002` Preserve evidence, rollback guidance, and review findings.
- `FR-003` Document shared knowledge decisions for future reuse.

## Acceptance Criteria
- `AC-001` Generated artifacts describe changed parts and tests.
- `AC-002` Architecture includes a readable Mermaid topology.
- `AC-003` Feature card includes the shared knowledge decision table.

## Changed Parts
- `validation reports`
- `architecture.md`
- `diagrams/`

## Product Risks
- blank diagram
- generic service boxes
