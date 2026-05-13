# Integration Map

Status: curated
Confidence: medium
Needs human review: yes
Last reviewed: 2026-05-13

## Pipeline Artifact Flow

The primary integration is file-based and repository-local:

```text
user request -> nfp skills -> featurectl.py wrapper -> featurectl_core modules -> feature workspace -> canonical feature memory -> .ai/knowledge
```

`featurectl.py` is a stable wrapper. Focused `featurectl_core` modules mutate
machine-readable artifacts, validation status, evidence manifests, and the
parseable `events.yaml` sidecar. `nfp-*` skills write narrative planning,
review, and finish artifacts around those files.

`pipelinebench.py` is a stable wrapper. Focused `pipelinebench_core` modules
read completed feature workspaces or canonical features and write benchmark
score artifacts.

## Runtime Boundaries

- Feature workspace -> canonical feature memory: `promote` copies completed
  artifacts, updates `.ai/features/index.yaml`, refreshes `.ai/features/overview.md`,
  and marks the source workspace read-only.
- Evidence -> review -> verification: slice evidence feeds review artifacts,
  final verification output, and feature-card claim provenance.
- Project profile -> context skill: `init --profile-project` refreshes
  `.ai/knowledge/project-index.yaml`, `.ai/knowledge/features-overview.md`, and
  `.ai/knowledge/discovered-signals.md`.
- Project profile -> init showcase runner: repeated repository profiling reads
  stable counts and modules from `project-index.yaml` while reading feature
  signal names from `discovered-signals.md`.
- Execution event log -> validators and benchmarks: `execution.md` remains the
  human-readable journal, while `events.yaml` provides structured event records.
- Benchmark score -> skill iteration: hard checks catch structural regressions;
  manual soft scores capture architecture clarity, module communication, reuse,
  ADR usefulness, and review quality.
- Public raw check -> remote or file raw bytes: `pipelinebench.py
  check-public-raw` verifies physical newline counts for rendered source
  artifacts without executing fetched content.
- CLI wrapper -> core module: top-level scripts stay small and stable while
  implementation details stay under focused `featurectl_core` and
  `pipelinebench_core` modules.

## External Integrations

The pipeline has no required network service dependency. Real Codex showcase
runners may invoke a local `codex` binary, but deterministic tests use local fake
or offline runners. Manual soft-score files are trusted local reviewer input and
are parsed as YAML data only.
