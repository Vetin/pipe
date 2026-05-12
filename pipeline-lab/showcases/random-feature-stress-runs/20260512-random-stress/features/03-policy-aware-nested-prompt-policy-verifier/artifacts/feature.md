# Feature: Policy-Aware Nested prompt policy verifier

## Intent
Add policy-aware nested prompt policy verifier to verify nested Codex prompts discover AGENTS.md and avoid direct internal skill invocation lists.

## Motivation
Generated artifacts must identify touched modules, state transitions, tests, review focus, rollback guidance, and shared knowledge impact.

## Actors
- Pipeline maintainer
- Nested Codex worker
- Future agent reusing feature memory

## Goals
- `FR-001` Implement the requested behavior in `codex-e2e`.
- `FR-002` Preserve evidence, rollback guidance, and review findings.
- `FR-003` Document shared knowledge decisions for future reuse.

## Acceptance Criteria
- `AC-001` Generated artifacts describe changed parts and tests.
- `AC-002` Architecture includes a readable Mermaid topology.
- `AC-003` Feature card includes the shared knowledge decision table.

## Changed Parts
- `prompt.md`
- `run_codex_e2e_case.py`
- `codex-output.log`

## Product Risks
- policy bypass
- chat-only state
- missing worktree policy
