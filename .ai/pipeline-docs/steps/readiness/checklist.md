# Readiness Checklist

- Run `featurectl.py validate --readiness`.
- Run a read-only cross-artifact analyze pass.
- Confirm every requirement has architecture, design, slice, and test coverage.
- Confirm slice dependencies, critical path, ownership, parallelization, and
  conflict-risk notes are coherent.
- Summarize missing artifacts, stale flags, assumptions, and gate blockers.
- Record `Docs Consulted: Readiness` in `execution.md`.
- Ask for implementation approval or stop at the requested point.
