---
name: nfp-02-feature-contract
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 02 Feature Contract

Use this skill to create `feature.md`.

Methodology:

- Read `.agents/pipeline-core/references/native-skill-protocol.md`.
- Apply `skills/native-feature-pipeline/references/upstream-pattern-map.md` as the behavioral synthesis of cloned upstream methodologies; cite patterns in `Docs Consulted:` when they influence a decision.
- Apply `.agents/pipeline-core/references/methodology-lenses.md` for ambiguity
  taxonomy, clarification limits, elicitation lenses, source-backed claims, and
  adaptive rigor.
- Confirm the current directory is the feature worktree.
- Read `apex.md`, `feature.yaml`, `state.yaml`, and `execution.md`.
- Load the feature-contract docset with
  `featurectl.py load-docset --step feature-contract`.
- Use `skills/native-feature-pipeline/references/artifact-model.md`,
  `.agents/pipeline-core/references/feature-identity-policy.md`, and
  `.agents/pipeline-core/references/generated-templates/feature-template.md`.
- Record `Docs Consulted: Feature Contract` in `execution.md`.

Responsibilities:

- ask grouped blocking questions when behavior is unsafe or unclear
- score ambiguity before drafting and after vague answers
- draft intent, motivation, actors, goals, non-goals, requirements, acceptance
  criteria, assumptions, related features, and product risks
- separate source-backed facts from assumptions and open questions
- document related existing features or explicitly state that no relevant
  existing behavior was found during context discovery
- update the feature contract gate to `drafted`
- validate the workspace before stopping or handing off
  through `featurectl.py validate`

Do not draft architecture or implementation details in this step.

Required `feature.md` sections:

```markdown
# Feature: <Title>

## Intent
## Motivation
## Actors
## Problem
## Goals
## Non-Goals
## Related Existing Features
## Functional Requirements
## Non-Functional Requirements
## Acceptance Criteria
## Product Risks
## Assumptions
## Open Questions
```

Use local IDs such as `FR-001`, `NFR-001`, and `AC-001`. Acceptance criteria
must be testable.

Clarification policy:

- score ambiguity with the taxonomy in `methodology-lenses.md`
- ask at most five high-impact blocking questions before drafting
- ask one question at a time when the answer changes domain model, API,
  permission, destructive behavior, or acceptance criteria
- do not continue on security-critical, data-loss, compliance,
  public-contract, migration, or business-critical ambiguity
- record each unclear item as answered, assumed, deferred, or blocking
- record non-blocking assumptions explicitly
- when direction is genuinely open, present two or three approaches with
  tradeoffs and identify which one the draft assumes

Contract quality gates:

- every functional requirement is measurable and maps to one or more
  acceptance criteria
- every actor with mutation, review, approval, retry, rollback, export, or
  admin capability has an explicit permission rule or open question
- every destructive or irreversible flow has preview, audit, rollback, and
  verification expectations
- every external contract or integration mentions idempotency, replay/stale
  data, authentication, and observable failure behavior when applicable
- product risks include at least one pre-mortem or inversion finding for
  standard and comprehensive rigor
- if no existing feature can be reused, explain which sources were inspected

One-artifact stop behavior:

- create or update `feature.md`
- set `feature_contract` to `drafted` once the draft exists
- keep architecture, technical design, slicing, and implementation untouched
- record the stop point and next step in `execution.md`
- run `featurectl.py validate --workspace <workspace>`

If automatic handoff does not happen, print:

```text
Next skill: nfp-03-architecture.
Continue with that skill.
```
