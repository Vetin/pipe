---
name: nfp-09-review
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 09 Review

Use this skill to run deterministic and agentic review.

Responsibilities:

- run deterministic validation through `featurectl.py validate --review`
- perform or delegate spec, code quality, security, architecture, contract, test,
  regression, and performance review according to the requested tier
- write review files under `reviews/`
- block verification for critical findings
