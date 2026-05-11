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
- Start native runs from user intent. The user should be able to ask for a
  feature in plain language; the repository context should trigger intake,
  context loading, contract drafting, design, slicing, implementation, review,
  verification, and promotion without requiring the user to name internal
  `nfp-*` steps.
- Use methodology references as behavior patterns: clarify before planning,
  write testable contracts, design from repo context, slice by dependency,
  execute red/green loops, review adversarially, then promote only verified
  memory.

## What To Reject

- A single monolithic skill that mixes product, design, code, review, and
  promotion.
- Script-generated product or architecture prose.
- Hidden approvals, duplicated handoff files, or state stored only in chat.
- Unbounded implementation before readiness, worktree, and evidence checks pass.
- Reproducible tests that succeed because the prompt enumerates each internal
  skill by name. That tests obedience, not whether the native pipeline is
  discoverable or production-like.

## Native Artifact Influence

Influences `apex.md`, `feature.md`, `architecture.md`, `tech-design.md`,
`slices.yaml`, `execution.md`, `reviews/`, `evidence/`, `feature-card.md`, and
`.ai/features/index.yaml`.

Artifacts must form a trace graph:

- requirements and risks in `feature.md`;
- decisions and module boundaries in `architecture.md`;
- interfaces, migrations, contracts, flags, and failure handling in
  `tech-design.md`;
- dependency-aware execution in `slices.yaml`;
- red/green evidence and review outcomes in `execution.md`, `evidence/`, and
  `reviews/`;
- promotion memory in `feature-card.md`.

## Native Skill Influence

All `nfp-*` skills must follow shared protocol, load a step docset, record docs
consulted, write only owned artifacts, and hand off explicitly.

They must also preserve native behavior: the skill can be invoked by the
runtime, but showcase prompts should ask for the feature outcome and let the
pipeline docs guide the agent.

## Validation Rule Implied

`featurectl.py validate` must reject forbidden files, stale downstream artifacts,
missing gates, invalid evidence order, and critical blocking review findings.
Native showcase validation must also reject prompts that directly enumerate
`nfp-00` through `nfp-12` as the control path.
