# Feature Card: Guardrail Status And Summary Polish

## Implementation

- Added `.ai/knowledge/pipeline-guardrails-status.md` as a durable status anchor
  for public raw, wrapper, compile, artifact-formatting, and workflow checks.
- Hardened artifact formatting tests so generated canonical YAML cannot regress
  into blank-line-noisy output.
- Added promotion-time execution-summary compaction from `events.yaml`.
- Split review validation into `featurectl_core/validators/review.py`.
- Reformatted central backlog items into readable reason and next-step blocks.

## Manual Validation

- `python -m pytest tests/feature_pipeline/test_artifact_formatting.py -q`
  passed.
- `python -m pytest tests/feature_pipeline/test_finish_promote.py -q` passed.
- `python -m pytest tests/feature_pipeline/test_gates_and_evidence.py -q`
  passed.
- `python -m pytest tests/feature_pipeline -q` passed with 174 tests and
  409 subtests.
- `python .agents/pipeline-core/scripts/pipelinebench.py check-public-raw
  --min-lines 5` passed.
- `python -m compileall .agents/pipeline-core/scripts` passed.
- `git diff --check` passed.

## Verification Debt

- Historical canonical execution journals remain unmigrated unless a dedicated
  migration feature is requested.
- Showcase/demo code remains in `pipelinebench_core/showcases.py`.
- Promotion event metadata expansion remains backlog work.

## Claim Provenance

- Guardrail status is backed by
  `.ai/knowledge/pipeline-guardrails-status.md`,
  `.github/workflows/pipeline-guardrails.yml`, and
  `pipelinebench_core/raw_checks.py`.
- YAML readability is backed by
  `tests/feature_pipeline/test_artifact_formatting.py`.
- Promotion summary compaction is backed by `featurectl_core/events.py` and
  `tests/feature_pipeline/test_finish_promote.py`.
- Review validator modularity is backed by
  `featurectl_core/validators/review.py` and review-blocking tests.

## Rollback Guidance

Revert the slice commits in reverse order. Removing the promotion compaction
call restores per-event summaries without changing `events.yaml`. Moving review
helpers back into `validation.py` restores the previous module layout without
changing artifact schemas.

## Shared Knowledge Updates

- `.ai/knowledge/pipeline-guardrails-status.md` records permanent guardrail
  status and thresholds.
- `.ai/knowledge/architecture-overview.md` references the status document.
- `.ai/knowledge/module-map.md` lists `validators/review.py`.
- `.ai/knowledge/integration-map.md` describes the status-document retrieval
  path.
- `.ai/knowledge/pipeline-backlog.md` now uses readable reason and next-step
  blocks.

## Plan Drift

Review validator extraction landed during the first slice because the red
artifact-formatting test intentionally checked for `validators/review.py`.
The final slice verified that extraction and recorded evidence separately.
