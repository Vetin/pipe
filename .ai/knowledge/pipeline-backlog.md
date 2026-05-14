# Pipeline Backlog

Status: curated
Confidence: medium
Needs human review: yes
Last reviewed: 2026-05-13

## Purpose

This file tracks accepted Native Feature Pipeline verification debt that should
not remain hidden inside individual feature cards. Feature cards may still
record local debt, but durable cross-feature work belongs here.

## Active Backlog

### Historical execution log migration

- Source: `pipeline/event-schema-strictness-and-narrative-execution-logs`
- Status: accepted debt
- Reason:
  Historical canonical features can keep their existing execution
  journals, but future migration should convert detailed event-like prose into
  concise narrative summaries with exact records in `events.yaml`.
- Suggested next step:
  Add a migration command or validation mode that can
  rewrite old `execution.md` event logs from sidecar data.

### Showcase benchmark package split

- Source: repeated review findings
- Status: accepted debt
- Reason:
  `pipelinebench_core/showcases.py` is intentionally still inside the
  benchmark package. It should move to a separate showcase package when the
  showcase runner grows again.
- Suggested next step:
  Create `showcasebench_core/` and keep
  `pipelinebench_core` focused on scoring, reports, candidates, and scenarios.

### Promotion event metadata expansion

- Source: event schema review
- Status: accepted debt
- Reason:
  `feature_promoted` currently requires `canonical_path` only. Future
  lifecycle auditing would benefit from `source_workspace` and
  `promotion_mode`, but making them mandatory now would break existing sidecars.
- Suggested next step:
  Add optional metadata first, then promote it to required
  after canonical features are backfilled.

### Real Codex behavioral e2e regularization

- Source: `pipeline/manual-check-readiness-controls`
- Status: accepted debt
- Reason:
  The repository now has an opt-in real Codex behavioral e2e scaffold, but it is
  intentionally not part of the default suite because it requires a local Codex
  binary and can be slow or environment-sensitive.
- Suggested next step:
  Run the opt-in test in a trusted local or CI environment with
  `RUN_REAL_CODEX_E2E=1 CODEX_BIN=codex`, then decide whether to publish a
  scheduled/manual workflow for it.

## Closed Backlog

No closed backlog items have been recorded yet.
