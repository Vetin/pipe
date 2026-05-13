# ADR Index

Status: curated
Confidence: medium
Needs human review: yes
Last reviewed: 2026-05-13

## Promoted Pipeline Decisions

- ADR-001 Promoted Readonly Workspaces
  - Source: `.ai/features/pipeline/artifact-readability-execution-semantics/adrs/ADR-001-promoted-readonly-workspaces.md`
  - Decision: promoted workspaces remain as read-only run evidence instead of
    being left active or deleted.
- ADR-002 Canonical Memory And Lab Signals
  - Source: `.ai/features/pipeline/artifact-readability-execution-semantics/adrs/ADR-002-canonical-memory-and-lab-signals.md`
  - Decision: canonical feature memory is separate from discovered signals;
    `lab_signal` is limited to pipeline-lab and benchmark work.
- ADR-003 Execution Event Log Semantics
  - Source: `.ai/features/pipeline/artifact-readability-execution-semantics/adrs/ADR-003-execution-event-log-semantics.md`
  - Decision: `execution.md` has one current-state section, one event log, and
    structured retry completion events.
- ADR-004 Manual Benchmark Soft Scoring
  - Source: `.ai/features/pipeline/artifact-readability-execution-semantics/adrs/ADR-004-manual-benchmark-soft-scoring.md`
  - Decision: `pipelinebench.py` keeps hard checks deterministic and accepts
    manual soft-score YAML as reviewer data.
- ADR-005 Core Modules And Event Sidecar
  - Source: `.ai/features/pipeline/core-modularity-and-readable-events/adrs/ADR-005-core-modules-and-event-sidecar.md`
  - Decision: CLI wrappers stay stable while control-plane internals move into
    focused modules, and new workspaces maintain a parseable `events.yaml`
    sidecar beside human-readable `execution.md`.
- ADR-006 Events Schema And Execution Boundary
  - Source: `.ai/features/pipeline/raw-schema-and-execution-boundary-hardening/adrs/ADR-006-events-schema-and-execution-boundary.md`
  - Decision: `events.yaml` is the machine-readable event source of truth;
    `execution.md` is the human-readable journal.
