# Upstream Pattern Map

This document maps the cloned methodology references in
`methodology/UPSTREAM_LOCK.md` to concrete Native Feature Pipeline behavior.
It is synthesis only; do not copy upstream prose into generated feature
artifacts.

## What To Borrow

- From BMAD-style flows: split product, architecture, implementation, and QA
  into distinct roles and gates; use adversarial review before promotion.
- From Spec Kit style flows: make the feature contract the source of truth,
  clarify ambiguity before planning, and trace every task back to requirements.
- From OpenSpec style flows: treat each feature as a change set with explicit
  contracts, validation, and promotion boundaries.
- From Superpowers style flows: keep skills focused, run small red/green loops,
  and request reviews with context packets rather than chat history.
- From AI-DLC/specs.md/aidlc-workflows: decompose intent into bounded units,
  separate domain design from logical design, and preserve human checkpoints at
  destructive or business-critical decisions.
- From task graph systems such as Task Master and CCPM: model slices with
  dependencies, complexity, status, and update rules when scope changes.
- From get-shit-done style flows: score ambiguity, interview only on blocking
  gaps, and require pass/fail acceptance criteria.
- From Roo/agent packaging: keep native skills discoverable by user intent and
  tool context instead of depending on a user to name every internal step.

## What To Reject

- Directly pasting upstream methodology text into NFP skills or artifacts.
- Prompting reproducible tests to invoke each internal skill by name; native
  emulation must start from a normal feature request and let repository context
  trigger the pipeline.
- Treating generated plans as approval to perform irreversible data changes.
- Flattening the feature into one generic checklist that hides architecture,
  contracts, slice dependencies, review findings, or evidence.
- Running implementation before ambiguity, contract, architecture, design, and
  readiness gates are recorded.

## Native Artifact Influence

- `feature.md` must include measurable intent, non-goals, risks, assumptions,
  functional requirements, non-functional requirements, and pass/fail
  acceptance criteria.
- `architecture.md` must show repo-specific context, module communication,
  security, observability, failure modes, rollback, and ADR links.
- `tech-design.md` must convert architecture into interfaces, data shapes,
  migrations, contracts, flags, error handling, and test surfaces.
- `slices.yaml` must act like a dependency-aware task graph: each slice owns
  requirements, files, tests, red/green evidence, and rollback notes.
- `execution.md` is the durable run log: docs consulted, gates, decisions,
  scope changes, evidence, review, and handoff state.
- `reviews/`, `evidence/`, and `feature-card.md` provide the adversarial QA,
  verification, and promotion memory expected by production-grade delivery.

## Native Skill Influence

- `nfp-00-intake` and `nfp-01-context` must behave like intent clarification
  and established-project discovery, not code generation.
- `nfp-02-feature-contract` must include ambiguity scoring and stop on
  unresolved business/security risk.
- `nfp-03-architecture` and `nfp-04-tech-design` must separate domain design
  from logical implementation details and create ADRs for significant choices.
- `nfp-05-slicing` must produce dependency-aware slices that can be executed,
  reviewed, and resumed independently.
- `nfp-08-tdd-implementation` must keep red/green/refactor evidence and update
  downstream tasks if implementation changes the plan.
- `nfp-09-review` through `nfp-12-promote` must perform adversarial review,
  verification, finish summaries, and promotion only after blocking findings
  are resolved or explicitly recorded.

## Validation Rule Implied

Native emulation and real runs must prove that:

- the outer prompt contains a normal feature request, not a list of internal
  `nfp-*` skill invocations;
- all required artifacts exist and cross-reference requirements, slices,
  tests, risks, decisions, and evidence;
- destructive or irreversible actions have non-delegable gates;
- red evidence precedes green evidence for implemented slices;
- review findings are traceable and cannot be bypassed silently;
- final promotion records source revision, artifact paths, verification
  commands, known limitations, and rollback guidance.
