# Feature Card: pipeline/portable-artifact-consistency

## Summary

Portable artifact consistency closes the remaining source-of-truth drift found
in review: canonical features now synchronize into `.ai/knowledge`, project
profiles avoid local absolute paths, canonical discovered signals use
non-contradictory labels, execution logs use structured slice events, semantic
completion labels live in `change_label`, and source-controlled Python files are
guarded against collapsed long-line formatting.

## Implementation

- `featurectl.py init --profile-project` writes `project.root: .` and prefers the
  remote repository name before a worktree directory fallback.
- `featurectl.py promote` refreshes `.ai/knowledge/features-overview.md` and
  `.ai/knowledge/project-index.yaml` together with `.ai/features`.
- Repository source-truth validation rejects stale knowledge feature memory and
  absolute project roots.
- `complete-slice` stores hexadecimal values in `diff_hash` and semantic labels
  in `change_label`.
- Execution events use `event_type=slice_completed` or
  `event_type=slice_retry_completed` with attempt, reason, and retry supersedes
  metadata.
- Current run state is written after the event log and history sections.

## Manual Validation

- `python -m pytest tests/feature_pipeline -q`
- `git diff --check`
- `featurectl.py validate --workspace .ai/feature-workspaces/pipeline/portable-artifact-consistency--20260512-portable-consistency`
- Canonical validation for the six existing promoted pipeline features.

## Verification Debt

- `black` is not installed locally, so `python -m black --check .agents tests
  pipeline-lab` could not run.
- Source readability is enforced by `test_artifact_formatting.py` until formatter
  installation is standardized.

## Claim Provenance

- Source-truth synchronization claims map to `featurectl.py`,
  `test_featurectl_core.py`, and `test_finish_promote.py`.
- Event/evidence claims map to `featurectl.py`,
  `test_gates_and_evidence.py`, and migrated canonical `execution.md` and
  `evidence/manifest.yaml` files.
- Readability claims map to `test_artifact_formatting.py` and the full
  `tests/feature_pipeline` run.

## Rollback Guidance

- Revert this feature commit range to restore previous promotion/profile/event
  behavior.
- If only event validation becomes too strict for legacy artifacts, temporarily
  move old prose events under `## History` before reverting code.
- If promotion sync causes unexpected project profile churn, revert
  `sync_knowledge_canonical_features` and rerun `featurectl.py init
  --profile-project` manually after promotion.

## Shared Knowledge Updates

- `.ai/knowledge/features-overview.md`: includes the latest canonical feature
  memory and is synchronized during promotion.
- `.ai/knowledge/project-index.yaml`: stores repository-relative root metadata
  and all canonical feature keys.
- `.ai/knowledge/discovered-signals.md`: uses `Canonical reason` for canonical
  entries and reserves `Why not canonical` for noncanonical signals.
- `.ai/knowledge/architecture-overview.md`: existing pipeline architecture
  memory remains valid; this feature reinforces the artifact lifecycle.
