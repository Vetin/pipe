---
name: nfp-01-context
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 01 Context

Use this skill to discover repository context before drafting feature behavior.

Methodology:

- Read `.agents/pipeline-core/references/native-skill-protocol.md`.
- Apply `methodology/extracted/upstream-pattern-map.md` as the behavioral synthesis of cloned upstream methodologies; cite patterns in `Docs Consulted:` when they influence a decision.
- Load the context docset with `featurectl.py load-docset --step context`.
- Use `methodology/extracted/context-and-doc-loading.md` and
  `.agents/pipeline-core/references/context-reuse-policy.md` to prefer real
  repository evidence over invented architecture.
- Record `Docs Consulted: Context` in `execution.md`.

Responsibilities:

- read `apex.md`, `feature.yaml`, `state.yaml`, and `execution.md`
- inspect `.ai/knowledge`, `.ai/features`, docs, source tree, contracts, tests,
  and ADRs
- bootstrap project knowledge when `.ai/knowledge` is missing, sparse, or
  clearly generic
- record docs consulted and context findings in `execution.md`

Do not invent architecture when repository knowledge is missing.

Project init profile:

- At repository root, when project knowledge is absent or generic, run:

  ```bash
  python .agents/pipeline-core/scripts/featurectl.py init --profile-project
  ```

- Read `.ai/knowledge/project-index.yaml` and `.ai/knowledge/project-snapshot.md`
  after the profile is generated.
- Treat generated knowledge as a map of sources to inspect, not as final truth.
- Before using a generated claim in feature, architecture, or design artifacts,
  verify it by reading the cited source path.

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

- `.ai/knowledge/project-index.yaml`
- `.ai/knowledge/project-snapshot.md`
- `.ai/knowledge/project-overview.md`
- `.ai/knowledge/features-overview.md`
- `.ai/knowledge/module-map.md`
- `.ai/knowledge/architecture-overview.md`
- `.ai/knowledge/testing-overview.md`
- `.ai/knowledge/contracts-overview.md`
- `.ai/knowledge/integration-map.md`

The provisional files must reference real inspected paths and must not claim
specific architecture facts without a source.

End by updating `execution.md` with a `Docs Consulted: Context` entry and
running `featurectl.py validate --workspace <workspace>`.

If automatic handoff does not happen, print:

```text
Next skill: nfp-02-feature-contract.
Continue with that skill.
```
