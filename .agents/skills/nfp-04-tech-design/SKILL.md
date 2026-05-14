---
name: nfp-04-tech-design
description: Specify implementation contracts, module responsibilities, data, errors, flags, and test strategy.
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 04 Tech Design

Use this skill to create `tech-design.md` and feature contracts.

Methodology:

- Read `.agents/pipeline-core/references/native-skill-protocol.md`.
- Apply `.agents/pipeline-core/references/upstream-pattern-map.md` as the behavioral synthesis of cloned upstream methodologies; cite patterns in `Docs Consulted:` when they influence a decision.
- Apply `.agents/pipeline-core/references/methodology-lenses.md` for
  task-graph metadata, source provenance, design alternatives, and
  completeness/correctness/coherence checks.
- Confirm the current directory is the feature worktree.
- Read `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`,
  `feature.md`, and `architecture.md`.
- Load the tech-design docset with `featurectl.py load-docset --step tech-design`.
- Use `.agents/pipeline-core/references/artifact-model.md` and generated technical design,
  ADR, and contract templates as shape references.
- Record `Docs Consulted: Technical Design` in `execution.md`.

Responsibilities:

- describe implementation modules and responsibilities
- translate architecture change deltas into concrete implementation deltas
- define APIs, schemas, events, internal contracts, data model, error handling,
  security considerations, tests, migration, rollback, and integration notes
- define ownership, dependency, conflict-risk, and test-strategy constraints for
  later slices
- record alternatives rejected when interface, data, migration, or contract
  choices are material
- record docs consulted in `execution.md`

Workflow:

1. Confirm the current directory is the feature worktree.
2. Read `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`,
   `feature.md`, and `architecture.md`.
3. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py load-docset --workspace <workspace> --step tech-design
   ```

4. Draft `tech-design.md` with:

   ```markdown
   # Technical Design: <Title>

   ## Change Delta
   ## Implementation Summary
   ## Modules And Responsibilities
   ## Dependency And Ownership Plan
   ## Contracts
   ## API/Event/Schema Details
   ## Core Code Sketches
   ## Data Model
   ## Error Handling
   ## Security Considerations
   ## Test Strategy
   ## Migration Plan
   ## Rollback Plan
   ## Integration Notes
   ## Decision Traceability
   ```

5. In `Dependency And Ownership Plan`, identify the critical path, parallel
   streams, file ownership, conflict risk, and test ownership expected by
   `nfp-05-slicing`.
6. Add structured contracts under `contracts/` when the design exposes or
   consumes API, event, schema, database, or internal module contracts.
7. Record `Docs Consulted: Technical Design` in `execution.md`.
8. Set the technical design gate to `drafted`.
9. Run `featurectl.py validate --workspace <workspace>`.

Do not create implementation slices or code in this step.

If automatic handoff does not happen, print:

```text
Next skill: nfp-05-slicing.
Continue with that skill.
```

## Skill Contract

Inputs:
- `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`, `feature.md`,
  `architecture.md`, ADRs, contracts, inspected source paths, and test context.

Owned artifacts:
- `tech-design.md`, contracts under `contracts/` when needed, and technical
  design decisions in `execution.md`.

Forbidden actions:
- Do not create slices, implementation code, `approvals.yaml`, or `handoff.md`.
- Do not mutate `state.yaml` manually; use `featurectl.py gate set`.

Validation command:
- `python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace>`

Docs consulted requirement:
- Append `Docs Consulted: Technical Design` to `execution.md` with explicit
  path bullets, `Used for`, and `Confidence` entries.

Next step fallback:
- Print `Next skill: nfp-05-slicing` when automatic handoff does not happen.
