# Feature Card: pipeline/source-truth-hardening

Source-truth hardening keeps canonical feature memory, execution journals,
promotion status, evidence manifests, production skill reference roots, and
project profile output aligned.

## Manual Validation

- Focused canonical memory tests validate overview/index/status/workspace drift.
- Evidence tests validate failed `complete-slice` attempts do not mutate the
  manifest.
- Methodology tests validate `.agents/pipeline-core/references` as the
  production reference root and explicit subagent fallback policy.
- Project profile tests validate generated showcase/stress artifacts are
  filtered while real feature docs remain discoverable.

## Verification Debt

- `featurectl.py` remains a large single file and should be split later.
- Historical promoted workspaces should eventually move to an archive via a
  deterministic migration command.

## Claim Provenance

- Canonical memory claims: `tests/feature_pipeline/test_finish_promote.py`.
- Evidence atomicity claims: `tests/feature_pipeline/test_evidence_order.py`.
- Skill policy claims: `tests/feature_pipeline/test_methodology_contract.py`.
- Project profile claims: `tests/feature_pipeline/test_featurectl_core.py`.
- Slice evidence: `evidence/manifest.yaml`.

## Rollback Guidance

Revert this feature branch or the individual commits. No external data,
credentials, services, or migrations are touched.

## Shared Knowledge Updates

- `.ai/knowledge/features-overview.md`: should describe canonical feature memory
  separately from generated benchmark/showcase artifacts.
- `.ai/knowledge/architecture-overview.md`: should mention source-truth
  validation as part of the pipeline architecture.
- `.ai/knowledge/module-map.md`: should retain `.agents`, `.ai`, `pipeline-lab`,
  and `tests` as main module boundaries.
- `.ai/knowledge/integration-map.md`: no external integration changes.
