# Feature: Auditable Feature signal confidence normalizer

## Intent
Add auditable feature signal confidence normalizer to deduplicate noisy feature signals and explain confidence across docs and source files.

## Motivation
Generated artifacts must identify touched modules, state transitions, tests, review focus, rollback guidance, and shared knowledge impact.

## Actors
- Pipeline maintainer
- Nested Codex worker
- Future agent reusing feature memory

## Goals
- `FR-001` Implement the requested behavior in `project-init`.
- `FR-002` Preserve evidence, rollback guidance, and review findings.
- `FR-003` Document shared knowledge decisions for future reuse.

## Acceptance Criteria
- `AC-001` Generated artifacts describe changed parts and tests.
- `AC-002` Architecture includes a readable Mermaid topology.
- `AC-003` Feature card includes the shared knowledge decision table.

## Changed Parts
- `profile scanner`
- `features-overview.md`
- `.ai/knowledge/project-index.yaml`

## Product Risks
- overstated feature memory
- duplicate catalog rows
