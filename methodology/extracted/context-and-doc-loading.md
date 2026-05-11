# Context And Doc Loading

## What To Borrow

- Progressive disclosure: load required docs first, optional docs only when
  relevant.
- Search the current repository before inventing architecture.
- Bootstrap provisional knowledge when a brownfield repo has no `.ai/knowledge`.

## What To Reject

- Loading every document into context.
- Writing confident architecture claims without inspected sources.
- Losing which docs influenced decisions.

## Native Artifact Influence

`.ai/pipeline-docs/docset-index.yaml`, step `docset.yaml` files,
`.ai/knowledge/*`, and `execution.md` `Docs Consulted` sections.

## Native Skill Influence

Every `nfp-*` skill loads its step docset and records the docs actually used.
`nfp-01-context` and `nfp-03-architecture` bootstrap provisional knowledge.

## Validation Rule Implied

Started gates require matching `Docs Consulted: <Step>` entries in
`execution.md`; missing required docset files are reported by `load-docset`.
