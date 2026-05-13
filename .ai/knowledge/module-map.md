# Module Map

Status: curated
Confidence: medium
Needs human review: yes
Last reviewed: 2026-05-13

## Pipeline Control Modules

- `.agents/pipeline-core/scripts/featurectl.py`: stable command-line entrypoint
  for the deterministic pipeline control plane.
- `.agents/pipeline-core/scripts/featurectl_core/cli.py`: argument parser and
  command dispatch for the feature control plane.
- `.agents/pipeline-core/scripts/featurectl_core/profile.py`: init tree,
  project profile, knowledge rendering, and initial workspace prose.
- `.agents/pipeline-core/scripts/featurectl_core/validation.py`: workspace and
  artifact gate validation orchestration.
- `.agents/pipeline-core/scripts/featurectl_core/validators/`: focused
  canonical memory, execution-log, and event sidecar validators.
- `.agents/pipeline-core/scripts/featurectl_core/evidence.py`: evidence
  manifest, red/green order, slice completion, and retry metadata.
- `.agents/pipeline-core/scripts/featurectl_core/events.py`: Markdown event
  rendering plus parseable `events.yaml` sidecar synchronization.
- `.agents/pipeline-core/scripts/featurectl_core/promotion.py`: canonical
  index, overview, status, latest-state, and worktree path helpers.
- `.agents/pipeline-core/scripts/featurectl_core/docsets.py`: pipeline docset
  lookup and step normalization.
- `.agents/pipeline-core/scripts/featurectl_core/formatting.py`: shared YAML
  and text writers with readable block-style serialization.
- `.agents/pipeline-core/scripts/featurectl_core/shared.py`: constants,
  git helpers, slugging, time, and workspace resolution.
- `.agents/pipeline-core/scripts/pipelinebench.py`: stable command-line
  entrypoint for benchmark scoring and reports.
- `.agents/pipeline-core/scripts/pipelinebench_core/cli.py`: benchmark argument
  parser.
- `.agents/pipeline-core/scripts/pipelinebench_core/commands.py`: benchmark
  command handlers.
- `.agents/pipeline-core/scripts/pipelinebench_core/scenarios.py`: scenario
  discovery and listing.
- `.agents/pipeline-core/scripts/pipelinebench_core/score.py`: hard checks and
  manual soft-score loading.
- `.agents/pipeline-core/scripts/pipelinebench_core/report.py`: score and
  comparison report rendering.
- `.agents/pipeline-core/scripts/pipelinebench_core/candidates.py`: candidate
  skill isolation.
- `.agents/pipeline-core/scripts/pipelinebench_core/showcases.py`: experimental
  showcase execution.
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
