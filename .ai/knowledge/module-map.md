# Module Map

Status: curated
Confidence: medium
Needs human review: yes
Last reviewed: 2026-05-12

## Pipeline Control Modules

- `.agents/pipeline-core/scripts/featurectl.py`: stable command-line entrypoint
  for the deterministic pipeline control plane.
- `.agents/pipeline-core/scripts/featurectl_core/cli.py`: workspace, gate,
  evidence, validation, promotion, and project-profile implementation.
- `.agents/pipeline-core/scripts/pipelinebench.py`: stable command-line
  entrypoint for benchmark scoring and reports.
- `.agents/pipeline-core/scripts/pipelinebench_core/cli.py`: offline benchmark
  scoring, candidate isolation checks, showcase comparison, and manual
  soft-score report generation.
- `pipeline-lab/showcases/scripts/run_init_profile_showcases.py`: repeated
  project-init showcase runner. It reads compact project metadata from
  `project-index.yaml` and feature signal/catalog data from
  `discovered-signals.md`.
- `.agents/skills/nfp-00-intake` through `.agents/skills/nfp-12-promote`: skill
  prompts that define the human/agent workflow around the deterministic scripts.
- `.agents/skills/project-init`: repository bootstrap/profile skill, separate
  from feature-run steps.

## Knowledge Modules

- `.ai/features`: canonical feature memory promoted from completed workspaces.
- `.ai/feature-workspaces`: active and promoted-readonly run workspaces.
- `.ai/features-archive`: archived incoming variants and noncanonical runs.
- `.ai/knowledge`: retrieval layer for future agents, including canonical
  features, discovered signals, architecture, modules, integrations, tests, and
  ADR index.

## Benchmark Modules

- `pipeline-lab/benchmarks/scenarios`: deterministic benchmark scenario
  definitions.
- `pipeline-lab/scorecards`: scorecard metadata for hard and soft evaluation.
- `pipeline-lab/showcases`: curated showcase scenarios and reports.
- `tests/feature_pipeline`: regression tests for control-plane behavior,
  artifact formatting, source truth, benchmarks, evidence, review, and policy.
