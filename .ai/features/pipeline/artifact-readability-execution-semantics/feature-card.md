# Feature Card: pipeline/artifact-readability-execution-semantics

This feature hardens the pipeline artifact layer after source-of-truth and
lifecycle stabilization. It makes generated YAML and Markdown readable,
normalizes `execution.md` into current-state/event-log/history sections,
formalizes retry slice events, separates lab signals from product memory, adds
manual soft scoring to `pipelinebench.py`, and promotes pipeline architecture
decisions into ADR and knowledge docs.

## Manual Validation

- `python -m pytest tests/feature_pipeline/test_artifact_formatting.py tests/feature_pipeline/test_featurectl_core.py -q`
- `python -m pytest tests/feature_pipeline/test_gates_and_evidence.py tests/feature_pipeline/test_finish_promote.py tests/feature_pipeline/test_featurectl_core.py -q`
- `python -m pytest tests/feature_pipeline/test_pipelinebench.py -q`
- `python -m pytest tests/feature_pipeline -q`
- `python pipeline-lab/showcases/scripts/validate_pipeline_goals.py --passes 3 --report /tmp/readability-goals.md`
- Manual `pipelinebench.py score-run --soft-score-file` against this feature workspace produced `hard_score: 8/8` and `soft_score: 12/15`.

## Verification Debt

No blocking verification debt remains. The remaining maintainability debt is to
split `featurectl.py` into modules after this behavior is canonical.

## Claim Provenance

- Artifact readability claims map to `tests/feature_pipeline/test_artifact_formatting.py`.
- Execution and retry claims map to `tests/feature_pipeline/test_finish_promote.py`,
  `tests/feature_pipeline/test_gates_and_evidence.py`, and migrated
  `.ai/features/pipeline/*/execution.md` files.
- Profile signal claims map to `tests/feature_pipeline/test_featurectl_core.py`,
  `.ai/knowledge/project-index.yaml`, and `.ai/knowledge/discovered-signals.md`.
- Soft-score claims map to `tests/feature_pipeline/test_pipelinebench.py` and
  `pipelinebench.py` manual score output.
- ADR and knowledge claims map to `.ai/knowledge/adr-index.md`,
  `.ai/knowledge/architecture-overview.md`, `.ai/knowledge/module-map.md`, and
  `.ai/knowledge/integration-map.md`.

## Rollback Guidance

Revert this feature's commits if stricter execution validation blocks an urgent
unrelated promotion. Partial rollback options:

- Revert execution-log validation and migration if legacy `execution.md` parsing
  must be accepted temporarily.
- Revert lab-signal classification if project profiling needs the previous
  broad filtering behavior.
- Revert `pipelinebench.py --soft-score-file` if benchmark reports must remain
  hard-check only.

## Shared Knowledge Updates

- `.ai/knowledge/features-overview.md`: canonical feature memory remains the
  first retrieval layer.
- `.ai/knowledge/discovered-signals.md`: lab signals are explicitly marked and
  constrained to pipeline-lab or benchmark work.
- `.ai/knowledge/architecture-overview.md`: control plane, artifact lifecycle,
  evidence lifecycle, execution semantics, and Mermaid topology documented.
- `.ai/knowledge/module-map.md`: featurectl, pipelinebench, skill, feature
  memory, and benchmark ownership documented.
- `.ai/knowledge/integration-map.md`: feature workspace -> canonical feature
  memory -> `.ai/knowledge` flow documented.
- `.ai/knowledge/adr-index.md`: four pipeline architecture decisions indexed.
