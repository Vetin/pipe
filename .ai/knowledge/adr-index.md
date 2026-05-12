# ADR Index

Status: curated
Confidence: medium
Needs human review: yes
Last reviewed: 2026-05-12

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
