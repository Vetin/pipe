# Pipeline Constitution

Status: initial

The repository follows the Native Feature Pipeline for substantial feature work.

## Verification Commands

- `python -m unittest discover -s tests`

## Safety Rules

- Keep feature work isolated in git worktrees.
- Keep deterministic state in `state.yaml`.
- Keep approvals and handoff notes in `execution.md`.
- Do not use `approvals.yaml` or `handoff.md`.
- Do not implement before required planning gates are approved or delegated.
