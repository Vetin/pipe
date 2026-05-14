# Verification Review

The final deterministic verification passed.

## Manual Validation

Manual preflight is documented and scriptable through
`pipeline-lab/manual-check/preflight.sh <workspace>`. The real Codex behavioral
test is present but intentionally opt-in through `RUN_REAL_CODEX_E2E=1`.

## Verification Debt

- Real Codex behavioral e2e is not run by default because it requires a local
  Codex binary and can be slow or environment-sensitive.
- Manual checking still needs a human to run the opt-in real Codex test when a
  local Codex environment is available.
