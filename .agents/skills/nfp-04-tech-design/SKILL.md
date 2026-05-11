---
name: nfp-04-tech-design
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 04 Tech Design

Use this skill to create `tech-design.md` and feature contracts.

Methodology:

- Read `.agents/pipeline-core/references/native-skill-protocol.md`.
- Apply `methodology/extracted/upstream-pattern-map.md` as the behavioral synthesis of cloned upstream methodologies; cite patterns in `Docs Consulted:` when they influence a decision.
- Confirm the current directory is the feature worktree.
- Read `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`,
  `feature.md`, and `architecture.md`.
- Load the tech-design docset with `featurectl.py load-docset --step tech-design`.
- Use `methodology/extracted/artifact-model.md` and generated technical design,
  ADR, and contract templates as shape references.
- Record `Docs Consulted: Technical Design` in `execution.md`.

Responsibilities:

- describe implementation modules and responsibilities
- define APIs, schemas, events, internal contracts, data model, error handling,
  security considerations, tests, migration, rollback, and integration notes
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

   ## Implementation Summary
   ## Modules And Responsibilities
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
   ```

5. Add structured contracts under `contracts/` when the design exposes or
   consumes API, event, schema, database, or internal module contracts.
6. Record `Docs Consulted: Technical Design` in `execution.md`.
7. Set the technical design gate to `drafted`.
8. Run `featurectl.py validate --workspace <workspace>`.

Do not create implementation slices or code in this step.

If automatic handoff does not happen, print:

```text
Next skill: nfp-05-slicing.
Continue with that skill.
```
