# Verification Review

## Manual Validation

- `python .agents/pipeline-core/scripts/featurectl.py --help`: passed.
- `python .agents/pipeline-core/scripts/pipelinebench.py --help`: passed.
- `python .agents/pipeline-core/scripts/pipelinebench.py list-scenarios`: passed.
- `python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace> --evidence`: passed.
- `git diff --check`: passed.
- `python -m pytest tests/feature_pipeline -q`: passed with 154 tests and
  301 subtests.

## Verification Debt

None. The remaining risk is limited to normal follow-up observation after
promotion because this change reorganizes local control-plane modules and
generated artifacts without changing external services.

## Review Notes

The wrapper entrypoints still execute, event sidecars are created for new
workspaces, and canonical-vs-lab signal rules are covered by contract tests.
