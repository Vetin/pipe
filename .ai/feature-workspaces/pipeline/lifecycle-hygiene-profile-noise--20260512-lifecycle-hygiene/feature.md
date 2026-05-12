# Feature: Lifecycle Hygiene And Profile Noise

## Intent
Stabilize the Native Feature Pipeline source-of-truth lifecycle after promotion and reduce noisy generated feature signals in project knowledge.

## Motivation
Promoted feature workspaces currently remain under `.ai/feature-workspaces` with active-looking state, execution logs can keep stale current-step sections, duplicate slice completion events can appear, and project profiling can surface benchmark/showcase/spec documents as real feature memory.

## Actors
- Codex pipeline user
- Future feature-building agent
- Pipeline maintainer

## Goals
- Make promoted workspaces explicitly read-only or archived so active discovery does not confuse them with in-flight work.
- Keep execution logs with exactly one active `## Latest Status` block and no active legacy `## Current Step` / `## Next Step` sections.
- Make `complete-slice` idempotent unless a retry is explicitly requested.
- Separate canonical feature memory from discovered low-confidence signals and filter generated/spec noise from feature discovery.
- Soften root agent policy for small repairs while preserving pipeline usage for feature, architecture, security, and cross-module changes.

## Non-Goals
- Splitting `featurectl.py` into modules in this slice.
- Replacing the benchmark runner.
- Deleting historical promoted workspaces.
- Changing the canonical feature index schema beyond lifecycle metadata needed for this fix.

## Functional Requirements
- FR-001: Promotion must mark the source workspace as `promoted-readonly` and set machine-readable lifecycle metadata.
- FR-002: Validation must reject active workspaces that duplicate a completed canonical feature unless the workspace is explicitly `promoted-readonly`, `archived`, or `abandoned`.
- FR-003: Execution log validation must require exactly one active `## Latest Status` block for finished/promoted work and reject active legacy `## Current Step` / `## Next Step` sections.
- FR-004: Execution log validation must detect duplicate `completed slice S-###` events unless duplicate entries are marked as retry events.
- FR-005: `complete-slice` must fail before mutating evidence or slice state when the target slice is already complete unless `--append-retry` is used.
- FR-006: Project profiling must exclude generated showcase/run/spec feature signals from canonical feature overview and write discovered signals separately.
- FR-007: Root `AGENTS.md` must use selective pipeline triggers and only require project profiling when knowledge is missing, stale, or explicitly requested.
- FR-008: Legacy `skills/native-feature-pipeline/references` must be clearly marked as archival material, not a production skill reference root.

## Non-Functional Requirements
- NFR-001: Validation failures must be deterministic and identify the exact artifact to fix.
- NFR-002: Generated knowledge output must be usable by future LLM runs without mixing canonical feature memory with low-confidence lab signals.
- NFR-003: Changes must preserve existing successful promoted features and keep current canonical memory readable.

## Acceptance Criteria
- AC-001: A promoted workspace under `.ai/feature-workspaces` validates only when marked `promoted-readonly`, `archived`, or `abandoned`.
- AC-002: A finished/promoted workspace with two active `## Latest Status` sections fails validation.
- AC-003: A finished/promoted workspace with active `## Current Step` or `## Next Step` sections outside history fails validation.
- AC-004: A duplicated non-retry `completed slice S-001` execution event fails validation.
- AC-005: Running `complete-slice` twice on the same slice fails without modifying `evidence/manifest.yaml`.
- AC-006: `init --profile-project` writes canonical features to `.ai/knowledge/features-overview.md` and low-confidence discovered entries to `.ai/knowledge/discovered-signals.md`.
- AC-007: Profile output excludes feature signals from `pipeline-lab/showcases`, `pipeline-lab/runs`, `plan.md`, `vision.md`, and `features.md`.
- AC-008: The full `tests/feature_pipeline` suite passes after the change.

## Assumptions
- Existing promoted workspace directories may remain in the repo if they are explicitly marked read-only.
- Historical execution sections can remain only when they are renamed into history-style sections that do not look like active state.
- `--append-retry` is enough for v1 retry event recording; replacing historical events can be added later if needed.

## Open Questions
- None for this implementation pass.
