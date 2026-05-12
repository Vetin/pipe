# Feature Card: pipeline/clean-checkout-artifact-hygiene

## Intent

Make Native Feature Pipeline artifacts trustworthy from a clean checkout by
separating dense generated profile data, enforcing readable source-controlled
artifacts, documenting legacy evidence identity semantics, and moving large CLI
entrypoints behind stable wrapper modules.

## Implementation

- Split `.ai/knowledge/project-index.yaml` from verbose
  `.ai/knowledge/profile-examples.yaml`.
- Render `.ai/knowledge/discovered-signals.md` with `Current Feature Picture`,
  `Canonical Signals`, `Noncanonical Signals`, and `Detected Feature Signals`.
- Added `completion_identity_policy` to generated evidence manifests and
  legacy tolerance metadata where old canonical manifests used semantic
  `change_label` entries without a real `diff_hash`.
- Replaced top-level `featurectl.py` and `pipelinebench.py` with stable
  wrappers that import `featurectl_core.cli` and `pipelinebench_core.cli`.
- Stopped project profiling from creating `.ai/knowledge/*.generated.md`
  sidecars when curated knowledge docs already exist.

## Requirements Covered

- FR-001 through FR-007 are covered by slices S-001, S-002, and S-003.
- AC-001 through AC-006 passed through focused tests, CLI smoke checks, and the
  final full feature-pipeline suite.

## Architecture Summary

The public command surface stays unchanged:

```text
featurectl.py -> featurectl_core.cli
pipelinebench.py -> pipelinebench_core.cli
```

Project profile memory is now layered:

```text
project-index.yaml        compact retrieval memory
profile-examples.yaml     verbose source/test/doc/contract examples
discovered-signals.md     canonical vs noncanonical signal map
```

## Slices

- S-001: profile/example split, readable signal sections, and context-skill
  guidance for `lab_signal`.
- S-002: artifact readability guards and evidence identity policy backfill.
- S-003: thin wrappers, importable core CLI modules, shared knowledge updates,
  and generated sidecar suppression.

## Tests

- `python -m pytest tests/feature_pipeline/test_featurectl_core.py -q`
- `python -m pytest tests/feature_pipeline/test_artifact_formatting.py -q`
- `python .agents/pipeline-core/scripts/featurectl.py status --workspace .ai/features/pipeline/portable-artifact-consistency`
- `python .agents/pipeline-core/scripts/pipelinebench.py list-scenarios`
- `python -m unittest discover -s tests/feature_pipeline`
- `python -m pytest tests/feature_pipeline -q`
- `python pipeline-lab/showcases/scripts/validate_pipeline_goals.py --passes 3 --report /tmp/pipeline-goal-validation-final.md`
- `git diff --check`

## Reviews

- Strict review recorded in `reviews/quality.yaml`.
- Verification review recorded in `reviews/verification-review.md`.
- No critical, major, or blocking findings remain.

## Manual Validation

- Confirmed top-level wrappers execute existing CLI commands.
- Confirmed `init --profile-project` no longer creates
  `.ai/knowledge/*.generated.md` sidecars.
- Confirmed goal validation runs three passes with zero failures.

## Verification Debt

- `python -m black --check .agents tests pipeline-lab` was not run because
  `black` is not installed in this environment.
- Residual risk is accepted because source readability is covered by
  `test_artifact_formatting.py` and `git diff --check`.

## Claim Provenance

| Claim | Evidence |
| --- | --- |
| Profile examples are split from compact project index. | S-001 evidence and `tests/feature_pipeline/test_featurectl_core.py`. |
| Legacy change-label-only manifests declare policy. | S-002 evidence and `tests/feature_pipeline/test_artifact_formatting.py`. |
| CLI wrappers preserve command compatibility. | S-003 verification output and final full suite. |
| Generated sidecar noise is blocked. | S-003 retry evidence and artifact formatting guard. |
| Full pipeline remains healthy. | `evidence/final-verification-output.log`. |

## Rollback Guidance

Revert the feature branch commits for this feature. If only the wrapper split is
suspect, restore the prior monolithic scripts from the previous commit and
remove `featurectl_core/` and `pipelinebench_core/`. If profile output changes
are suspect, restore `write_project_profile`, remove `profile-examples.yaml`,
and rerun `featurectl.py init --profile-project`.

## Shared Knowledge Updates

| Path | Decision | Evidence | Future reuse |
| --- | --- | --- | --- |
| `.ai/knowledge/project-index.yaml` | Updated. | S-001 profile split. | Use for compact project retrieval only. |
| `.ai/knowledge/profile-examples.yaml` | Added. | S-001 renderer and refreshed profile. | Use when examples are needed after reading compact index. |
| `.ai/knowledge/discovered-signals.md` | Updated. | S-001 renderer and goal validator fix. | Use canonical signals first; treat lab signals as scoped leads. |
| `.ai/knowledge/architecture-overview.md` | Updated. | S-003 wrapper/core knowledge update. | Reuse wrapper/core topology for future script changes. |
| `.ai/knowledge/module-map.md` | Updated. | S-003 module map update. | Find stable wrappers and core CLI implementation paths. |
| `.ai/knowledge/integration-map.md` | Updated. | S-003 integration update. | Understand wrapper to core to artifact flow. |

## Source Revision

- Verification source revision: `9e50aea6565395dd9aab35c5b1b8312a7c3444a0`.

## Plan Drift

- S-003 required one explicit retry after final verification found that the goal
  validator still expected the phrase `Current Feature Picture`.
- The retry also fixed `init --profile-project` sidecar generation for curated
  docs, which was discovered while validating the clean checkout artifact
  hygiene goal.
