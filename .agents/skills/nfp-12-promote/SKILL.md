---
name: nfp-12-promote
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 12 Promote

Use this skill to promote a completed workspace into canonical feature memory.

Methodology:

- Read `.agents/pipeline-core/references/native-skill-protocol.md`.
- Apply `methodology/extracted/upstream-pattern-map.md` as the behavioral synthesis of cloned upstream methodologies; cite patterns in `Docs Consulted:` when they influence a decision.
- Apply `.agents/pipeline-core/references/methodology-lenses.md` for fresh
  verification, promotion memory, source revision, and conflict safety.
- Confirm the current directory is the feature worktree.
- Read `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`, and
  `feature-card.md`.
- Load the promote docset with `featurectl.py load-docset --step promote`.
- Use `methodology/extracted/artifact-model.md`,
  `.agents/pipeline-core/references/context-reuse-policy.md`, and
  `.agents/pipeline-core/references/feature-identity-policy.md`.
- Record `Docs Consulted: Promote` in `execution.md`.

Responsibilities:

- validate finish state
- check canonical path conflicts
- confirm final verification was recorded after the last implementation/review
  change
- confirm promoted memory includes verification debt, manual validation, claim
  provenance, source revision, and rollback guidance
- promote the workspace to `.ai/features/<domain>/<slug>/`
- regenerate `.ai/features/index.yaml`
- archive conflicting variants only when explicitly requested

Workflow:

1. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py load-docset --workspace <workspace> --step promote
   ```

2. Append `Docs Consulted: Promote` to `execution.md`.
3. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace>
   ```

4. Recheck `feature-card.md`, `reviews/verification-review.md`,
   `evidence/final-verification-output.log`, and `evidence/manifest.yaml` for
   source revision, verification debt, manual validation, claim provenance, and
   rollback guidance.
5. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py promote --workspace <workspace> --conflict abort
   ```

6. If a canonical feature already exists, stop by default.
7. Use `--conflict archive-as-variant` only when the user explicitly approves
   archiving the existing canonical feature as a variant.
8. Confirm `.ai/features/index.yaml` contains the promoted feature key.

Do not implement merge or replace conflict behavior in v1.
