# Feature: Artifact Readability And Execution Semantics

## Intent
Improve the human readability and operational semantics of Native Feature Pipeline artifacts after the lifecycle/source-truth hardening work.

## Motivation
The pipeline now has stronger source-of-truth rules, but several generated artifacts are still hard to inspect in raw view, execution logs mix active status with historical events, retry slice events lack structured semantics, and benchmark/profile outputs still need stronger qualitative and categorization support.

## Actors
- Codex pipeline maintainer
- Future feature-building agent
- Human reviewer reading GitHub raw diffs
- Pipeline benchmark operator

## Goals
- Keep generated YAML and Markdown readable in GitHub raw view and local diffs.
- Normalize `execution.md` into one active current-state section, one chronological event log, and one historical section.
- Formalize retry slice events with attempt number and reason.
- Mark pipeline-lab feature signals as `lab_signal` and make discovered-signal docs structured and non-empty.
- Add manual soft-score input to `pipelinebench.py`.
- Promote key pipeline architecture decisions into ADR/knowledge docs.

## Non-Goals
- Full modular split of `featurectl.py`; this feature may add seams but does not complete the extraction.
- Replacing showcase runners.
- Implementing a real LLM judge for soft scores.
- Changing the existing canonical feature index schema beyond readability and metadata needed here.

## Functional Requirements
- FR-001: Generated YAML must use block-style readable output and generated Markdown must keep major sections on separate lines.
- FR-002: Tests must detect collapsed generated YAML/Markdown and long-line regressions in source-controlled pipeline artifacts.
- FR-003: `execution.md` must have a canonical `## Current Run State`, `## Event Log`, and `## History` structure for new workspaces and promoted/finished validation.
- FR-004: Gate and slice events must be written into `## Event Log`; no event may appear after the active status section unless the status section is rewritten as the last active state.
- FR-005: Retry slice completions must include `attempt=<n>` and `reason=<text>`.
- FR-006: Duplicate slice completion validation must accept retry events only when attempt and reason are present.
- FR-007: Project profile catalog entries from `pipeline-lab` docs must use `kind: lab_signal`, not generic `detected`.
- FR-008: `.ai/knowledge/discovered-signals.md` must always be substantive: either structured discovered signals or an explicit no-signals message.
- FR-009: `pipelinebench.py` must accept a manual soft-score file and produce a scored report section.
- FR-010: Pipeline architecture decisions must be represented in `.ai/knowledge/adr-index.md` and deepened knowledge docs.

## Non-Functional Requirements
- NFR-001: Formatting checks must be deterministic and runnable offline.
- NFR-002: Execution-log validation must produce clear blocker messages.
- NFR-003: Soft scores must be optional and must not weaken hard checks.
- NFR-004: Knowledge docs should remain generated or source-linked, not hand-wavy summaries.

## Acceptance Criteria
- AC-001: `python -m pytest tests/feature_pipeline/test_artifact_formatting.py` passes and fails on intentionally collapsed fixture artifacts.
- AC-002: New feature workspaces start with `## Current Run State`, `## Event Log`, and `## History`.
- AC-003: Finished/promoted validation rejects gate/slice events outside `## Event Log` after current state.
- AC-004: `complete-slice --append-retry` fails without `--retry-reason` and logs retry events as `attempt=2 reason=...`.
- AC-005: Duplicate retry completion without attempt/reason fails validation.
- AC-006: `init --profile-project` categorizes pipeline-lab signals as `lab_signal`.
- AC-007: `discovered-signals.md` contains structured Signal/Source/Confidence/Why not canonical rows or an explicit no-signal message.
- AC-008: `pipelinebench.py score-run --soft-score-file manual-score.yaml` writes soft-score totals and comments.
- AC-009: `.ai/knowledge/adr-index.md` references promoted pipeline decisions or explicitly explains why no ADR exists.
- AC-010: Full `python -m pytest tests/feature_pipeline` passes.

## Assumptions
- Existing historical execution logs can be migrated in place without losing event evidence.
- Existing retry lines can be assigned attempt numbers during migration.
- Manual soft score files are trusted local reviewer input.

## Open Questions
- None for this implementation pass.
