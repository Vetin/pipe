---
name: nfp-11-finish
description: Prepare feature memory, final feature card, shared knowledge updates, and release summary.
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 11 Finish

Use this skill to prepare feature memory and PR summary.

Methodology:

- Read `.agents/pipeline-core/references/native-skill-protocol.md`.
- Apply `.agents/pipeline-core/references/upstream-pattern-map.md` as the behavioral synthesis of cloned upstream methodologies; cite patterns in `Docs Consulted:` when they influence a decision.
- Apply `.agents/pipeline-core/references/methodology-lenses.md` for claim
  provenance, verification debt, manual validation, plan drift, and promotion
  readiness.
- Confirm the current directory is the feature worktree.
- Read `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`,
  `feature.md`, `architecture.md`, `tech-design.md`, `slices.yaml`,
  `reviews/*.yaml`, and `evidence/manifest.yaml`.
- Load the finish docset with `featurectl.py load-docset --step finish`.
- Use `.agents/pipeline-core/references/artifact-model.md`,
  `.agents/pipeline-core/references/evaluation-patterns.md`, and
  `.agents/pipeline-core/references/generated-templates/feature-card-template.md`.
- Read `.ai/knowledge/features-overview.md`,
  `.ai/knowledge/architecture-overview.md`, `.ai/knowledge/module-map.md`, and
  `.ai/knowledge/integration-map.md` to update or confirm living knowledge
  after the feature is complete.
- Record `Docs Consulted: Finish` in `execution.md`.

Responsibilities:

- validate completed slices, review, and verification evidence
- generate `feature-card.md`
- write PR summary and final execution summary
- update living documentation summaries when appropriate
- capture shared-knowledge updates in `feature-card.md` so future agents can
  see what changed without replaying the full transcript
- include a `Shared Knowledge Decision Table` with `Decision`, `Evidence`, and
  `Future reuse` columns for every updated, confirmed unchanged, or deferred
  `.ai/knowledge` file
- do not claim completion without fresh final verification after the last
  implementation or review fix

Workflow:

1. Run `featurectl.py load-docset --workspace <workspace> --step finish`.
2. Append `Docs Consulted: Finish` to `execution.md`.
3. Run `featurectl.py validate --workspace <workspace> --evidence`.
4. Run `featurectl.py validate --workspace <workspace> --review`.
5. Confirm `reviews/verification-review.md` and final verification output exist
   and include manual validation and verification debt state.
6. Write `feature-card.md` with feature key, intent, requirements, architecture
   summary, contracts, slices, tests, reviews, evidence, and future modification
   notes. Include `## Manual Validation`, `## Verification Debt`,
   `## Claim Provenance`, `## Rollback Guidance`, and
   `## Shared Knowledge Updates`.
7. Update `execution.md` with final summary and PR summary.
8. Update `.ai/knowledge` summaries when appropriate. At minimum, record in
   `feature-card.md` a `Shared Knowledge Decision Table` showing whether
   `.ai/knowledge/features-overview.md`,
   `.ai/knowledge/architecture-overview.md`, `.ai/knowledge/module-map.md`, and
   `.ai/knowledge/integration-map.md` were updated, confirmed unchanged, or
   deferred. Each row must include the `Decision`, `Evidence`, and
   `Future reuse` value.
9. Set the finish gate to `complete`.
10. Run `featurectl.py validate --workspace <workspace>`.

Do not promote canonical memory in this step; hand off to `nfp-12-promote`.

Feature memory must include:

- iteration count
- failed attempts and their failure classes
- stale or replanned artifacts
- accepted residual risks
- verification debt and owner/follow-up, or explicit "none"
- manual/UAT validation result, or explicit "not applicable"
- claim provenance mapping final claims to artifacts and commands
- rollback guidance for operators or future agents
- shared knowledge updates with `.ai/knowledge` paths and reuse notes
- shared knowledge decision table with update/unchanged/deferred status,
  evidence, and future reuse notes
- commands that prove final state
- plan drift notes explaining what changed from `feature.md`,
  `architecture.md`, `tech-design.md`, and `slices.yaml`
