---
name: nfp-11-finish
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 11 Finish

Use this skill to prepare feature memory and PR summary.

Methodology:

- Read `.agents/pipeline-core/references/native-skill-protocol.md`.
- Confirm the current directory is the feature worktree.
- Read `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`,
  `feature.md`, `architecture.md`, `tech-design.md`, `slices.yaml`,
  `reviews/*.yaml`, and `evidence/manifest.yaml`.
- Load the finish docset with `featurectl.py load-docset --step finish`.
- Use `methodology/extracted/artifact-model.md`,
  `methodology/extracted/evaluation-patterns.md`, and
  `.agents/pipeline-core/references/generated-templates/feature-card-template.md`.
- Record `Docs Consulted: Finish` in `execution.md`.

Responsibilities:

- validate completed slices, review, and verification evidence
- generate `feature-card.md`
- write PR summary and final execution summary
- update living documentation summaries when appropriate

Workflow:

1. Run `featurectl.py load-docset --workspace <workspace> --step finish`.
2. Append `Docs Consulted: Finish` to `execution.md`.
3. Run `featurectl.py validate --workspace <workspace> --evidence`.
4. Run `featurectl.py validate --workspace <workspace> --review`.
5. Confirm `reviews/verification-review.md` and final verification output exist.
6. Write `feature-card.md` with feature key, intent, requirements, architecture
   summary, contracts, slices, tests, reviews, evidence, and future modification
   notes.
7. Update `execution.md` with final summary and PR summary.
8. Update `.ai/knowledge` summaries when appropriate.
9. Set the finish gate to `complete`.
10. Run `featurectl.py validate --workspace <workspace>`.

Do not promote canonical memory in this step; hand off to `nfp-12-promote`.

Feature memory must include:

- iteration count
- failed attempts and their failure classes
- stale or replanned artifacts
- accepted residual risks
- commands that prove final state
- plan drift notes explaining what changed from `feature.md`,
  `architecture.md`, `tech-design.md`, and `slices.yaml`
