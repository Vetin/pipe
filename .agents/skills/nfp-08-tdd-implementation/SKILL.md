---
name: nfp-08-tdd-implementation
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 08 TDD Implementation

Use this skill to implement slices with red-green-refactor evidence.

Responsibilities:

- record pre-red git state
- write failing test first
- store raw red, green, and verification outputs under `evidence/`
- record evidence through `featurectl.py record-evidence`
- complete slices only after evidence order is valid
- commit each completed slice or record a diff hash

Before implementation:

1. Change into the feature worktree root.
2. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py worktree-status --workspace <workspace>
   ```

3. Stop immediately if it fails. Do not write tests, implementation code, or
   evidence until it passes.

Per slice:

1. Record pre-red git state.
2. Write the failing test first.
3. Run the slice red command.
4. Store raw red output with `featurectl.py record-evidence`.
5. Implement the minimum code needed for green.
6. Run the slice green command.
7. Store raw green output with `featurectl.py record-evidence`.
8. Run verification commands.
9. Store raw verification output with `featurectl.py record-evidence`.
10. Run review and store review evidence.
11. Commit the slice or compute a diff hash.
12. Run `featurectl.py complete-slice`.

If implementation reveals the plan is wrong, stop, write `scope-change.md`, mark
affected artifacts stale, and return to the correct earlier skill.
