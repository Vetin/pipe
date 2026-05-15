# Workflow State Machine

Native Feature Pipeline steps advance in this order:

```text
intake
context
feature_contract
architecture
tech_design
slicing
readiness
worktree
tdd_implementation
review
verification
finish
promote
```

Implementation is blocked until feature contract, architecture, technical design,
and slicing readiness are approved or delegated.

## State Mutation Commands

Agents must mutate machine state through `featurectl.py` rather than editing
`state.yaml` by hand:

```bash
python .agents/pipeline-core/scripts/featurectl.py step set --workspace <workspace> --step <step> --by <actor>
python .agents/pipeline-core/scripts/featurectl.py scope-change --workspace <workspace> --reason "<reason>" --return-step <step> --stale <artifact> --by <actor>
```

`featurectl.py step set` records a `step_changed` event in `events.yaml` and
updates the current run state in `execution.md`.

`featurectl.py scope-change` writes `scope-change.md`, marks selected stale
artifacts, records a `scope_changed` event, and returns the run to the requested
earlier step.

## Readiness Modes

Planning-only and implementation-start validation are distinct:

```bash
python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace> --planning-package
python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace> --implementation
```

`validate --planning-package` checks artifact completeness, slice structure, and
Docs Consulted proof without requiring approval gates.

`validate --implementation` revalidates the planning package, requires approved
or delegated planning gates, verifies the current checkout is the configured
feature worktree, and blocks when relevant planning, evidence, or review
artifacts are stale.

`featurectl.py implementation-ready --workspace <workspace>` is the
operator-facing implementation-start check. It uses the same planning-package
and gate validation as `validate --implementation` and prints readiness-oriented
diagnostics.
