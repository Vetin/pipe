# ADR-005 Core Modules And Event Sidecar

Status: accepted
Date: 2026-05-13

## Context

`featurectl_core/cli.py` and `pipelinebench_core/cli.py` had become the main
maintainability bottlenecks. They mixed command parsing, validation, evidence,
promotion, project profiling, scoring, reports, candidates, and showcase logic
in large modules.

The pipeline also stored execution history primarily as readable Markdown. That
is useful for humans, but future validators and benchmark tools need a parseable
event source that does not depend on scraping prose.

## Decision

Keep `.agents/pipeline-core/scripts/featurectl.py` and
`.agents/pipeline-core/scripts/pipelinebench.py` as stable wrappers. Move their
internals into focused core modules with clear ownership boundaries.

Create `events.yaml` for new feature workspaces. The sidecar mirrors parseable
events from `execution.md` and keeps `execution.md` as the human-readable run
journal.

## Consequences

- CLI behavior remains stable for users and nested Codex sessions.
- Future fixes can target smaller modules instead of editing large dispatch
  files.
- Validators and benchmarks can consume `events.yaml` directly.
- Existing workspaces remain legacy-compatible; new workspaces get the sidecar
  during creation.

## Source Anchors

- `.agents/pipeline-core/scripts/featurectl_core/`
- `.agents/pipeline-core/scripts/pipelinebench_core/`
- `.agents/pipeline-core/scripts/featurectl_core/events.py`
- `.ai/feature-workspaces/pipeline/core-modularity-and-readable-events--20260513-core-modularity-events/events.yaml`
