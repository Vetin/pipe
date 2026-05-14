---
name: nfp-05-slicing
description: Split approved planning into dependency-aware implementation slices with evidence requirements.
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 05 Slicing

Use this skill to create `slices.yaml`.

Methodology:

- Read `.agents/pipeline-core/references/native-skill-protocol.md`.
- Apply `.agents/pipeline-core/references/upstream-pattern-map.md` as the behavioral synthesis of cloned upstream methodologies; cite patterns in `Docs Consulted:` when they influence a decision.
- Apply `.agents/pipeline-core/references/methodology-lenses.md` for task graph
  metadata, complexity scoring, critical path, parallelization, ownership,
  conflict risk, and TDD readiness.
- Confirm the current directory is the feature worktree.
- Read `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`,
  `feature.md`, `architecture.md`, and `tech-design.md`.
- Load the slicing docset with `featurectl.py load-docset --step slicing`.
- Use `.agents/pipeline-core/references/workflow-and-gates.md` and
  `.agents/pipeline-core/references/generated-templates/slice-template.yaml`.
- Record `Docs Consulted: Slicing` in `execution.md`.

Responsibilities:

- create TDD slices linked to requirements and acceptance criteria
- include expected touchpoints, red command, expected failure, green command,
  verification commands, review focus, evidence status, and status
- include complexity, critical path, parallelizable marker, file ownership,
  conflict risk, dependency notes, and test strategy for every slice
- identify parallel execution streams and bottlenecks before implementation
- avoid hard allowed-file or forbidden-file enforcement in v1

Workflow:

1. Confirm the current directory is the feature worktree.
2. Read `feature.md`, `architecture.md`, `tech-design.md`, `state.yaml`, and
   `execution.md`.
3. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py load-docset --workspace <workspace> --step slicing
   ```

4. Create `slices.yaml` with `artifact_contract_version`, `feature_key`, and a
   `slices` list.
5. For each slice include `id`, `title`, linked requirements, linked acceptance
   criteria, dependencies, priority, expected touchpoints, scope confidence,
   `tdd.failing_test_file`, `tdd.red_command`, `tdd.expected_failure`,
   `tdd.green_command`, verification commands, review focus, evidence status,
   and status.
   Slice IDs must be unique `S-###` values. Dependencies must reference existing
   slice IDs. Requirement and acceptance-criteria links must reference IDs that
   appear in `feature.md`.
   For loop-ready execution, also include `iteration_budget`,
   `rollback_point`, `independent_verification`, `failure_triage_notes`,
   `complexity`, `critical_path`, `parallelizable`, `file_ownership`,
   `conflict_risk`, `dependency_notes`, and `test_strategy`.
6. Set `slicing_readiness` to `drafted`.
7. Run `featurectl.py validate --workspace <workspace>`.

Do not use `allowed_files` or `forbidden_files` in v1.

10-loop readiness:

- Keep slices independently reviewable and small enough for repeated
  red/green/review/fix iterations.
- No slice may depend on hidden state from a later slice.
- Cross-module behavior must include at least one integration or regression
  slice.
- High-risk slices should appear early enough that design gaps surface before
  broad implementation.
- Complexity scores use `1..10`; scores `7..10` require smaller follow-up
  slices or a written reason they cannot be split safely.
- Critical-path slices must not be blocked by optional UI polish or
  documentation-only work.
- Parallelizable slices must have disjoint expected touchpoints or an explicit
  conflict-risk mitigation.

If automatic handoff does not happen, print:

```text
Next skill: nfp-06-readiness.
Continue with that skill.
```

## Skill Contract

Inputs:
- `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`, `feature.md`,
  `architecture.md`, `tech-design.md`, ADRs, and test strategy.

Owned artifacts:
- `slices.yaml`, slice dependency/risk notes, and slicing decisions in
  `execution.md`.

Forbidden actions:
- Do not use `allowed_files` or `forbidden_files`, implement code, create
  `approvals.yaml` or `handoff.md`, or mutate `state.yaml` manually.

Validation command:
- `python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace>`

Docs consulted requirement:
- Append `Docs Consulted: Slicing` to `execution.md` with explicit path bullets,
  `Used for`, and `Confidence` entries.

Next step fallback:
- Print `Next skill: nfp-06-readiness` when automatic handoff does not happen.
