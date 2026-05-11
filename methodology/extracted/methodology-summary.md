# Methodology Summary

## What To Borrow

- Treat feature delivery as a sequence of gates, not one free-form prompt.
- Keep product intent, architecture, contracts, slices, evidence, review, and
  feature memory as separate artifacts.
- Make every artifact traceable to requirements, acceptance criteria, decisions,
  tests, and evidence.
- Use focused skills with small responsibilities and shared deterministic
  helpers.
- Preserve a durable execution log so another agent can resume without chat
  history.

## What To Reject

- A single monolithic skill that mixes product, design, code, review, and
  promotion.
- Script-generated product or architecture prose.
- Hidden approvals, duplicated handoff files, or state stored only in chat.
- Unbounded implementation before readiness, worktree, and evidence checks pass.

## Native Artifact Influence

Influences `apex.md`, `feature.md`, `architecture.md`, `tech-design.md`,
`slices.yaml`, `execution.md`, `reviews/`, `evidence/`, `feature-card.md`, and
`.ai/features/index.yaml`.

## Native Skill Influence

All `nfp-*` skills must follow shared protocol, load a step docset, record docs
consulted, write only owned artifacts, and hand off explicitly.

## Validation Rule Implied

`featurectl.py validate` must reject forbidden files, stale downstream artifacts,
missing gates, invalid evidence order, and critical blocking review findings.
