# ADR-010 Manual Check Readiness Controls

## Status

Accepted for this feature.

## Context

The repository is structurally aligned with the Native Feature Pipeline, but
manual checking requires stronger operational guarantees. Agents need a command
for step transitions, a validation mode for planning-only workflows, an
operational scope-change path, stronger docs-consulted proof, and opt-in real
Codex e2e checks.

## Decision

Add first-class control-plane support for step transitions, planning-package
validation, scope changes, manual preflight, and optional real Codex e2e
behavioral tests. Keep `events.yaml` as the official machine-readable event log
and keep `execution.md` as the human-readable journal.

## Consequences

- Skills no longer need to edit `state.yaml.current_step` manually.
- Planning-only workflows can validate artifacts without implementation
  approval.
- Scope changes have a durable artifact and stale-state mechanics.
- Manual checking has a reproducible preflight.
- Real Codex e2e remains opt-in and does not destabilize normal CI.
