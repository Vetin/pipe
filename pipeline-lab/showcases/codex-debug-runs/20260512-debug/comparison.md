# Codex E2E Runner Comparison

## Current Tests

- Unit test path: `$ROOT/tests/feature_pipeline/test_codex_e2e_runner.py`
- Uses fake Codex: `true`

## Selected Debug Runner

- Mode: `mock`
- Case count: `1`
- Advantage: explicit execution_mode, real Codex preflight, timeout metadata, generated artifact validation, and comparison report
- Recommendation: Keep fast mock unit tests, and use this debug runner for scalable real Codex smoke runs and artifact-quality review.
