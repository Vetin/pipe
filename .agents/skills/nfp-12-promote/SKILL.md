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
