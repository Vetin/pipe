# Feature: Execution Safety Guardrails

## Intent

Make the Native Feature Pipeline harder to misuse during real execution before
manual checking begins.

## Motivation

The repository now has the right pipeline shape, but review identified paths
where agents or tests can still bypass safety: real Codex e2e can validate from
the wrong directory, planning-only prompts do not prove product code stayed
unchanged, step and gate commands can jump ahead, and active workspaces can omit
the machine event log.

## Actors

- Codex sessions running the Native Feature Pipeline.
- Maintainers running deterministic and opt-in real Codex tests.
- Future agents reading pipeline artifacts before implementation.

## Problem

The pipeline can look valid while important execution invariants are not
enforced by tools. Manual checking should not start until command behavior,
validation, and e2e scaffolds make unsafe shortcuts visible.

## Goals

- Enforce legal step transitions through `featurectl.py step set`.
- Enforce planning gate dependencies through `featurectl.py gate set`.
- Require `events.yaml` for active workspaces.
- Validate `execution.md` current-state consistency throughout active runs.
- Split worktree correctness from implementation readiness.
- Prove real Codex planning-only tests do not change product source or tests.
- Distinguish under-specified prompts that must stop for clarification.
- Require per-path Docs Consulted use and confidence.
- Label outcome-smoke runner output as partial pipeline fidelity.
- Block `featurectl.py new` on dirty base checkouts unless explicitly allowed.
- Expand CI or workflow coverage for the deterministic feature pipeline suite.

## Non-Goals

- Do not globally migrate historical canonical feature journals in this slice.
- Do not automate a full production Codex harness beyond the opt-in e2e
  scaffold.
- Do not remove the existing mock e2e tests or pipelinebench offline modes.
- Do not change the core `events.yaml` event schema unless required by these
  guardrails.

## Functional Requirements

- FR-001: Real Codex e2e tests must run `featurectl.py validate` from the
  feature worktree, not from the parent `worktrees/` directory.
- FR-002: Real Codex planning-only tests must prove product source files,
  product tests, and package manifests are unchanged before gates.
- FR-003: Under-specified real Codex prompts must record blocking questions or
  stop before full planning artifacts and approvals.
- FR-004: Sufficiently specified real Codex prompts may draft the planning
  package, pass `validate --planning-package`, and fail
  `validate --implementation` until gates are approved or delegated.
- FR-005: `featurectl.py step set` must reject illegal forward jumps and require
  `scope-change` for backward replanning.
- FR-006: `featurectl.py gate set` must enforce gate dependency order for
  architecture, technical design, slicing readiness, implementation, review,
  verification, and finish gates.
- FR-007: Active workspaces must include `events.yaml`; legacy inactive or
  canonical records may remain tolerant.
- FR-008: `execution.md` current-state basics must be validated for every active
  workspace, not only at finish or promote.
- FR-009: `worktree-status` must report worktree isolation only; implementation
  readiness must be available as a separate command.
- FR-010: Docs Consulted validation must require every referenced path to have a
  use explanation and low, medium, or high confidence.
- FR-011: Outcome-smoke e2e reports must be marked as partial pipeline fidelity
  and not valid as full pipeline readiness evidence.
- FR-012: `featurectl.py new` must fail on dirty base checkouts unless
  `--allow-dirty` is provided.
- FR-013: CI must include a deterministic full `tests/feature_pipeline` run or a
  clearly named job for it.

## Non-Functional Requirements

- NFR-001: Guardrails must be deterministic and testable without a live Codex
  binary, except for explicitly opt-in real e2e tests.
- NFR-002: Error messages must tell the caller which command or gate is blocked
  and why.
- NFR-003: Existing promoted or legacy canonical artifacts must not be broken by
  stricter active-workspace validation.
- NFR-004: The implementation must preserve existing mock e2e and offline
  benchmark coverage.

## Acceptance Criteria

- AC-001: Tests fail if the real Codex e2e validates from `worktrees/` instead
  of the feature worktree.
- AC-002: Tests fail if a planning-only real Codex run modifies `auth.py`,
  `test_auth.py`, package manifests, or other non-pipeline product files.
- AC-003: Tests cover under-specified and sufficiently specified reset-password
  prompts with different expected outcomes.
- AC-004: Tests cover blocked and allowed `step set` transitions.
- AC-005: Tests cover blocked gate approvals before dependencies are satisfied.
- AC-006: Validation fails active workspaces that omit `events.yaml`.
- AC-007: Active execution logs fail validation when Current Run State does not
  match `state.yaml.current_step`.
- AC-008: `worktree-status` can pass for a planning-only workspace while
  `implementation-ready` fails.
- AC-009: Docs Consulted sections fail when one `Used for` entry is reused for
  multiple paths or confidence is missing.
- AC-010: Outcome-smoke manifests and reports include partial-fidelity labels.
- AC-011: `featurectl.py new` fails on a dirty base checkout without
  `--allow-dirty` and passes with it.
- AC-012: The deterministic feature pipeline suite runs locally before
  promotion.

## Product Risks

- Stricter validation may expose old tests or fixtures that relied on permissive
  state mutation.
- Legal transition checks may block ad hoc repair workflows unless scope-change
  is used intentionally.
- Real Codex e2e behavior can vary by environment, so the opt-in tests must keep
  robust assertions and useful artifacts.

## Assumptions

- `events.yaml` remains the official machine-readable event history.
- Inactive promoted-readonly, archived, abandoned, or canonical records can use
  legacy tolerance where needed.
- The feature worktree shape remains
  `worktrees/<feature>/.ai/feature-workspaces/<domain>/<run>`.
- CI can run deterministic tests without the opt-in real Codex e2e.

## Open Questions

- Should future gate dependency checks validate artifact content at approval
  time, or only enforce dependency order and leave artifact quality to
  `validate`?
