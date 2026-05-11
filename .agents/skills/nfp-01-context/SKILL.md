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

Minimum searches:

```text
find .ai/knowledge -type f
find .ai/features -type f
find docs -type f
rg "<domain>"
rg "<feature term>"
rg "ADR"
```

When knowledge is missing, create provisional knowledge files with:

```text
Status: provisional
Confidence: low | medium
Needs human review: yes
Sources inspected: ...
```

Minimum provisional files:

- `.ai/knowledge/project-overview.md`
- `.ai/knowledge/module-map.md`
- `.ai/knowledge/architecture-overview.md`

The provisional files must reference real inspected paths and must not claim
specific architecture facts without a source.

End by updating `execution.md` with a `Docs Consulted: Context` entry and
running `featurectl.py validate --workspace <workspace>`.

If automatic handoff does not happen, print:

```text
Next skill: nfp-02-feature-contract.
Continue with that skill.
```
