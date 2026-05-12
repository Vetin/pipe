# ADR-001: Promoted Readonly Workspaces

Status: accepted
Date: 2026-05-12

## Context

Completed features need canonical memory under `.ai/features`, but the original
workspace still contains useful run evidence: execution history, red/green logs,
reviews, and intermediate artifacts.

## Decision

Promotion keeps the source workspace as read-only run evidence. The canonical
copy is written under `.ai/features`, while the source workspace gets
`feature.yaml.status: promoted-readonly`, `state.yaml.lifecycle:
promoted-readonly`, and `state.yaml.read_only: true`.

## Consequences

Future agents can inspect the run evidence without mistaking it for active work.
Validation rejects active workspaces that duplicate completed canonical features
unless the workspace is explicitly inactive.
