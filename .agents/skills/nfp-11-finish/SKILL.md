---
name: nfp-11-finish
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 11 Finish

Use this skill to prepare feature memory and PR summary.

Responsibilities:

- validate completed slices, review, and verification evidence
- generate `feature-card.md`
- write PR summary and final execution summary
- update living documentation summaries when appropriate

Workflow:

1. Run `featurectl.py validate --workspace <workspace> --evidence`.
2. Run `featurectl.py validate --workspace <workspace> --review`.
3. Confirm `reviews/verification-review.md` and final verification output exist.
4. Write `feature-card.md` with feature key, intent, requirements, architecture
   summary, contracts, slices, tests, reviews, evidence, and future modification
   notes.
5. Update `execution.md` with final summary and PR summary.
6. Update `.ai/knowledge` summaries when appropriate.
7. Set the finish gate to `complete`.
8. Run `featurectl.py validate --workspace <workspace>`.

Do not promote canonical memory in this step; hand off to `nfp-12-promote`.
