# Verification Review

## Manual Validation

- Confirmed `pipelinebench.py check-public-raw --min-lines 5` remains available.
- Added `.github/workflows/pipeline-guardrails.yml` so wrapper help, compileall,
  artifact formatting tests, and public raw checks run on `main`.
- Confirmed `events.schema.json` rejects unexpected top-level fields.
- Confirmed `execution.md` receives concise prose summaries while exact records
  remain in `events.yaml`.
- Confirmed `validation.py` is reduced to 377 lines after moving focused checks
  into validator modules.
- Confirmed `.ai/knowledge/pipeline-backlog.md` records accepted verification debt.

## Verification Debt

- Historical canonical `execution.md` files were not globally migrated.
- `pipelinebench_core/showcases.py` remains in the benchmark package and is now
  tracked in `.ai/knowledge/pipeline-backlog.md`.
- Promotion events still require only `canonical_path`; future metadata
  expansion is tracked in `.ai/knowledge/pipeline-backlog.md`.

## Commands

- `python -m pytest tests/feature_pipeline/test_artifact_formatting.py -q`
- `python -m pytest tests/feature_pipeline/test_gates_and_evidence.py -q`
- `python -m pytest tests/feature_pipeline/test_finish_promote.py tests/feature_pipeline/test_gates_and_evidence.py -q`
- `python -m pytest tests/feature_pipeline -q`
