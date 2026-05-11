---
name: nfp-05-slicing
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 05 Slicing

Use this skill to create `slices.yaml`.

Methodology:

- Read `.agents/pipeline-core/references/native-skill-protocol.md`.
- Confirm the current directory is the feature worktree.
- Read `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`,
  `feature.md`, `architecture.md`, and `tech-design.md`.
- Load the slicing docset with `featurectl.py load-docset --step slicing`.
- Use `methodology/extracted/workflow-and-gates.md` and
  `.agents/pipeline-core/references/generated-templates/slice-template.yaml`.
- Record `Docs Consulted: Slicing` in `execution.md`.

Responsibilities:

- create TDD slices linked to requirements and acceptance criteria
- include expected touchpoints, red command, expected failure, green command,
  verification commands, review focus, evidence status, and status
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
   `rollback_point`, `independent_verification`, and `failure_triage_notes`.
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

If automatic handoff does not happen, print:

```text
Next skill: nfp-06-readiness.
Continue with that skill.
```
