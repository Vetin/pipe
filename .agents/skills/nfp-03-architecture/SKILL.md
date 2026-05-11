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
- Apply `.agents/pipeline-core/references/methodology-lenses.md` for
  brownfield research, elicitation lenses, change-delta thinking, and
  completeness/correctness/coherence checks.
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
- identify new, modified, removed, and unchanged behavior
- describe module communication, security model, failure modes, observability,
  rollback, and architecture risks
- document considered alternatives and why the selected direction fits the
  existing repository
- keep claims grounded in inspected files, ADRs, contracts, and tests
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

   ## Change Delta

   ## System Context

   ## Component Interactions

   ## Diagrams

   ## Security Model

   ## Failure Modes

   ## Observability

   ## Rollback Strategy

   ## Migration Strategy

   ## Architecture Risks

   ## Alternatives Considered

   ## Completeness Correctness Coherence

   ## ADRs
   ```

6. In `Change Delta`, explicitly list new, modified, removed, and unchanged
   behavior. If a category is empty, say so.
7. Add diagrams under `diagrams/` when they clarify flow or module boundaries.
8. Add ADRs under `adrs/` only for significant decisions. Each ADR must include
   alternatives and consequences.
9. Append `Docs Consulted: Architecture` to `execution.md` with short notes on
   how each document was used.
10. Set the architecture gate to `drafted` once the artifact exists.
11. Run:

    ```bash
    python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace>
    ```

Do not write technical design details, implementation slices, or code in this step.

If automatic handoff does not happen, print:

```text
Next skill: nfp-04-tech-design.
Continue with that skill.
```
