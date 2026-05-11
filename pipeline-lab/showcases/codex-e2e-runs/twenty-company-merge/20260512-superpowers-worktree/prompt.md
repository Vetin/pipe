You are a nested Codex worker running as a reproducible E2E feature implementation case.

Repository ownership:
- Work only inside this fresh feature worktree: /Users/egormasnankin/work/harness-pipeline/pipeline-lab/showcases/repos/worktrees/codex-twenty-company-merge-20260512-superpowers-worktree
- Original codebase checkout: /Users/egormasnankin/work/harness-pipeline/pipeline-lab/showcases/repos/twenty
- This repository represents the original codebase from case file: /Users/egormasnankin/work/harness-pipeline/pipeline-lab/showcases/codex-e2e-cases.yaml
- Original codebase base ref: origin/main
- Target branch name: nfp/twenty-company-merge
- Do not modify sibling repositories or harness files.
- The worktree already exists; do not implement in the base checkout.
- Preserve unrelated user changes. If unexpected dirty files are present, stop and report them.

Case:
- Case id: twenty-company-merge
- Title: Twenty Duplicate Company Merge Audit Trail
- Domain: company
- Feature request: Detect duplicate companies, preview merge effects, merge records, and keep reversible audit history.
- Expected result: Document entity relationships, conflict resolution, duplicate detection, preview, merge, audit log, and rollback-safe behavior.

Native Feature Pipeline:
- If `.agents/pipeline-core`, `.agents/skills`, `.ai/pipeline-docs`, or `skills` are missing, copy/install them from /Users/egormasnankin/work/harness-pipeline/.agents, /Users/egormasnankin/work/harness-pipeline/.ai/pipeline-docs, and /Users/egormasnankin/work/harness-pipeline/skills into this worktree before continuing.
- Treat this as a normal user feature request. Discover the repository's native pipeline instructions from `.agents`, `.ai/pipeline-docs`, and local docs; do not ask the user to invoke individual internal skills by name.
- Progress through these outcomes in order:
  - intake and repository context discovery
  - feature contract with measurable requirements and acceptance criteria
  - architecture grounded in inspected modules and system boundaries
  - technical design covering contracts, data, errors, flags, and tests
  - dependency-aware implementation slices
  - readiness gates for destructive, security, data, and public API risks
  - test-first implementation with red/green evidence
  - adversarial review and fix verification
  - final verification, feature memory, promotion, and commit
- Use local helper commands where the discovered pipeline docs point you, especially for scaffolding, validation, gate state, evidence, review, finish, and promotion.
- Use `apex.md`, `feature.yaml`, `state.yaml`, and `execution.md` to navigate and record work.
- Do not create `approvals.yaml` or `handoff.md`; approval history belongs in `execution.md`, machine gate state belongs in `state.yaml`.

Implementation expectations:
- Complete artifacts, architecture, technical design, slices, TDD implementation, review, verification, finish, promote, and commit.
- Use focused tests first, then broader validation where feasible.
- Record red/green evidence and any blocked validation with exact commands and reasons.
- Commit the finished implementation on `nfp/twenty-company-merge`.
- Final response must include branch, commit, changed files, NFP artifact paths, tests run, and known limitations.
