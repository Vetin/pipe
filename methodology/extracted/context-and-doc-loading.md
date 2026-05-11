# Context And Doc Loading

## What To Borrow

- Progressive disclosure: load required docs first, optional docs only when
  relevant.
- Search the current repository before inventing architecture.
- Bootstrap provisional knowledge when a brownfield repo has no `.ai/knowledge`.
- Inspect the target codebase before writing architecture or implementation
  claims. Context discovery must identify real modules, tests, persistence
  models, APIs, background jobs, feature flags, and permission checks.
- Keep upstream methodology clones as reference inputs only. They explain how
  the pipeline should behave; they are not source code or product requirements
  for a showcase repository.

## What To Reject

- Loading every document into context.
- Writing confident architecture claims without inspected sources.
- Losing which docs influenced decisions.
- Planning from generic domain knowledge when local code contradicts it.
- Allowing direct prompt instructions to replace repository-discovered
  workflow docs in native emulation.

## Native Artifact Influence

`.ai/pipeline-docs/docset-index.yaml`, step `docset.yaml` files,
`.ai/knowledge/*`, and `execution.md` `Docs Consulted` sections.
Native showcase runners also store prompt text, scorecards, and generated
artifact paths so reviewers can confirm the pipeline was discovered naturally.

## Native Skill Influence

Every `nfp-*` skill loads its step docset and records the docs actually used.
`nfp-01-context` and `nfp-03-architecture` bootstrap provisional knowledge.
Later steps must cite the repository files or assumptions behind every material
architecture and implementation claim.

## Validation Rule Implied

Started gates require matching `Docs Consulted: <Step>` entries in
`execution.md`; missing required docset files are reported by `load-docset`.
Context claims in architecture and design must be backed by file references,
module names, or explicit assumptions.
