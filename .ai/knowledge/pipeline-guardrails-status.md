# Pipeline Guardrails Status

Status: curated
Confidence: high
Needs human review: no
Last reviewed: 2026-05-14

## Purpose

This document records the durable checks that prove the Native Feature Pipeline
is usable from a clean checkout and that public raw artifacts are physically
multi-line files.

## Guardrail Owner

- Workflow: `Pipeline Guardrails`
- Workflow file: `.github/workflows/pipeline-guardrails.yml`
- Local command owner: `.agents/pipeline-core/scripts/pipelinebench.py`
- Raw check implementation: `.agents/pipeline-core/scripts/pipelinebench_core/raw_checks.py`

## Required Checks

- Wrapper execution:
  - `python .agents/pipeline-core/scripts/featurectl.py --help`
  - `python .agents/pipeline-core/scripts/pipelinebench.py --help`
- Compile check:
  - `python -m compileall .agents/pipeline-core/scripts`
- Artifact formatting:
  - `python -m pytest tests/feature_pipeline/test_artifact_formatting.py -q`
- Public raw check:
  - `python .agents/pipeline-core/scripts/pipelinebench.py check-public-raw --min-lines 5`

## Public Raw Thresholds

- wrapper files: more than 5 lines
- .gitignore: more than 10 lines
- .ai/features/index.yaml: more than 5 lines
- canonical `events.yaml`: more than 5 lines

## Current Local Status

The most recent local review before this feature confirmed that public raw
line counts were physically multi-line for wrappers, `.gitignore`,
`formatting.py`, `.ai/features/index.yaml`, and a canonical `events.yaml`.
The `Pipeline Guardrails` workflow was also inspected with `gh run list` and
showed the latest two runs as completed successfully.

## Review Guidance

If GitHub's rendered view and `raw.githubusercontent.com` disagree, trust a
fresh shell check over the rendered page. Use commit-specific raw URLs in CI to
avoid branch cache ambiguity.
