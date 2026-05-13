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
- Reason: historical canonical features can keep their existing execution
  journals, but future migration should convert detailed event-like prose into
  concise narrative summaries with exact records in `events.yaml`.
- Suggested next step: add a migration command or validation mode that can
  rewrite old `execution.md` event logs from sidecar data.

### Showcase benchmark package split

- Source: repeated review findings
- Status: accepted debt
- Reason: `pipelinebench_core/showcases.py` is intentionally still inside the
  benchmark package. It should move to a separate showcase package when the
  showcase runner grows again.
- Suggested next step: create `showcasebench_core/` and keep
  `pipelinebench_core` focused on scoring, reports, candidates, and scenarios.

### Promotion event metadata expansion

- Source: event schema review
- Status: accepted debt
- Reason: `feature_promoted` currently requires `canonical_path` only. Future
  lifecycle auditing would benefit from `source_workspace` and
  `promotion_mode`, but making them mandatory now would break existing sidecars.
- Suggested next step: add optional metadata first, then promote it to required
  after canonical features are backfilled.

## Closed Backlog

No closed backlog items have been recorded yet.
