---
name: nfp-03-architecture
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 03 Architecture

Use this skill to create `architecture.md`, significant ADRs, and diagrams.

Methodology:

- Read `.agents/pipeline-core/references/native-skill-protocol.md`.
- Apply `methodology/extracted/upstream-pattern-map.md` as the behavioral synthesis of cloned upstream methodologies; cite patterns in `Docs Consulted:` when they influence a decision.
- Confirm the current directory is the feature worktree.
- Read `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`, and
  `feature.md`.
- Load the architecture docset with `featurectl.py load-docset --step architecture`.
- Use `methodology/extracted/artifact-model.md`,
  `methodology/extracted/context-and-doc-loading.md`, and
  `.agents/pipeline-core/references/generated-templates/architecture-template.md`.
- Write architecture from inspected repository context, not generic invention.
- Record `Docs Consulted: Architecture` in `execution.md`.

Responsibilities:

- load the architecture docset
- read feature and context findings
- describe module communication, security model, failure modes, observability,
  rollback, and architecture risks
- create ADRs only for significant decisions
- record docs consulted in `execution.md`

Workflow:

1. Confirm the current directory is the feature worktree.
2. Read `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`, and
   `feature.md`.
3. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py load-docset --workspace <workspace> --step architecture
   ```

4. Read required docs first and relevant optional docs within budget.
5. Draft `architecture.md` with these sections:

   ```markdown
   # Architecture: <Title>

   ## System Context

   ## Component Interactions

   ## Diagrams

   ## Security Model

   ## Failure Modes

   ## Observability

   ## Rollback Strategy

   ## Architecture Risks

   ## ADRs
   ```

6. Add diagrams under `diagrams/` when they clarify flow or module boundaries.
7. Add ADRs under `adrs/` only for significant decisions.
8. Append `Docs Consulted: Architecture` to `execution.md` with short notes on
   how each document was used.
9. Set the architecture gate to `drafted` once the artifact exists.
10. Run:

    ```bash
    python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace>
    ```

Do not write technical design details, implementation slices, or code in this step.

If automatic handoff does not happen, print:

```text
Next skill: nfp-04-tech-design.
Continue with that skill.
```
