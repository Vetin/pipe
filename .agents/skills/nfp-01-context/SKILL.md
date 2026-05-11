---
name: nfp-01-context
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 01 Context

Use this skill to discover repository context before drafting feature behavior.

Responsibilities:

- read `apex.md`, `feature.yaml`, `state.yaml`, and `execution.md`
- inspect `.ai/knowledge`, `.ai/features`, docs, source tree, contracts, tests,
  and ADRs
- bootstrap provisional knowledge when `.ai/knowledge` is missing or sparse
- record docs consulted and context findings in `execution.md`

Do not invent architecture when repository knowledge is missing.
