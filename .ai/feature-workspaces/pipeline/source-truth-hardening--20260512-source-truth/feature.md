# Feature: Source Of Truth Hardening

## Intent

Make canonical feature memory, active workspace state, execution journals, and
project profiling agree with each other so future agents can trust the Native
Feature Pipeline state without reading the chat transcript.

## Motivation

Recent review findings showed drift between `.ai/features/index.yaml`,
`.ai/features/overview.md`, `feature.yaml`, `state.yaml`, and `execution.md`.
The same review found an evidence mutation hazard, stale legacy reference paths,
unclear subagent fallback policy, and generated showcase noise in project
profiling.

## Actors

- Feature implementer using `featurectl.py`
- Reviewer validating source-of-truth consistency
- Future Codex session retrieving canonical memory
- Pipeline maintainer updating skills and tests

## Goals

- Keep canonical index and overview synchronized.
- Reject completed canonical features whose `feature.yaml` still says `draft`.
- Require execution journals to expose a current machine-readable latest status.
- Make `complete-slice` validation atomic with respect to evidence manifest
  commit metadata.
- Clarify production skill behavior for subagent fallback and promotion
  conflicts.
- Keep generated showcase outputs out of project feature discovery.

## Non-Goals

- Split `featurectl.py` into modules.
- Implement LLM-judge scoring.
- Migrate all historical feature workspaces into an archive.
- Rewrite every old generated execution journal by hand.

## Functional Requirements

- FR-001: `featurectl.py validate` must fail when `.ai/features/index.yaml`
  lists canonical features but `.ai/features/overview.md` does not list the same
  feature keys.
- FR-002: `featurectl.py validate` must fail when a canonical feature indexed as
  complete has a canonical `feature.yaml` status of `draft`.
- FR-003: `featurectl.py validate` must flag active workspaces whose feature key
  is already canonical complete unless the workspace state is promoted,
  archived, or read-only.
- FR-004: `featurectl.py validate` must require `execution.md` to include
  `## Latest Status` with the current step matching `state.yaml.current_step`.
- FR-005: `complete-slice` must not mutate `evidence/manifest.yaml` when
  evidence validation fails.
- FR-006: Production `nfp-*` skills must reference `.agents/pipeline-core`
  shared references, not `skills/native-feature-pipeline/references`.
- FR-007: `nfp-08` and `nfp-09` must define explicit sequential fallback
  behavior when subagents are unavailable.
- FR-008: `nfp-12` must state that `archive-as-variant` archives the incoming
  workspace and never moves the existing canonical feature.
- FR-009: `init --profile-project` must filter generated benchmark/showcase
  output from feature signals.

## Non-Functional Requirements

- NFR-001: The fixes must be covered by focused tests.
- NFR-002: Validation failures must include actionable blocker text.
- NFR-003: Existing lean command set must remain unchanged.
- NFR-004: Changes must be backward-compatible with existing promoted feature
  memory where possible.

## Acceptance Criteria

- AC-001: A test repo with stale `.ai/features/overview.md` fails validation
  with a canonical overview blocker.
- AC-002: A complete indexed feature with canonical `feature.yaml.status: draft`
  fails validation.
- AC-003: A completed workspace with stale `## Latest Status` current step fails
  validation.
- AC-004: A failed `complete-slice` leaves the evidence manifest byte-identical.
- AC-005: No production skill file contains
  `skills/native-feature-pipeline/references`.
- AC-006: The promote skill and promote tests agree that `archive-as-variant`
  archives the incoming workspace.
- AC-007: Project profiling no longer treats generated stress/showcase artifact
  headings as current feature signals.

## Assumptions

- Existing active historical workspaces can remain present for now if marked or
  validated consistently; full archive migration is a later cleanup.
- Pipeline source-of-truth checks can run as part of the normal `validate`
  command instead of introducing a new CLI mode.

## Open Questions

- Should a later migration delete or archive the two historical active
  workspaces that already have canonical memories?
