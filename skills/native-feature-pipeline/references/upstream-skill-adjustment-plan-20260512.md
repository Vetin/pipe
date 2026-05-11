# Upstream Skill Adjustment Plan 2026-05-12

This plan maps the local methodology upstreams in
`methodology/UPSTREAM_LOCK.md` to concrete Native Feature Pipeline changes.
It is intentionally implementation-facing: each borrowed practice must become
skill text, a shared reference, validation logic, or showcase judge evidence.

## Upstreams Reviewed

| Upstream | Practices to reuse in NFP |
| --- | --- |
| BMAD | Progressive context phases, established-project discovery, named elicitation lenses, adversarial review that actively seeks defects. |
| Spec Kit | Spec as source of truth, ambiguity taxonomy, max-five high-impact clarifications, cross-artifact analyze gate, story/task traceability. |
| OpenSpec | Brownfield delta model, actions over rigid phases, SHALL/MUST scenario style, completeness/correctness/coherence verification. |
| Superpowers | Brainstorm alternatives before creative choices, strict red/green TDD discipline, evidence before completion claims, tiny executable plans. |
| AI-DLC workflows | Adaptive rigor levels, brownfield reverse engineering, overconfidence checks, unit-of-work dependency planning. |
| specs.md | Inception/construction/operations split, project-type-aware decomposition, baseline-vs-after behavior evaluation, LLM-judge style quality pyramid. |
| Shotgun | Research-first planning, existing-solution reuse checks, observability for pipeline runs, hard/soft evaluator failures. |
| get-shit-done | Ambiguity score gate, Socratic but bounded interviews, UAT state, claim provenance, verification debt. |
| CCPM | PRD/epic/task graph discipline, exact file ownership, parallel stream/conflict-risk analysis, script-first status reporting. |
| Claude Task Master | Complexity scores, dependency validation, critical path and bottleneck detection, task update rules when implementation drifts. |
| Roo Code | Agent-loop state model, isolated eval runs, task metrics, timeout/health monitoring, intent-based conflict resolution. |

## Change Batches

### Batch 1: Intake, Init, Context, Feature Contract

Update `project-init`, `nfp-00-intake`, `nfp-01-context`, and
`nfp-02-feature-contract` to enforce:

- adaptive rigor levels: minimal, standard, comprehensive;
- repository-first discovery before feature claims;
- current feature picture, module map, and existing-solution/reuse map;
- ambiguity taxonomy and ambiguity score with a hard stop on unresolved
  business, security, destructive, or data-model uncertainty;
- max-five blocking clarification budget, recorded as answered, assumed, or
  deferred;
- 2-3 approach options when design direction is material and unclear;
- source-backed claim provenance in `execution.md`.

Validation after this batch:

- run native feature emulation for the best three `features.md` showcases;
- run a methodology judge comparing current output with the committed baseline;
- run the unit tests that cover native emulation and project init.

### Batch 2: Architecture, Technical Design, Slicing, Readiness

Update `nfp-03-architecture`, `nfp-04-tech-design`, `nfp-05-slicing`, and
`nfp-06-readiness` to enforce:

- change delta inventory: new, modified, removed behavior;
- explicit decisions, alternatives, tradeoffs, risks, migration, and rollback;
- module communication grounded in inspected files rather than summaries;
- story-to-slice traceability with requirement, acceptance, ADR, contract, and
  test links;
- task metadata: priority, complexity, dependency chain, critical path,
  parallelization marker, file ownership, conflict risk, and test strategy;
- readiness analyze gate for duplicate, ambiguous, underspecified,
  inconsistent, uncovered, and constitution-risk findings;
- completeness/correctness/coherence gate before implementation.

Validation after this batch:

- rerun native feature emulation and judge side by side against baseline and
  batch 1;
- run slice/readiness tests;
- confirm validator rejects missing new slice metadata.

### Batch 3: TDD, Review, Verification, Finish, Promote

Update `nfp-08-tdd-implementation`, `nfp-09-review`,
`nfp-10-verification`, `nfp-11-finish`, and `nfp-12-promote` to enforce:

- no production code without a focused failing test first;
- wrong-failure triage before green implementation;
- future slice/task updates when implementation changes scope;
- adversarial review with hard/soft findings, mandatory issue search, and
  evidence-backed zero-finding justification;
- UAT/manual validation state for user-visible workflows;
- verification debt and claim provenance before finish;
- promotion only after fresh final verification and resolved or explicitly
  accepted blocking findings;
- isolated evaluation/run metadata inspired by Roo: run id, timeout, status,
  health, metrics, and artifact paths.

Validation after this batch:

- rerun native feature emulation and judge across all batches;
- run full `tests/feature_pipeline` suite;
- run goal validation for plan/vision conformance;
- commit final judge reports and validation artifacts.

## Reusable Assets To Add

- `.agents/pipeline-core/references/methodology-lenses.md`: compact shared
  reference for adaptive rigor, ambiguity taxonomy, elicitation lenses,
  research-first behavior, task graph metadata, TDD law, adversarial review,
  verification debt, and eval metrics.
- `pipeline-lab/showcases/scripts/judge_native_feature_builds.py`: deterministic
  LLM-judge-style evaluator that scores native emulation outputs and active
  skill coverage across methodology dimensions. It should be replaceable by a
  real LLM judge when credentials are configured.
- Unit tests for the judge and new validation surfaces.

## Commit Strategy

1. Commit this plan as its own methodology adjustment record.
2. For each batch, modify only the owned skill/reference/script/test files.
3. After every batch, run e2e emulation, judge comparison, and targeted tests.
4. Commit each batch with its validation report.
5. Finish with a full validation commit only after plan and vision checks pass.
