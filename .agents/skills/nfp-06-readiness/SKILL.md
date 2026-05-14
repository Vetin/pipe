---
name: nfp-06-readiness
description: Validate gates, risks, dependencies, and artifact readiness before implementation starts.
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 06 Readiness

Use this skill to validate planning readiness before implementation.

Methodology:

- Read `.agents/pipeline-core/references/native-skill-protocol.md`.
- Apply `.agents/pipeline-core/references/upstream-pattern-map.md` as the behavioral synthesis of cloned upstream methodologies; cite patterns in `Docs Consulted:` when they influence a decision.
- Apply `.agents/pipeline-core/references/methodology-lenses.md` for
  cross-artifact analysis, task graph integrity, and
  completeness/correctness/coherence checks.
- Confirm the current directory is the feature worktree.
- Read `apex.md`, `feature.yaml`, `state.yaml`, and `execution.md`.
- Load the readiness docset with `featurectl.py load-docset --step readiness`.
- Use `.agents/pipeline-core/references/workflow-and-gates.md` and
  `.agents/pipeline-core/references/gate-policy.md`.
- Record `Docs Consulted: Readiness` in `execution.md`.

Responsibilities:

- run `featurectl.py validate --planning-package` for planning-stop workflows
- run `featurectl.py validate --readiness` and
  `featurectl.py validate --implementation` before implementation starts
- analyze the planning package for duplicate, ambiguous, underspecified,
  inconsistent, uncovered, and constitution-risk findings
- validate slice dependencies, complexity, critical path, file ownership,
  parallelization, and conflict-risk notes
- summarize blockers, assumptions, stale artifacts, and missing gates
- ask for implementation approval or stop at the requested point

Keep readiness logic in deterministic validation where practical.

Workflow:

1. Confirm the current directory is the feature worktree.
2. Read `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`, `feature.md`,
   `architecture.md`, `tech-design.md`, and `slices.yaml`.
3. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py load-docset --workspace <workspace> --step readiness
   ```

4. Append `Docs Consulted: Readiness` to `execution.md`.
5. Perform a read-only analyze pass across `feature.md`, `architecture.md`,
   `tech-design.md`, and `slices.yaml`:
   - duplicate or conflicting requirements
   - ambiguous actors, states, permissions, data ownership, or completion
     signals
   - requirements without architecture/design/slice/test coverage
   - architecture decisions without technical design impact
   - slice dependencies with cycles, bottlenecks, or missing owners
   - unmitigated destructive, security, public-contract, migration, or data
     loss risks
6. For planning-stop workflows, run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace> --planning-package
   ```

   This validates artifact completeness and Docs Consulted proof without
   requiring approval gates.
7. For implementation-start workflows, run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace> --readiness
   python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace> --implementation
   ```

8. If validation fails, summarize blockers and stop.
9. If validation passes, summarize assumptions, residual risks, critical path,
   parallelization opportunities, and conflict-risk controls, then ask for implementation
   approval unless the user already explicitly delegated that gate.

Implementation may start only when `feature_contract`, `architecture`,
`tech_design`, and `slicing_readiness` are approved or delegated.

If approved or delegated, print:

```text
Next skill: nfp-07-worktree.
Continue with that skill.
```

## Skill Contract

Inputs:
- `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`, `feature.md`,
  `architecture.md`, `tech-design.md`, `slices.yaml`, gates, and stale flags.

Owned artifacts:
- Readiness findings and approval/delegation notes in `execution.md`.

Forbidden actions:
- Do not approve gates silently, implement code, create `approvals.yaml` or
  `handoff.md`, or mutate `state.yaml` manually.

Validation command:
- Planning-stop: `python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace> --planning-package`
- Implementation-start: `python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace> --implementation`

Docs consulted requirement:
- Append `Docs Consulted: Readiness` to `execution.md` with explicit path
  bullets, `Used for`, and `Confidence` entries.

Next step fallback:
- Print `Next skill: nfp-07-worktree` when automatic handoff does not happen.
