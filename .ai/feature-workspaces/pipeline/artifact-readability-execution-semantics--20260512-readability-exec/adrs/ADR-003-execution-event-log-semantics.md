# ADR-003: Execution Event Log Semantics

Status: accepted
Date: 2026-05-12

## Context

Older execution logs mixed active status, historical notes, gate events, and
slice completion events across several sections. That made it hard to determine
the authoritative current step or identify duplicate slice completion events.

## Decision

`execution.md` uses three operational sections:

- `## Current Run State`: the single mutable current status section.
- `## Event Log`: append-only chronological operational events.
- `## History`: migrated or non-operational historical notes.

Retry slice completions use structured events with `attempt` and `reason`.
Deprecated `## Latest Status`, active `## Current Step`, and active `## Next
Step` headings are invalid for finished or promoted work.

## Consequences

Validation can detect stale status, event placement drift, duplicate completion
events, and ambiguous retry entries. Future tooling can parse event history
without interpreting prose sections.
