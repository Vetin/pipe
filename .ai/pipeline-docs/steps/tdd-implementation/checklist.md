# TDD Implementation Checklist

- Verify worktree status before touching tests or code.
- Record pre-red git state.
- Write failing test first.
- Confirm red output fails for the expected reason before implementation.
- Triage wrong red failures before production code.
- Implement minimal green code.
- Record green and verification output.
- Record review evidence.
- Update future slices if implementation changes dependency, ownership,
  conflict risk, or test strategy.
- Record iteration ledger entries and resume checkpoints for each loop.
- Record `Docs Consulted: TDD Implementation` in `execution.md`.
- Complete the slice only after evidence validation passes.
