---
name: nfp-06-readiness
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 06 Readiness

Use this skill to validate planning readiness before implementation.

Responsibilities:

- run `featurectl.py validate --readiness`
- summarize blockers, assumptions, stale artifacts, and missing gates
- ask for implementation approval or stop at the requested point

Keep readiness logic in deterministic validation where practical.
