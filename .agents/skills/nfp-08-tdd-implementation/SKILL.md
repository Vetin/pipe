---
name: nfp-08-tdd-implementation
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 08 TDD Implementation

Use this skill to implement slices with red-green-refactor evidence.

Responsibilities:

- record pre-red git state
- write failing test first
- store raw red, green, and verification outputs under `evidence/`
- record evidence through `featurectl.py record-evidence`
- complete slices only after evidence order is valid
- commit each completed slice or record a diff hash
