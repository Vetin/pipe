---
name: project-init
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# Project Init

Use this skill when the user asks for `/init`, repository onboarding, project
profiling, a project feature map, or brownfield context before feature work.
It accepts raw ideas, executive research notes, business analysis, or detailed
requirements by first grounding the repository itself.

Purpose:

- create or refresh `.ai/knowledge` from real repository files
- extract a current feature picture and source-backed module map
- make later NFP feature phases easier to run without guessing architecture
- keep generated knowledge clearly marked as provisional until sources are read

Methodology:

- Use OpenAI skill guidance: keep this as a focused repeatable workflow with a
  clear output and final checks.
- Use `methodology/extracted/upstream-pattern-map.md` for brownfield bootstrap
  rules and context-grounded phase behavior.
- Use `methodology/extracted/web-best-practices-20260512.md` for repository
  indexing, living specs, and validation-loop expectations.
- Treat generated repository indexes as maps to inspect, not as final product
  or architecture truth.

Workflow:

1. Confirm the current directory is the repository root or move to the root with
   `git rev-parse --show-toplevel`.
2. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py init --profile-project
   ```

3. Read `.ai/knowledge/project-index.yaml` and
   `.ai/knowledge/project-snapshot.md`.
4. Read `.ai/knowledge/features-overview.md`, `.ai/knowledge/module-map.md`,
   `.ai/knowledge/testing-overview.md`, `.ai/knowledge/contracts-overview.md`,
   and `.ai/knowledge/integration-map.md`.
5. Recheck the top feature catalog entries by opening at least three cited
   source paths when the repository has enough files.
6. Produce a concise project briefing for the user:
   - project identity, branch, and source counts
   - current feature picture
   - likely module boundaries
   - test and contract surfaces
   - integration/deployment surfaces
   - source confidence and follow-up risks
7. When this init is used before a feature request, append the relevant
   knowledge paths to that feature workspace `execution.md` under
   `Docs Consulted: Context`.

Quality checks:

- `.ai/knowledge/project-index.yaml` exists and has non-zero source or doc
  counts for a non-empty repository.
- `.ai/knowledge/project-index.yaml` contains `feature_catalog`.
- `.ai/knowledge/features-overview.md` contains `Current Feature Picture`.
- Every summary claim references generated knowledge or a cited repository
  source.
- No implementation code is changed by this skill.

If a repository does not yet include `.agents/pipeline-core/scripts/featurectl.py`,
install or copy the Native Feature Pipeline core first, then rerun this skill.
