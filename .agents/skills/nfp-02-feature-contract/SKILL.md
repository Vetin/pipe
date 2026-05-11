---
name: nfp-02-feature-contract
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 02 Feature Contract

Use this skill to create `feature.md`.

Responsibilities:

- ask grouped blocking questions when behavior is unsafe or unclear
- draft intent, motivation, actors, goals, non-goals, requirements, acceptance
  criteria, assumptions, related features, and product risks
- update the feature contract gate to `drafted`
- validate the workspace before stopping or handing off

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

- ask grouped blocking questions only
- do not continue on security-critical or business-critical ambiguity
- record non-blocking assumptions explicitly

One-artifact stop behavior:

- create or update `feature.md`
- set `feature_contract` to `drafted` once the draft exists
- keep architecture, technical design, slicing, and implementation untouched
- record the stop point and next step in `execution.md`
- run `featurectl.py validate --workspace <workspace>`
