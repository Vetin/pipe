# Feature: Traceable Evidence timeline export

## Intent
Add traceable evidence timeline export to render red, green, review, fix, and verification evidence into a chronological report.

## Motivation
Generated artifacts must identify touched modules, state transitions, tests, review focus, rollback guidance, and shared knowledge impact.

## Actors
- Pipeline maintainer
- Nested Codex worker
- Future agent reusing feature memory

## Goals
- `FR-001` Implement the requested behavior in `evidence`.
- `FR-002` Preserve evidence, rollback guidance, and review findings.
- `FR-003` Document shared knowledge decisions for future reuse.

## Acceptance Criteria
- `AC-001` Generated artifacts describe changed parts and tests.
- `AC-002` Architecture includes a readable Mermaid topology.
- `AC-003` Feature card includes the shared knowledge decision table.

## Changed Parts
- `execution.md`
- `reviews/`
- `evidence/manifest.yaml`

## Product Risks
- missing failed attempt
- unlinked command output
