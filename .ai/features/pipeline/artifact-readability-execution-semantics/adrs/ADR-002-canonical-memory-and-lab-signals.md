# ADR-002: Canonical Memory And Lab Signals

Status: accepted
Date: 2026-05-12

## Context

Project profiling can find real product features, canonical promoted features,
and pipeline-lab benchmark/showcase documents. Mixing those signals makes future
feature agents over-trust generated or lab-only material.

## Decision

Canonical feature memory remains in `.ai/knowledge/features-overview.md`.
Low-confidence discovered signals stay in `.ai/knowledge/discovered-signals.md`.
Signals from `pipeline-lab/` are categorized as `lab_signal` and should be used
only when working on pipeline-lab, benchmarks, showcases, or validation tooling.

## Consequences

Feature planning has a cleaner retrieval order: canonical memory first,
discovered source leads second, lab signals only for pipeline infrastructure
work. Generated showcase/run outputs remain filtered out of product feature
memory.
