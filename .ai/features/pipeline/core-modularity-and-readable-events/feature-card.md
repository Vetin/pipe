# Feature Card: pipeline/core-modularity-and-readable-events

## Intent

Fix the remaining public-review findings after artifact hygiene work by proving
raw public files from a clean checkout, splitting large control-plane modules,
adding parseable execution events, and tightening knowledge-consumption rules.

## Implementation

- Split `featurectl_core/cli.py` into focused modules for shared helpers,
  formatting, docsets, profile generation, validation, evidence, events, and
  promotion.
- Split `pipelinebench_core/cli.py` into parser, command, common, scenario,
  score, report, candidate, and showcase modules.
- Added `events.yaml` sidecar support for new feature workspaces and for
  appended gate, stale, slice, retry, archive, and promotion events.
- Tightened artifact formatting tests for curated Markdown, knowledge docs,
  module-size boundaries, wrapper execution, and `.gitignore` readability.
- Added context and methodology contract tests so canonical feature memory stays
  ahead of `lab_signal` entries and execution-event features mention
  `events.yaml` in architecture and finish skills.
- Updated shared architecture, module, integration, ADR, and tech-design
  knowledge summaries with the new module and event-sidecar model.

## Slices

- S-001: public raw/readability guardrails completed.
- S-002: featurectl module split and event sidecar completed.
- S-003: pipelinebench module split completed.
- S-004: context signal consumption and knowledge updates completed.

## Tests

- `python -m pytest tests/feature_pipeline/test_artifact_formatting.py -q`
- `python -m pytest tests/feature_pipeline/test_featurectl_core.py tests/feature_pipeline/test_gates_and_evidence.py tests/feature_pipeline/test_finish_promote.py -q`
- `python -m pytest tests/feature_pipeline/test_pipelinebench.py tests/feature_pipeline/test_artifact_formatting.py -q`
- `python -m pytest tests/feature_pipeline/test_context_skill_contract.py tests/feature_pipeline/test_methodology_contract.py tests/feature_pipeline/test_artifact_formatting.py -q`
- `python -m pytest tests/feature_pipeline -q`

## Manual Validation

- `python .agents/pipeline-core/scripts/featurectl.py --help`: passed.
- `python .agents/pipeline-core/scripts/pipelinebench.py --help`: passed.
- `python .agents/pipeline-core/scripts/pipelinebench.py list-scenarios`: passed.
- `python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace> --evidence`: passed.
- `git diff --check`: passed.
- Public raw and fresh-clone checks were run during context discovery and
  recorded in `execution.md`.

## Verification Debt

None for the implemented scope. The feature intentionally leaves legacy
canonical workspaces without mandatory backfilled `events.yaml`; the sidecar is
required for new workspaces and new appended events.

## Claim Provenance

| Claim | Evidence |
| --- | --- |
| Wrappers still execute | Help smoke commands and full tests |
| Featurectl is split by responsibility | `test_artifact_formatting.py` module-boundary checks |
| Pipelinebench is split by responsibility | `test_pipelinebench.py` and module-boundary checks |
| Events are parseable | `test_featurectl_core.py` and `test_gates_and_evidence.py` |
| Canonical memory outranks lab signals | `test_context_skill_contract.py` |
| Knowledge docs are readable and typo-checked | `test_artifact_formatting.py` |

## Rollback Guidance

Revert the feature commit and remove the canonical feature path if promotion has
already happened. The stable wrappers are intentionally unchanged, so rollback
returns callers to the previous single-module internals without changing public
CLI names.

## Shared Knowledge Updates

| Knowledge file | Decision | Evidence | Future reuse |
| --- | --- | --- | --- |
| `.ai/knowledge/architecture-overview.md` | Updated | Module split and `events.yaml` sidecar | Future architecture runs see the control-plane topology |
| `.ai/knowledge/module-map.md` | Updated | Focused module ownership list | Future repair work can target the right module |
| `.ai/knowledge/integration-map.md` | Updated | Artifact/event flow update | Future validation work can use the sidecar model |
| `.ai/knowledge/adr-index.md` | Updated | ADR-005 added | Future decisions can cite module and event policy |
| `.ai/knowledge/tech-design-overview.md` | Updated | Added section heading | Formatting tests can enforce readable docs |

## Plan Drift

The implementation kept the planned four slices. The only drift was that some
module-split work landed before individual slice evidence was fully recorded;
the evidence manifest records the relevant failing and passing tests for each
slice.
