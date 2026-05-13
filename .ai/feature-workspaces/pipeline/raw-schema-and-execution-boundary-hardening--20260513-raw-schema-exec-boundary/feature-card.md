# Feature Card: Raw Schema And Execution Boundary Hardening

## Summary

This feature resolves the remaining clean-checkout and source-of-truth findings
from the public review.

It confirms that the earlier raw one-line wrapper reports were stale in this
environment, then hardens the repository so the same regression is caught from
local checked-out bytes.

## Implementation

- Fixed `featurectl_core.formatting.read_yaml()` so YAML errors raise
  `FeatureCtlError` instead of `NameError`.
- Changed YAML output to preserve Unicode with `allow_unicode=True`.
- Added public raw byte guard tests for wrappers, `.gitignore`, and canonical
  feature index files.
- Added `events.schema.json` and `events.yaml` validation.
- Updated generated apex docs to include `events.yaml` before evidence.
- Normalized promoted implementation gates to `complete`.
- Backfilled the `core-modularity-and-readable-events` canonical feature.
- Split oversized validation logic into focused validator modules.

## Validation

- `python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace> --evidence`
- `python -m py_compile <featurectl_core> <validators> <pipelinebench_core>`
- `python .agents/pipeline-core/scripts/featurectl.py --help`
- `python .agents/pipeline-core/scripts/pipelinebench.py --help`
- `python .agents/pipeline-core/scripts/pipelinebench.py list-scenarios`
- `python -m pytest tests/feature_pipeline -q`
- `git diff --check`

The full feature-pipeline suite passed with `161 passed, 317 subtests passed`.

## Evidence

- S-001 captured red/green evidence for formatting helper runtime failures and
  raw-byte guardrails.
- S-002 captured red/green evidence for missing event schema validation.
- S-003 captured red/green evidence for apex, event boundary, and lifecycle drift.
- S-004 captured red/green evidence for the validation hotspot split.
- Final verification output is stored in `evidence/final-verification-output.log`.

## Review

Strict review passed with no blocking findings.

Residual risk:

- Public raw responses can lag immediately after push.
- The validation split reduced the main hotspot but did not split every validator.

## Manual Validation

- Verified public raw line counts for `featurectl.py`, `pipelinebench.py`,
  `.gitignore`, and `.ai/features/index.yaml`.
- Verified wrapper command output locally.
- Verified `events.yaml` validation rejects malformed sidecars.
- Verified the core modularity canonical feature now documents `events.yaml`.

## Verification Debt

- Re-run public raw checks after pushing to `origin/main`.
- Continue splitting `featurectl_core/validation.py` if future validators grow.
- Keep showcase logic separation from benchmark scoring as a later cleanup.

## Claim Provenance

- Raw byte findings are backed by local `curl` checks and byte-count tests.
- Event validation claims are backed by `tests/feature_pipeline/test_gates_and_evidence.py`.
- Lifecycle claims are backed by `tests/feature_pipeline/test_finish_promote.py`.
- Maintainability claims are backed by the validator module split test.

## Shared Knowledge Updates

The feature promotes:

- a new ADR for the `events.yaml` and `execution.md` boundary;
- canonical memory for raw byte guardrails and event schema validation;
- focused validator module ownership for future pipeline repairs.
- `.ai/knowledge/architecture-overview.md` should continue to describe
  `events.yaml` as the machine-readable event source.
- `.ai/knowledge/module-map.md` should include the validator module boundary.
- `.ai/knowledge/adr-index.md` should reference ADR-006 after promotion.

## Rollback Guidance

Revert the feature commits on the feature branch before promotion, or revert the
promoted canonical feature commit on `main` after promotion.
