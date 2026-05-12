# Feature: Clean Checkout Artifact Hygiene

## Intent

Make the pipeline's source-controlled artifacts trustworthy from a clean public
checkout and easier to consume by humans and future agents.

## Motivation

The external review still reports collapsed raw files, dense project memory,
unclear legacy evidence semantics, and monolithic CLI scripts. Local and public
raw checks show several formatting findings are stale, but the pipeline needs
harder guards and clearer artifacts so stale reviews are easy to disprove and
real drift is blocked before promotion.

## Actors

- Codex agents using `.ai/knowledge` for context discovery.
- Pipeline maintainers reviewing generated artifacts and CLI changes.
- Human reviewers inspecting public GitHub raw files.

## Goals

- Add clean-checkout/readability validation for public tree artifacts.
- Split bulky project profile examples out of canonical project index memory.
- Render discovered signals as readable canonical and noncanonical sections.
- Encode legacy evidence policy for change-label-only manifests.
- Move large CLI implementations behind importable core modules while keeping
  top-level script entrypoints stable.

## Non-Goals

- Full semantic decomposition of every `featurectl` function into separate
  domain modules.
- Changing the public CLI command names.
- Rewriting benchmark scoring behavior beyond module separation.

## Functional Requirements

- FR-001: Formatting/readability tests must verify source-controlled pipeline
  artifacts from the checked-out tree have multiple lines and no long lines.
- FR-002: Generated profile output must write bulky example lists to
  `.ai/knowledge/profile-examples.yaml`, not `.ai/knowledge/project-index.yaml`.
- FR-003: `project-index.yaml` must contain repository metadata, counts, modules,
  canonical features, feature signals, and compact feature catalog data only.
- FR-004: `discovered-signals.md` must render separate `Canonical Signals` and
  `Noncanonical Signals` sections with one signal block per entry.
- FR-005: Evidence manifests with semantic `change_label` entries and no
  `diff_hash` must explicitly declare the completion identity policy or legacy
  tolerance.
- FR-006: `featurectl.py` and `pipelinebench.py` must be thin top-level wrappers
  around importable core CLI modules.
- FR-007: Context guidance must tell agents to prefer canonical memory and ignore
  `lab_signal` unless working on pipeline-lab, benchmarks, or showcases.

## Non-Functional Requirements

- NFR-001: Existing CLI invocations must remain backward-compatible.
- NFR-002: Tests must run from the repository root without network access.
- NFR-003: Generated YAML and Markdown must remain line-based and reviewable.

## Acceptance Criteria

- AC-001: `python -m pytest tests/feature_pipeline/test_artifact_formatting.py`
  validates root artifacts and generated init/new/promote artifacts.
- AC-002: After `featurectl.py init --profile-project`,
  `.ai/knowledge/profile-examples.yaml` exists and example arrays are absent from
  `.ai/knowledge/project-index.yaml`.
- AC-003: `discovered-signals.md` contains `## Canonical Signals` and
  `## Noncanonical Signals` headings.
- AC-004: Current and legacy evidence manifests with change-label-only slices
  include explicit policy metadata.
- AC-005: Top-level `featurectl.py` and `pipelinebench.py` remain callable and
  delegate to `.agents/pipeline-core/scripts/*_core/cli.py`.
- AC-006: Full `python -m pytest tests/feature_pipeline -q` passes.

## Assumptions

- The one-line raw-file observations are stale for the current remote because
  public raw line counts are already multi-line.
- A thin-wrapper module split is acceptable as a first maintainability step.

## Open Questions

- Should a future feature fully decompose `featurectl_core.cli` into validation,
  evidence, profile, and promotion modules?
