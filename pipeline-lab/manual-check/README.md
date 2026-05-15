# Manual Check Readiness

This directory contains the repeatable preflight used before manual pipeline
checking. It complements deterministic unit tests and the mock Codex runner with
an explicit opt-in path for real conversational Codex behavior.

## Test Matrix

| Layer | Purpose | Command |
| --- | --- | --- |
| Deterministic unit tests | Validate featurectl, schemas, events, gates, evidence, and promotion behavior. | `python -m pytest tests/feature_pipeline -q` |
| Mock prompt-runner tests | Validate prompt shape, worktree preparation, command wiring, and runner artifacts without invoking real Codex. | `python -m pytest tests/feature_pipeline/test_codex_e2e_runner.py -q` |
| Real Codex behavioral e2e | Validate user prompt to Codex to pipeline workspace behavior. | `RUN_REAL_CODEX_E2E=1 CODEX_BIN=codex python -m pytest tests/feature_pipeline/test_real_codex_conversation.py -q` |
| Manual preflight | Validate a specific workspace before human inspection. | `pipeline-lab/manual-check/preflight.sh <workspace>` |

## Manual Pass Criteria

Manual pass criteria:

- feature worktree exists.
- feature workspace exists inside the worktree.
- `apex.md`, `feature.yaml`, `state.yaml`, and `execution.md` exist.
- `feature.md`, `architecture.md`, `tech-design.md`, and `slices.yaml` exist.
- `execution.md` records Docs Consulted sections with real paths and use notes.
- `featurectl.py validate --workspace <workspace> --planning-package` passes.
- `featurectl.py worktree-status --workspace <workspace>` validates checkout
  isolation without requiring implementation gates.
- `featurectl.py implementation-ready --workspace <workspace>` fails until
  gates are approved or delegated.
- no implementation code changed before gates.
- `approvals.yaml` and `handoff.md` do not exist.

## Preflight Behavior

The preflight script prints the current branch, git status, feature status,
base validation, planning package validation, implementation readiness, and
worktree status. Worktree status checks branch/path isolation only.
Implementation readiness remains a separate check and may be blocked for
planning-only workspaces; that is reported without hiding the result.
