# Feature: Core Modularity And Readable Events

## Intent

Finish the remaining post-review hardening by proving public raw output from a
fresh source, decomposing oversized control-plane modules, tightening generated
Markdown readability, and making execution/context rules easier to validate.

## Motivation

The previous public raw guardrail feature fixed the critical public rendering
issues. A follow-up review confirmed those fixes in GitHub blob view but asked
for raw `curl` and clean-clone validation, smaller core modules, stricter
documentation readability, clearer execution event structure, context-skill
rules for canonical versus lab signals, and a knowledge typo/line audit.

## Actors

- Pipeline maintainers reviewing `featurectl` and `pipelinebench` changes.
- Codex agents using context and knowledge artifacts during feature planning.
- Human reviewers validating public raw output and generated documentation.

## Goals

- Verify public raw and clean-clone behavior with recorded evidence.
- Reduce `featurectl_core/cli.py` and `pipelinebench_core/cli.py` ownership by
  extracting cohesive modules.
- Add regression tests that require extracted modules to exist and keep CLI
  modules below maintainability thresholds.
- Tighten curated Markdown line-length expectations for feature cards,
  execution logs, and knowledge docs.
- Add a structured execution event sidecar for future machine parsing while
  keeping `execution.md` readable.
- Strengthen context-skill tests around canonical memory and `lab_signal`
  consumption.
- Add explicit knowledge-doc typo and section audits.

## Non-Goals

- Rewriting all historical execution logs into YAML blocks.
- Changing public `featurectl.py` or `pipelinebench.py` command names.
- Introducing network-dependent tests in the repository test suite.
- Installing `black` or adding a new required formatter dependency.

## Functional Requirements

- FR-001: Public raw wrappers, `.gitignore`, and index line counts must be
  verified once with `curl -fsSL` and recorded in evidence.
- FR-002: A clean clone must execute both wrappers and pass
  `test_artifact_formatting.py`.
- FR-003: `featurectl_core` must expose separate modules for formatting,
  profile generation, validation, evidence, promotion, and event helpers.
- FR-004: `pipelinebench_core` must expose separate modules for scenarios,
  scoring, reports, candidates, and showcase helpers.
- FR-005: Tests must fail if `featurectl_core/cli.py` or
  `pipelinebench_core/cli.py` grows beyond agreed line-count thresholds.
- FR-006: Generated or canonical curated Markdown must have no non-table,
  non-code lines over 180 characters.
- FR-007: Knowledge docs must contain section headings and must not contain the
  typo `evidence//`.
- FR-008: The context skill must explicitly prefer canonical feature memory and
  restrict `lab_signal` usage to lab, benchmark, showcase, or validation work.
- FR-009: New feature workspaces must include a parseable `events.yaml` sidecar
  that mirrors execution event records.

## Non-Functional Requirements

- NFR-001: Existing CLI commands remain backward-compatible.
- NFR-002: All tests and validators run offline after the one-time public raw
  verification evidence is captured.
- NFR-003: Refactoring must preserve current artifact schemas and promotion
  behavior.
- NFR-004: No generated artifact may require a local absolute path.

## Acceptance Criteria

- AC-001: `python .agents/pipeline-core/scripts/featurectl.py --help` and
  `python .agents/pipeline-core/scripts/pipelinebench.py list-scenarios` pass.
- AC-002: `python -m pytest tests/feature_pipeline/test_artifact_formatting.py -q`
  passes with stricter Markdown and module-size checks.
- AC-003: `python -m pytest tests/feature_pipeline/test_context_skill_contract.py -q`
  proves canonical-versus-signal rules.
- AC-004: `python -m pytest tests/feature_pipeline/test_gates_and_evidence.py tests/feature_pipeline/test_finish_promote.py -q`
  proves `events.yaml` creation and promotion behavior.
- AC-005: `python -m pytest tests/feature_pipeline/test_pipelinebench.py -q`
  passes after the benchmark module split.
- AC-006: Full `python -m pytest tests/feature_pipeline -q` passes.
- AC-007: `git diff --check` passes.

## Assumptions

- Public raw inconsistency was caching; fresh `curl` and shallow clone have
  already shown the current public tree is readable.
- A pragmatic module split can reduce review risk without completely rewriting
  every command implementation.
- Key-value Markdown events may remain for human readability if `events.yaml`
  provides the parseable machine surface.

## Open Questions

- Should a later feature migrate historical canonical execution logs into
  `events.yaml`, or only require the sidecar for new workspaces?
