# Integration Map

Status: curated
Confidence: medium
Needs human review: yes
Last reviewed: 2026-05-12

## Pipeline Artifact Flow

The primary integration is file-based and repository-local:

```text
user request -> nfp skills -> featurectl.py wrapper -> featurectl_core -> feature workspace -> canonical feature memory -> .ai/knowledge
```

`featurectl.py` is a stable wrapper; `featurectl_core/cli.py` mutates
machine-readable artifacts and validation status. `nfp-*` skills write the
narrative planning, review, and finish artifacts around those files.
`pipelinebench.py` is a stable wrapper; `pipelinebench_core/cli.py` reads
completed feature workspaces or canonical features and writes benchmark score
artifacts.

## Runtime Boundaries

- Feature workspace -> canonical feature memory: `promote` copies completed
  artifacts, updates `.ai/features/index.yaml`, refreshes `.ai/features/overview.md`,
  and marks the source workspace read-only.
- Evidence -> review -> verification: slice evidence feeds review artifacts,
  final verification output, and feature-card claim provenance.
- Project profile -> context skill: `init --profile-project` refreshes
  `.ai/knowledge/project-index.yaml`, `.ai/knowledge/features-overview.md`, and
  `.ai/knowledge/discovered-signals.md`.
- Benchmark score -> skill iteration: hard checks catch structural regressions;
  manual soft scores capture architecture clarity, module communication, reuse,
  ADR usefulness, and review quality.
- CLI wrapper -> core module: top-level scripts stay small and stable while
  implementation details move under `featurectl_core` and `pipelinebench_core`.

## External Integrations

The pipeline has no required network service dependency. Real Codex showcase
runners may invoke a local `codex` binary, but deterministic tests use local fake
or offline runners. Manual soft-score files are trusted local reviewer input and
are parsed as YAML data only.
