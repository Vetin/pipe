---
name: nfp-12-promote
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 12 Promote

Use this skill to promote a completed workspace into canonical feature memory.

Responsibilities:

- validate finish state
- check canonical path conflicts
- promote the workspace to `.ai/features/<domain>/<slug>/`
- regenerate `.ai/features/index.yaml`
- archive conflicting variants only when explicitly requested

Workflow:

1. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py promote --workspace <workspace> --conflict abort
   ```

2. If a canonical feature already exists, stop by default.
3. Use `--conflict archive-as-variant` only when the user explicitly approves
   archiving the existing canonical feature as a variant.
4. Confirm `.ai/features/index.yaml` contains the promoted feature key.

Do not implement merge or replace conflict behavior in v1.
