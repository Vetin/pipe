# Silver Bullet Native Feature Pipeline — implementation specification for Codex

## 1. Purpose

Build a **Codex-native, multi-skill feature pipeline** that helps a repository deliver new product features in a predictable, auditable, enterprise-grade way.

The pipeline should let Codex move from a user’s feature idea to a controlled implementation while leaving behind durable artifacts that explain:

```text
why the feature exists
what behavior it promises
how it fits into the current system
which modules it communicates with
which architecture decisions were made
which contracts it exposes or consumes
which implementation slices built it
which tests proved it
which reviews challenged it
which evidence shows completion
how future agents can safely modify it
```

The system should use **Codex skills** for step-specific workflows, because Codex skills package instructions, resources, and optional scripts so Codex can follow repeatable workflows reliably. Repository-wide behavior should be guided by `AGENTS.md`, which Codex reads before doing work to apply project-specific instructions. ([OpenAI Developers][1])

Internal codename:

```text
Silver Bullet Native Feature Pipeline
```

Practical description:

```text
a predictable feature factory
a living architecture memory
a controlled agentic delivery pipeline
```

---

# 2. Core architecture

## 2.1 Design principles

Build:

```text
many focused skills
+ one shared artifact graph
+ one minimal machine state
+ one LLM-readable execution log
+ one deterministic validation layer
+ one feature worktree per feature
+ one repeatable skill evaluation loop
```

Avoid:

```text
one giant monolithic skill
multiple competing task lists
approvals duplicated across files
planning in one checkout and coding in another
a script that writes product/design prose
manual framework-bridging between BMAD, Spec Kit, OpenSpec, and Superpowers
```

## 2.2 Main building blocks

```text
AGENTS.md
  Lightweight global repository guidance.

.agents/skills/nfp-*
  Focused Codex skills, one per pipeline step.

.agents/pipeline-core/scripts/featurectl.py
  Deterministic validation and state/evidence helper.

.agents/pipeline-core/scripts/pipelinebench.py
  Benchmark and skill-power validation harness.

.ai/pipeline-docs/
  Step-specific documentation packs and alternatives.

.ai/knowledge/
  Living project, architecture, module, integration, testing, and domain documentation.

.ai/feature-workspaces/
  In-progress feature artifacts inside feature worktrees.

.ai/features/
  Canonical completed feature memory.

.ai/features-archive/
  Archived conflicting or abandoned feature variants.
```

## 2.3 Runtime ownership

```text
LLM skills own:
- intent interpretation
- clarification
- product requirements
- architecture
- technical design
- contracts
- slices
- reviews
- documentation prose
- implementation

Subagents own:
- bounded review
- challenge
- analysis
- comparison
- risk discovery

featurectl.py owns:
- scaffolding
- schema validation
- gate state
- staleness flags
- worktree checks
- evidence metadata
- evidence order validation
- promotion safety
- simple deterministic indexes

pipelinebench.py owns:
- benchmark scoring
- regression detection
- skill candidate comparison
```

Codex subagents may be used for bounded review and analysis work. They are useful for parallel exploration or specialized analysis, but they should not approve gates or mutate pipeline state by themselves. ([OpenAI Developers][2])

---

# 3. Scope

## 3.1 In scope

This specification covers **feature work**:

```text
new product capabilities
new cross-module behavior
new public or internal contracts
security-sensitive feature behavior
architecture-affecting feature delivery
```

## 3.2 Out of scope for v1

Do not implement separate pipelines for:

```text
bug fixes
refactors
migrations
security patches
performance work
dependency upgrades
maintenance work
```

These should be handled by future specifications.

Important future distinction:

```text
feature_key
  A canonical product capability, e.g. auth/reset-password.

change_key
  A specific change to a feature, e.g. auth/reset-password/token-expiry-fix.
```

This version uses only `feature_key`.

---

# 4. AGENTS.md policy

`AGENTS.md` should stay lightweight.

It should instruct Codex to use this pipeline for substantial feature work, but it should not force the full pipeline for tiny changes.

Use the pipeline for:

```text
new features
cross-module behavior changes
security-sensitive behavior
public API or contract changes
architecture-affecting feature work
large behavior-linked refactors
```

Do not require the full pipeline for:

```text
typo fixes
formatting
small test-only cleanup
one-line local bug fixes
non-behavioral documentation edits
```

Suggested `AGENTS.md` policy:

```markdown
# Repository Agent Instructions

Use the Native Feature Pipeline for substantial feature work.

For feature work:

- start with `nfp-00-intake`
- create a dedicated git worktree for the feature
- keep all feature artifacts and code changes inside that worktree
- use `apex.md`, `feature.yaml`, `state.yaml`, and `execution.md` to navigate
- use `featurectl.py` for scaffolding, validation, gate state, staleness, evidence, and promotion
- do not write implementation code until feature contract, architecture, technical design, and slicing readiness gates are approved or explicitly delegated
- record all clarifying questions, assumptions, docs consulted, approvals, scope changes, and next steps in `execution.md`

Do not use the full feature pipeline for trivial non-behavioral edits.
```

---

# 5. Worktree-first rule

Every feature starts in a new git worktree.

Git worktrees let one repository support multiple working trees, so more than one branch can be checked out at a time. This makes them a good fit for isolating feature work and agent activity. ([Git][3])

## 5.1 Flow

```text
User asks for a feature
→ Codex runs nfp-00-intake
→ featurectl.py creates feature branch and worktree
→ Codex changes directory into the worktree
→ Codex creates all .ai/feature-workspaces artifacts inside the worktree
→ planning, implementation, tests, reviews, evidence, and commits happen inside the worktree
```

## 5.2 Naming

Feature key:

```text
auth/reset-password
```

Branch:

```text
feature/auth-reset-password-run-20260504-k7p9
```

Worktree:

```text
../worktrees/auth-reset-password-run-20260504-k7p9
```

Workspace inside the worktree:

```text
.ai/feature-workspaces/auth/reset-password--run-20260504-k7p9/
```

## 5.3 Rules

```text
Do not create feature planning artifacts in the main checkout.
Do not write implementation code outside the feature worktree.
Do not commit the worktree directory itself; it is an external checkout.
Feature workspace artifacts may be committed on the feature branch.
Benchmark run outputs are normally ignored.
```

---

# 6. Feature identity

Do not use global numeric feature IDs like:

```text
F001
F002
F003
```

Use semantic feature keys:

```text
<domain>/<feature-slug>
```

Examples:

```text
auth/reset-password
auth/email-verification
billing/subscription-upgrade
notifications/email-digest
admin/user-invites
```

Canonical feature path:

```text
.ai/features/<domain>/<feature-slug>/
```

In-progress feature workspace path:

```text
.ai/feature-workspaces/<domain>/<feature-slug>--<run-id>/
```

Feature-scoped local IDs are allowed:

```text
FR-001
NFR-001
AC-001
ADR-001
S-001
```

Cross-feature references must include the feature key:

```text
auth/reset-password#FR-001
auth/reset-password#ADR-001
auth/reset-password#S-001
```

---

# 7. Repository structure

```text
repo/
  AGENTS.md
  .gitignore

  methodology/
    upstream/
      BMAD-METHOD/
      spec-kit/
      OpenSpec/
      superpowers/
    docs-snapshots/
      kiro/
      cursor/
      windsurf/
      roo-code/
      agent-skills/
      ears/
      constitutional-sdd/
    README.md
    UPSTREAM_LOCK.md
    LICENSE_REVIEW.md
    extracted/
      methodology-summary.md
      artifact-model.md
      workflow-and-gates.md
      context-and-doc-loading.md
      review-and-verification.md
      evaluation-patterns.md

  .ai/
    constitution.md

    knowledge/
      project-overview.md
      features-overview.md
      architecture-overview.md
      tech-design-overview.md
      contracts-overview.md
      testing-overview.md
      adr-index.md
      module-map.md
      integration-map.md
      domains/
        <domain>/
          overview.md

    pipeline-docs/
      README.md
      docset-index.yaml
      global/
        coding-standards.md
        testing-standards.md
        security-standards.md
        review-standards.md
        architecture-standards.md
      steps/
        intake/
          docset.yaml
          overview.md
          checklist.md
          alternatives/
        context/
          docset.yaml
          overview.md
          checklist.md
          alternatives/
        feature-contract/
          docset.yaml
          overview.md
          checklist.md
          alternatives/
        architecture/
          docset.yaml
          overview.md
          checklist.md
          alternatives/
        tech-design/
          docset.yaml
          overview.md
          checklist.md
          alternatives/
        slicing/
          docset.yaml
          overview.md
          checklist.md
          alternatives/
        readiness/
          docset.yaml
          overview.md
          checklist.md
          alternatives/
        worktree/
          docset.yaml
          overview.md
          checklist.md
          alternatives/
        tdd-implementation/
          docset.yaml
          overview.md
          checklist.md
          alternatives/
        review/
          docset.yaml
          overview.md
          checklist.md
          alternatives/
        verification/
          docset.yaml
          overview.md
          checklist.md
          alternatives/
        finish/
          docset.yaml
          overview.md
          checklist.md
          alternatives/
        promote/
          docset.yaml
          overview.md
          checklist.md
          alternatives/

    feature-workspaces/
      <domain>/
        <feature-slug>--<run-id>/
          apex.md
          feature.yaml
          state.yaml
          execution.md
          feature.md
          architecture.md
          tech-design.md
          slices.yaml
          scope-change.md
          feature-card.md
          adrs/
          diagrams/
          contracts/
          reviews/
          evidence/

    features/
      index.yaml
      overview.md
      <domain>/
        <feature-slug>/
          apex.md
          feature.yaml
          state.yaml
          execution.md
          feature.md
          architecture.md
          tech-design.md
          slices.yaml
          feature-card.md
          adrs/
          diagrams/
          contracts/
          reviews/
          evidence/

    features-archive/
      <domain>/
        <feature-slug>/
          <run-id>/

  .agents/
    pipeline-core/
      references/
        artifact-requirements.md
        workflow-state-machine.md
        feature-identity-policy.md
        gate-policy.md
        documentation-loading-policy.md
        quality-rubric.md
        context-reuse-policy.md
        subagent-review-policy.md
        skill-power-validation-policy.md
        generated-templates/
      scripts/
        featurectl.py
        pipelinebench.py
        schemas/
          feature.schema.json
          state.schema.json
          slices.schema.json
          index.schema.json
          docset.schema.json
          review.schema.json
          evidence.schema.json
          benchmark.schema.json
          evaluation-result.schema.json

    skills/
      nfp-00-intake/
        SKILL.md
        agents/openai.yaml
      nfp-01-context/
        SKILL.md
        agents/openai.yaml
      nfp-02-feature-contract/
        SKILL.md
        agents/openai.yaml
      nfp-03-architecture/
        SKILL.md
        agents/openai.yaml
      nfp-04-tech-design/
        SKILL.md
        agents/openai.yaml
      nfp-05-slicing/
        SKILL.md
        agents/openai.yaml
      nfp-06-readiness/
        SKILL.md
        agents/openai.yaml
      nfp-07-worktree/
        SKILL.md
        agents/openai.yaml
      nfp-08-tdd-implementation/
        SKILL.md
        agents/openai.yaml
      nfp-09-review/
        SKILL.md
        agents/openai.yaml
      nfp-10-verification/
        SKILL.md
        agents/openai.yaml
      nfp-11-finish/
        SKILL.md
        agents/openai.yaml
      nfp-12-promote/
        SKILL.md
        agents/openai.yaml

    skill-lab/
      quarantine/
        <skill-name>/
          <candidate-version>/
            SKILL.candidate.md
            notes.md
            expected-improvement.md
      accepted/
        <skill-name>/
          <version>/
            SKILL.candidate.md
            evaluation-summary.md
      rejected/
        <skill-name>/
          <version>/
            SKILL.candidate.md
            rejection-summary.md

  pipeline-lab/
    README.md
    benchmarks/
      scenarios/
      suites/
    envs/
      toy-monolith/
      modular-api/
    runs/
    scorecards/

  tests/
    feature_pipeline/
```

---

# 8. Commit and ignore policy

Add `.gitignore` rules:

```gitignore
pipeline-lab/runs/
.ai/logs/
*.tmp
```

Usually committed:

```text
.agents/
.ai/pipeline-docs/
.ai/knowledge/
.ai/features/
methodology/extracted/
methodology/README.md
methodology/UPSTREAM_LOCK.md
methodology/LICENSE_REVIEW.md
```

Feature branches may commit:

```text
.ai/feature-workspaces/
```

Usually not committed:

```text
pipeline-lab/runs/
.ai/logs/
temporary files
```

Raw evidence logs may be committed when they are part of feature audit evidence.

---

# 9. Source-of-truth model

| Artifact                        | Source-of-truth role                                                                           |
| ------------------------------- | ---------------------------------------------------------------------------------------------- |
| `feature.yaml`                  | Feature identity, run ID, branch, worktree, paths, artifact contract version.                  |
| `state.yaml`                    | Minimal machine state: current step, gate statuses, stale flags, active slice, worktree info.  |
| `execution.md`                  | Human/LLM run journal: plan, approvals, docs consulted, decisions, scope changes, next action. |
| `apex.md`                       | Routing file telling Codex which files to read and where artifacts live.                       |
| `feature.md`                    | Product motivation, requirements, acceptance criteria, assumptions, risks.                     |
| `architecture.md` + `adrs/`     | System design, module communication, diagrams, architecture decisions.                         |
| `tech-design.md` + `contracts/` | Implementation design, module responsibilities, interfaces, schemas, test strategy.            |
| `slices.yaml`                   | TDD execution plan.                                                                            |
| `evidence/`                     | Raw command outputs and evidence manifest.                                                     |
| `reviews/`                      | Review findings and review summaries.                                                          |
| `feature-card.md`               | LLM-friendly retrieval summary generated by finish skill.                                      |
| `.ai/features/index.yaml`       | Deterministic canonical feature registry generated during promotion.                           |
| `.ai/knowledge/*`               | Living documentation maintained by finish/promote skills.                                      |

Do **not** create:

```text
approvals.yaml
handoff.md
```

Approval and handoff information belongs in `execution.md`. Gate state belongs in `state.yaml`.

---

# 10. Core artifacts

## 10.1 `apex.md`

Purpose:

```text
Route Codex to the correct files without duplicating content.
```

Example:

```markdown
# Apex: auth/reset-password

## Read Order

1. `feature.yaml` — identity and paths
2. `state.yaml` — machine state
3. `execution.md` — run plan, approvals, docs consulted, next step
4. `feature.md` — product contract
5. `architecture.md` — system design
6. `tech-design.md` — implementation design
7. `slices.yaml` — TDD execution plan
8. `evidence/manifest.yaml` — evidence index
9. `reviews/` — review results

## Main Artifacts

- Feature contract: `feature.md`
- Architecture: `architecture.md`
- Technical design: `tech-design.md`
- Implementation plan: `slices.yaml`
- ADRs: `adrs/`
- Contracts: `contracts/`
- Evidence: `evidence/`
- Reviews: `reviews/`
- Execution log: `execution.md`

## Current Status

See `state.yaml`.

## Next Action

See `execution.md`.
```

`featurectl.py` may scaffold or update `apex.md` because it is a routing file, not product/design prose.

---

## 10.2 `feature.yaml`

Purpose:

```text
Feature identity and paths.
```

Example:

```yaml
artifact_contract_version: '0.1.0'
feature_key: 'auth/reset-password'
domain: 'auth'
slug: 'reset-password'
title: 'Reset Password'
status: 'draft'
run_id: 'run-20260504-k7p9'
branch: 'feature/auth-reset-password-run-20260504-k7p9'
worktree: '../worktrees/auth-reset-password-run-20260504-k7p9'
canonical_path: '.ai/features/auth/reset-password'
workspace_path: '.ai/feature-workspaces/auth/reset-password--run-20260504-k7p9'
aliases:
  - 'forgot password'
  - 'password recovery'
keywords:
  - 'auth'
  - 'password'
  - 'email'
  - 'token'
created_at: '...'
updated_at: '...'
```

---

## 10.3 `state.yaml`

Purpose:

```text
Minimal machine-readable workflow state.
```

Example:

```yaml
artifact_contract_version: '0.1.0'

feature_key: 'auth/reset-password'
run_id: 'run-20260504-k7p9'

current_step: 'architecture'

worktree:
  branch: 'feature/auth-reset-password-run-20260504-k7p9'
  path: '../worktrees/auth-reset-password-run-20260504-k7p9'

gates:
  feature_contract: 'approved'
  architecture: 'drafted'
  tech_design: 'pending'
  slicing_readiness: 'pending'
  implementation: 'blocked'
  review: 'pending'
  verification: 'pending'
  finish: 'pending'

stale:
  feature: false
  architecture: false
  tech_design: false
  slices: false
  evidence: false
  feature_card: true
  canonical_docs: true

active_slice: null

locks:
  owner: null
  acquired_at: null
```

Allowed gate states:

```text
pending
drafted
approved
delegated
blocked
reopened
stale
complete
```

---

## 10.4 `execution.md`

Purpose:

```text
LLM-readable run plan, event log, approval log, and handoff record.
```

It must include:

```text
current user request
run plan
steps to run
stop point
automation/delegation boundaries
non-delegable checkpoints
clarifying questions
assumptions
docs consulted
gate events
scope changes
current step
next step
blocking issues
completed work summary
```

Example:

```markdown
# Execution Log: auth/reset-password

## User Request

Build reset password. Users request reset by email, receive a link, set a new password, and then log in again.

## Run Plan

Mode: planning autorun
Stop point: implementation plan
Implementation allowed: no

Planned steps:

1. Context discovery
2. Feature contract
3. Architecture
4. Technical design
5. Slicing
6. Readiness summary

## Non-Delegable Checkpoints

Stop and ask user before:

- destructive command
- production data migration
- new production dependency
- public API breaking change
- security model change
- credential/secret handling
- paid external service
- license-impacting dependency

## Clarifying Questions

None currently blocking.

## Assumptions

- Email service exists.
- Password policy is defined elsewhere.

## Docs Consulted

### Context step

- `.ai/knowledge/project-overview.md`: identified auth domain.
- `src/auth/`: found login and session modules.

### Architecture step

- `.ai/knowledge/architecture-overview.md`: reused service-boundary rule.
- `.ai/knowledge/adr-index.md`: reused token hashing decision from email verification.

## Gate Events

- feature_contract: approved by user at ...
- architecture: drafted at ...

## Scope Changes

None.

## Current Step

architecture

## Next Step

nfp-04-tech-design

## Summary

Feature contract is approved. Architecture draft created. Next step is technical design.
```

If automatic skill handoff does not happen, Codex must print:

```text
Next skill: nfp-04-tech-design.
Continue with that skill.
```

---

## 10.5 `feature.md`

Purpose:

```text
Product and behavior contract.
```

Should include:

```text
intent
motivation
actors/users
problem
goals
non-goals
related existing features
functional requirements
non-functional requirements
acceptance criteria
product risks
assumptions
open questions
```

Acceptance criteria should be testable and may use EARS-like wording.

---

## 10.6 `architecture.md`

Purpose:

```text
System-level design and module communication model.
```

Should include:

```text
how the feature fits into the system
module/component interactions
communication with other features/modules
system context
component diagrams
sequence or data-flow diagrams
security model
failure modes
observability
rollback strategy
architecture risks
links to ADRs
```

Architecture/design boundary:

```text
architecture.md
  system shape, module communication, tradeoffs, ADRs

tech-design.md
  implementation details, contracts, data model, functions/classes, tests
```

---

## 10.7 `adrs/`

Purpose:

```text
Architecture decision records.
```

Create ADRs only for decisions that are:

```text
hard to reverse
cross-module
security-sensitive
contract-affecting
performance/cost significant
a deliberate divergence from an existing pattern
```

Do not create ADRs for every minor implementation choice.

Each ADR should capture:

```text
decision
context
alternatives
tradeoffs
consequences
related requirements
related modules
related slices
superseded decisions, if any
```

---

## 10.8 `tech-design.md`

Purpose:

```text
Implementation-level design.
```

Should include:

```text
implementation summary
modules and responsibilities
public/internal contracts
API/event/schema details
core code sketches
data model
error handling
security considerations
test strategy
migration plan
rollback plan
integration notes
```

---

## 10.9 `contracts/`

Purpose:

```text
Machine-readable or structured contracts.
```

Supported contract styles:

```text
OpenAPI
JSON Schema
event schemas
protobuf
GraphQL schema
database migration notes
internal module interface descriptions
```

Do not assume every project uses OpenAPI.

---

## 10.10 `slices.yaml`

Purpose:

```text
TDD execution plan.
```

Each slice must include:

```text
slice ID
title
linked requirements
linked acceptance criteria
linked ADRs if relevant
linked contracts if relevant
dependencies
priority
expected touchpoints
scope confidence
failing test file
red command
expected failure
green command
verification commands
review focus
evidence status
status
```

Do **not** use hard `allowed_files` / `forbidden_files` enforcement in v1.

Use expected touchpoints instead:

```yaml
id: 'S-001'
title: 'Create password reset token model'
linked_requirements:
  - 'FR-003'
  - 'FR-004'
linked_acceptance_criteria:
  - 'AC-003'
linked_adrs:
  - 'ADR-001'
expected_touchpoints:
  - 'src/auth/password-reset-service.ts'
  - 'tests/auth/password-reset.test.ts'
scope_confidence: 'medium'
tdd:
  failing_test_file: 'tests/auth/password-reset.test.ts'
  red_command: 'pnpm test tests/auth/password-reset.test.ts'
  expected_failure: 'Password reset token model is not implemented'
  green_command: 'pnpm test tests/auth/password-reset.test.ts'
verification_commands:
  - 'pnpm lint'
  - 'pnpm typecheck'
review_focus:
  - 'Token cannot be reused'
  - 'Token expiry is enforced'
status: 'pending'
```

---

## 10.11 `evidence/`

Purpose:

```text
Raw audit evidence for TDD, verification, review, and completion.
```

Structure:

```text
evidence/
  manifest.yaml
  S-001/
    00-pre-red-git-state.txt
    01-red-command.txt
    01-red-output.log
    02-pre-green-git-state.txt
    03-green-command.txt
    03-green-output.log
    04-verification-command.txt
    04-verification-output.log
    05-review-summary.md
```

`manifest.yaml` example:

```yaml
artifact_contract_version: '0.1.0'
feature_key: 'auth/reset-password'

slices:
  S-001:
    red:
      command_file: 'S-001/01-red-command.txt'
      output_file: 'S-001/01-red-output.log'
      timestamp: '...'
      git_state_file: 'S-001/00-pre-red-git-state.txt'
    green:
      command_file: 'S-001/03-green-command.txt'
      output_file: 'S-001/03-green-output.log'
      timestamp: '...'
      git_state_file: 'S-001/02-pre-green-git-state.txt'
    verification:
      output_file: 'S-001/04-verification-output.log'
    review:
      summary_file: 'S-001/05-review-summary.md'
    commit: 'abc1234'
```

`complete-slice` must verify:

```text
red evidence exists
green evidence exists
verification evidence exists
review evidence exists
red timestamp is before green timestamp
raw output files exist
pre-red git state exists
commit or diff hash exists
```

---

# 11. Step documentation loading

Each skill loads a step docset.

Command:

```bash
python .agents/pipeline-core/scripts/featurectl.py load-docset \
  --workspace <workspace-path> \
  --step architecture
```

The command lists:

```text
required docs
optional docs
missing docs
selected alternatives
suggested related files
```

But it cannot prove Codex actually used those docs.

Therefore, every skill must write a **Docs Consulted** section in `execution.md`:

```markdown
## Docs Consulted: Architecture

- `.ai/knowledge/architecture-overview.md`
  - Used service boundary rule: Auth API owns auth flows.
- `.ai/knowledge/adr-index.md`
  - Reused ADR about hashing secret tokens.
- `.ai/features/auth/email-verification/architecture.md`
  - Reused EmailService interaction pattern.
```

Docset budget example:

```yaml
max_related_features: 5
max_doc_chars: 60000
required_docs_first: true
summarize_large_docs: true
```

---

# 12. Knowledge bootstrap

If `.ai/knowledge` is missing or empty, the pipeline must not invent architecture.

The context and architecture skills must bootstrap provisional knowledge by inspecting:

```text
README files
docs/
package manifests
source directory structure
module/package names
existing tests
existing APIs/contracts
existing ADRs, if any
```

Then write provisional files such as:

```text
.ai/knowledge/project-overview.md
.ai/knowledge/module-map.md
.ai/knowledge/architecture-overview.md
```

Each provisional file must include:

```text
Status: provisional
Confidence: low | medium
Needs human review: yes
Sources inspected: ...
```

This supports new repositories and brownfield repositories without existing architecture docs.

---

# 13. Methodology references

## 13.1 MVP references

Clone first:

```text
BMAD-METHOD
spec-kit
OpenSpec
superpowers
```

Later references:

```text
aidlc-workflows
specs.md
shotgun
get-shit-done
ccpm
claude-task-master
```

Docs snapshots later:

```text
kiro
cursor
windsurf
roo-code
agent-skills
ears
constitutional-sdd
```

## 13.2 Extraction docs

Keep extraction simple:

```text
methodology/extracted/methodology-summary.md
methodology/extracted/artifact-model.md
methodology/extracted/workflow-and-gates.md
methodology/extracted/context-and-doc-loading.md
methodology/extracted/review-and-verification.md
methodology/extracted/evaluation-patterns.md
```

Each should answer:

```text
what to borrow
what to reject
which native artifact it influences
which native skill it influences
which validation rule it implies
```

---

# 14. Template synthesis

Do not hardcode long templates in this specification.

Generate concise native templates after methodology extraction:

```text
feature-template.md
architecture-template.md
tech-design-template.md
adr-template.md
slice-template.yaml
review-template.md
feature-card-template.md
feature-yaml-template.yaml
apex-template.md
execution-template.md
docset-template.yaml
benchmark-scenario-template.yaml
scorecard-template.yaml
```

Templates must be:

```text
validation-friendly
feature-key aware
local-ID aware
project-agnostic
not direct copies of upstream files
small enough for repeated Codex use
clear about required vs optional sections
```

---

# 15. Skills

Each production skill must include version metadata:

```yaml
name: nfp-03-architecture
version: '0.1.0'
pipeline_contract_version: '0.1.0'
```

## 15.1 Shared skill rules

Every skill must:

```text
1. Confirm it is running inside the feature worktree.
2. Read `apex.md`.
3. Read `feature.yaml`.
4. Read `state.yaml`.
5. Read `execution.md`.
6. Load its step docset.
7. Record docs actually used in `execution.md`.
8. Update only its owned artifacts.
9. Call `featurectl.py validate`.
10. Update `state.yaml` only through `featurectl.py`.
11. Update `execution.md` with completed work and next step.
12. Print the next skill if automatic handoff does not happen.
```

Every skill must avoid:

```text
writing implementation code before implementation is allowed
skipping blocking clarification questions
silently creating assumptions for security/business-critical ambiguity
silently changing approved upstream artifacts
continuing after a non-delegable checkpoint
treating drafted artifacts as approved
```

---

## 15.2 `nfp-00-intake`

Purpose:

```text
Start a new feature run.
```

Owns:

```text
worktree creation
feature workspace creation
apex.md scaffold
feature.yaml scaffold
state.yaml scaffold
execution.md scaffold
```

Responsibilities:

```text
parse user request
infer domain and feature key, or ask if unclear
create branch and worktree
create feature workspace inside worktree
initialize apex.md, feature.yaml, state.yaml, execution.md
write initial run plan in execution.md
identify user-requested stop point
identify automation/delegation boundaries
write non-delegable checkpoints
set current_step to context
```

Must stop if:

```text
domain is unclear
feature intent is too ambiguous
user asks for full automation without delegation boundaries
security/business-critical ambiguity exists
```

No implementation code is allowed in this step.

---

## 15.3 `nfp-01-context`

Purpose:

```text
Discover existing context before drafting.
```

This is an LLM skill, not a `featurectl.py search-context` command.

Responsibilities:

```text
read .ai/knowledge if present
search existing .ai/features
search docs/
search source tree
search package/module names
search contracts and ADRs
identify related features, modules, contracts, tests, and decisions
record findings in execution.md
bootstrap provisional knowledge if needed
```

Suggested search techniques:

```text
rg "<domain>"
rg "<feature-term>"
rg "ADR"
find .ai/features -type f
find docs -type f
git grep "<module or contract name>"
inspect package/module structure
```

---

## 15.4 `nfp-02-feature-contract`

Purpose:

```text
Create the product and behavior contract.
```

Owns:

```text
feature.md
```

Responsibilities:

```text
ask blocking questions when needed
draft motivation and intent
define actors/users
define goals and non-goals
define functional requirements
define non-functional requirements
define acceptance criteria
record assumptions
record related existing features
record product risks
```

Planning automation may continue with assumptions only if:

```text
assumptions are explicit
no security-critical ambiguity exists
no business-critical ambiguity exists
readiness will surface assumption risk
```

Gate:

```text
feature_contract
```

---

## 15.5 `nfp-03-architecture`

Purpose:

```text
Create system architecture and communication model.
```

Owns:

```text
architecture.md
adrs/
diagrams/
```

Responsibilities:

```text
read context findings
read architecture overview if available
read ADR index if available
read related feature architecture docs
describe how feature fits current system
describe module/component communication
create diagrams
create ADRs only for significant decisions
describe security model
describe failure modes
describe observability
describe rollback strategy
```

---

## 15.6 `nfp-04-tech-design`

Purpose:

```text
Create implementation design and contracts.
```

Owns:

```text
tech-design.md
contracts/
```

Responsibilities:

```text
describe modules and responsibilities
describe APIs/events/schemas/internal contracts
include high-level code sketches
define data model if relevant
define error handling
define security considerations
define test strategy
define migration/rollback if relevant
```

---

## 15.7 `nfp-05-slicing`

Purpose:

```text
Create TDD execution slices.
```

Owns:

```text
slices.yaml
```

Responsibilities:

```text
create slices.yaml
link every slice to requirements and acceptance criteria
link ADRs and contracts where relevant
define dependencies and priorities
define expected touchpoints
define red command, expected failure, green command
define verification commands
define review focus
```

Do not add `allowed_files` / `forbidden_files` in v1.

---

## 15.8 `nfp-06-readiness`

Purpose:

```text
Validate that planning is ready for implementation.
```

This skill must stay simple.

Responsibilities:

```text
call featurectl.py validate --readiness
summarize blockers
summarize assumptions
summarize stale artifacts
summarize missing gates
ask for implementation approval or stop at user-requested point
```

Most readiness logic belongs in `featurectl.py validate`.

---

## 15.9 `nfp-07-worktree`

Purpose:

```text
Confirm worktree status and implementation readiness.
```

The worktree is normally created by intake. This skill verifies:

```text
current directory is the feature worktree
branch is correct
state.yaml worktree path is correct
planning gates allow implementation
git status is acceptable
```

Implementation may start only if these gates are approved or delegated:

```text
feature_contract
architecture
tech_design
slicing_readiness
```

---

## 15.10 `nfp-08-tdd-implementation`

Purpose:

```text
Implement slices with real red-green-refactor evidence.
```

For each slice:

```text
1. record pre-red git state
2. write failing test first
3. run red command
4. store raw red output in evidence/
5. record red evidence in evidence manifest
6. implement minimal code
7. run green command
8. store raw green output in evidence/
9. run verification commands
10. store raw verification output in evidence/
11. commit slice or record diff hash
12. complete slice only if evidence order is valid
```

If implementation reveals that the plan is wrong, use the scope-change mechanism.

---

## 15.11 Scope-change mechanism

If the plan becomes wrong during implementation:

```text
1. Stop implementation.
2. Write or update `scope-change.md`.
3. Explain what changed and why.
4. Mark affected artifacts stale with `featurectl.py mark-stale`.
5. Return to the correct earlier skill:
   - feature contract if behavior changed
   - architecture if system/module decisions changed
   - tech design if implementation approach changed
   - slicing if only task breakdown changed
6. Ask user approval if scope expands.
```

`scope-change.md` should include:

```text
reason
affected requirements
affected architecture/tech design
affected slices
risk
recommended return step
```

---

## 15.12 `nfp-09-review`

Purpose:

```text
Run deterministic and agentic review.
```

### Deterministic review

Handled by:

```text
featurectl.py validate
```

Checks:

```text
schemas valid
required files exist
gates satisfied
evidence order valid
completed slices have evidence
raw logs exist
critical review files block verification
```

### Agentic review

Handled by `nfp-09-review` and optional subagents.

Review tiers:

```text
basic_review
  spec compliance
  code quality

strict_review
  basic_review
  security review
  contract review
  test quality review

enterprise_review
  strict_review
  performance review
  regression risk review
  architecture compliance review
```

Fallback if subagents are unavailable:

```text
run sequential review prompts in the main agent
write review files in the same schema
```

Critical findings block verification.

---

## 15.13 `nfp-10-verification`

Purpose:

```text
Run final verification.
```

Responsibilities:

```text
read verification commands from .ai/constitution.md
run tests
run lint
run typecheck
run build
run contract/security checks if configured
store raw output in evidence/
write verification review
```

---

## 15.14 `nfp-11-finish`

Purpose:

```text
Prepare PR summary and feature memory draft.
```

Owns:

```text
feature-card.md
reviews/verification-review.md
PR summary
.ai/knowledge updates, if appropriate
```

Responsibilities:

```text
validate slices complete
validate reviews passed
validate verification evidence
generate/update feature-card.md
update execution.md summary
write PR summary
update living documentation as LLM-authored summaries
```

There is no `featurectl.py refresh-overviews`. Documentation prose is written by skills.

---

## 15.15 `nfp-12-promote`

Purpose:

```text
Promote completed feature workspace to canonical feature memory.
```

Responsibilities:

```text
validate finish state
check canonical path conflict
move/copy workspace to .ai/features/<domain>/<slug>/
update feature.yaml status
regenerate .ai/features/index.yaml deterministically
archive conflicting variants safely
```

For v1, promotion conflict options are only:

```text
abort
archive-as-variant
```

Do not implement:

```text
merge
replace
```

until a separate policy exists.

Archived variants go to:

```text
.ai/features-archive/<domain>/<feature-slug>/<run-id>/
```

---

# 16. Gates and safety

## 16.1 Required implementation gates

Implementation is blocked unless these are approved or delegated:

```text
feature_contract
architecture
tech_design
slicing_readiness
```

## 16.2 Non-delegable checkpoints

Even with full automation, Codex must stop for explicit user approval before:

```text
destructive commands
production data migrations
new production dependency
new paid/external service
credential or secret handling
permission/security model change
public API breaking change
license-impacting dependency
```

## 16.3 Gate events

Gate changes are made through:

```bash
python .agents/pipeline-core/scripts/featurectl.py gate set \
  --workspace <path> \
  --gate architecture \
  --status approved \
  --by user \
  --note "Approved after review."
```

This updates `state.yaml` and appends a structured event to `execution.md`.

---

# 17. Staleness rules

```text
feature.md changed
  → architecture stale
  → tech_design stale
  → slices stale
  → evidence stale
  → feature_card stale
  → canonical_docs stale

architecture.md, ADRs, or diagrams changed
  → tech_design stale
  → slices stale
  → evidence stale
  → feature_card stale
  → canonical_docs stale

tech-design.md or contracts changed
  → slices stale
  → evidence stale
  → feature_card stale
  → canonical_docs stale

slices.yaml changed
  → evidence stale
  → review stale
  → feature_card stale
  → canonical_docs stale

feature.yaml changed
  → index stale
```

Implementation cannot continue while required upstream artifacts are stale.

---

# 18. `featurectl.py`

`featurectl.py` is deterministic. It must not write narrative product/design/review content.

## 18.1 It may write

```text
scaffolds
routing files
schema-valid YAML state
gate events
staleness flags
evidence manifests
raw command output files
deterministic indexes
promotion/archive movements
```

## 18.2 It must not write

```text
feature requirements
architecture prose
technical design prose
contracts content
review reasoning
PR summaries
living documentation prose
```

## 18.3 MVP commands

```text
init
new
status
load-docset
validate
gate
mark-stale
record-evidence
complete-slice
worktree-status
promote
```

## 18.4 Command responsibilities

### `init`

Creates base directories and initial minimal files.

### `new`

Creates branch, worktree, and feature workspace.

```bash
python .agents/pipeline-core/scripts/featurectl.py new \
  --domain auth \
  --title "Reset Password"
```

Creates:

```text
../worktrees/auth-reset-password-run-...
.ai/feature-workspaces/auth/reset-password--run-.../
apex.md
feature.yaml
state.yaml
execution.md
```

### `status`

Prints:

```text
feature key
worktree path
current step
gate statuses
stale flags
blocking issues
next step from execution.md, if present
```

### `load-docset`

Lists required/optional/missing docs for a step.

### `validate`

Modes:

```bash
featurectl.py validate --workspace <path>
featurectl.py validate --workspace <path> --readiness
featurectl.py validate --workspace <path> --implementation
featurectl.py validate --workspace <path> --evidence
featurectl.py validate --workspace <path> --review
```

Checks:

```text
required files exist
schemas are valid
current step is legal
gates are compatible with current step
stale artifacts do not block current action
slices have TDD gates
evidence order is valid
critical review findings block verification
current directory matches feature worktree
```

### `gate`

Sets a gate state and appends event to `execution.md`.

### `mark-stale`

Marks downstream artifacts stale.

### `record-evidence`

Writes raw outputs into `evidence/` and updates `evidence/manifest.yaml`.

### `complete-slice`

Validates evidence order and marks a slice complete.

### `worktree-status`

Verifies the current checkout is the feature worktree.

### `promote`

Promotes a feature workspace into canonical feature memory.

Allowed v1 conflict behavior:

```text
abort
archive-as-variant
```

---

# 19. Schemas and versions

Every machine-readable artifact should include:

```yaml
artifact_contract_version: '0.1.0'
```

Required schemas:

```text
feature.schema.json
state.schema.json
slices.schema.json
index.schema.json
docset.schema.json
review.schema.json
evidence.schema.json
benchmark.schema.json
evaluation-result.schema.json
```

Important validation targets:

```text
feature.schema.json
  feature_key, domain, slug, run_id, paths, artifact_contract_version

state.schema.json
  current_step, gates, stale flags, worktree info

slices.schema.json
  requirement links, AC links, red command, expected failure, green command, verification commands

evidence.schema.json
  raw output file references, timestamps, git state files, commit/diff hash

review.schema.json
  severity, finding, artifact, evidence, recommendation, blocking status

index.schema.json
  semantic feature keys, paths, related features, ADR references

benchmark.schema.json
  scenario, env, expected artifacts, hard checks, soft score criteria
```

Future support:

```text
featurectl.py migrate-artifacts
```

This is not MVP, but schema evolution must be expected.

---

# 20. Review policy

Review is split into deterministic and agentic layers.

## 20.1 Deterministic validation

Handled by:

```text
featurectl.py validate
```

Catches:

```text
missing artifacts
invalid schemas
missing gates
stale artifacts
missing evidence
invalid evidence order
critical review blocking
wrong worktree
```

## 20.2 Agentic review

Handled by:

```text
nfp-09-review
```

Possible reviewers:

```text
spec compliance reviewer
code quality reviewer
security reviewer
architecture compliance reviewer
contract reviewer
test quality reviewer
regression risk reviewer
performance reviewer
```

Review output must use severity:

```text
critical
major
minor
note
```

Critical findings block verification.

---

# 21. Skill-power validation lab

## 21.1 Purpose

The pipeline should include a repeatable validation practice for improving skills, templates, docsets, and review prompts.

The validation lab should answer:

```text
Which skill version produces better artifacts?
Which prompt is brittle?
Which step loses context?
Which docset improves quality?
Which review catches seeded defects?
Which TDD skill records evidence reliably?
Which architecture skill best explains module communication?
```

## 21.2 Candidate isolation

Candidate skills must not live under:

```text
.agents/skills/
```

Use:

```text
.agents/skill-lab/quarantine/<skill-name>/<candidate-version>/
  SKILL.candidate.md
  notes.md
  expected-improvement.md
```

Do not name candidate files `SKILL.md`, so Codex does not discover them accidentally.

## 21.3 `pipelinebench.py`

`pipelinebench.py` evaluates existing runs and skill candidates.

Modes:

```text
offline
  Score existing generated artifacts.

interactive
  User/Codex runs scenario, pipelinebench scores outputs.

harness
  Future automated Codex execution.
```

MVP commands:

```text
init-lab
list-scenarios
score-run
compare-runs
generate-report
add-regression
```

Later commands:

```text
run-scenario
run-suite
promote-candidate
quarantine-candidate
```

## 21.4 MVP benchmark lab

Start with:

```text
one toy environment
three scenarios
three scorecards
one compare-runs command
one report.md
```

MVP scenarios:

```text
auth-reset-password
webhook-integration
frontend-settings
```

MVP scorecards:

```text
artifact-quality
architecture-quality
safety-and-gates
```

## 21.5 Hard checks vs soft scores

Hard checks are deterministic and must pass:

```text
file exists
schema valid
gate not accidentally approved
no implementation before readiness
slices have red/green commands
evidence files exist
wrong-worktree detection works
```

Soft scores are human/LLM-judged:

```text
requirement quality
architecture clarity
module communication quality
ADR usefulness
reuse quality
review quality
```

Promotion requires:

```text
all hard checks pass
no safety regression
target soft score improves or does not regress
```

---

# 22. Tests

Required tests:

```text
test_feature_identity.py
test_workspace_creation.py
test_state_machine.py
test_gate_status.py
test_docset_loading.py
test_context_skill_contract.py
test_staleness.py
test_slices_validation.py
test_evidence_order.py
test_review_blocking.py
test_worktree_rules.py
test_promotion.py
test_pipelinebench_offline.py
test_skill_candidate_isolation.py
```

Important checks:

```text
no approvals.yaml exists
no handoff.md exists
state.yaml has no next_skill
execution.md exists
apex.md routes to correct files
featurectl does not write narrative artifacts
worktree is created before planning artifacts
implementation is blocked before required gates
planning autorun stops on blocking ambiguity
docs consulted are recorded in execution.md
evidence red timestamp is before green timestamp
candidate skills are not under .agents/skills
```

---

# 23. Manual validation scenarios

## Scenario 1 — One artifact

Prompt:

```text
Create only the feature contract for reset password and stop.
```

Must pass:

```text
new worktree created
feature workspace created inside worktree
feature.md drafted
state gate feature_contract = drafted
execution.md records stop point
no meaningful architecture.md content beyond scaffold
no implementation code changed
```

---

## Scenario 2 — Partial planning

Prompt:

```text
Create feature contract and architecture, then stop.
```

Must pass:

```text
feature.md drafted
architecture.md drafted
diagrams/ populated if needed
ADRs created only for significant decisions
execution.md records docs consulted
state current_step reflects next step or stop point
no tech-design implementation details beyond scaffold
no code changed
```

---

## Scenario 3 — Full planning, stop before implementation

Prompt:

```text
Create all planning artifacts and stop before implementation.
```

Must pass:

```text
feature.md complete
architecture.md complete
tech-design.md complete
slices.yaml valid
readiness summary in execution.md
implementation gates not automatically approved unless user delegated
no code changed
```

---

## Scenario 4 — Full pipeline request without delegation

Prompt:

```text
Run the whole pipeline end to end.
```

Must pass:

```text
Codex presents execution.md pre-flight plan
Codex asks for delegation boundaries
Codex does not implement before approval/delegation
```

---

## Scenario 5 — Planning automation with blocking ambiguity

Prompt:

```text
Create planning artifacts for reset password automatically.
```

With critical details omitted, such as token expiry or account enumeration behavior.

Must pass:

```text
Codex stops for blocking clarification
execution.md records blocking questions
architecture is not drafted from unsafe assumptions
```

---

## Scenario 6 — Empty knowledge bootstrap

Run in a repo with no `.ai/knowledge`.

Must pass:

```text
context skill inspects repo/docs/source
provisional knowledge files are created
confidence marked low/medium
execution.md records inspected sources
architecture uses provisional knowledge carefully
```

---

## Scenario 7 — TDD evidence

After gates are approved:

```text
Implement first slice.
```

Must pass:

```text
pre-red git state recorded
red test output stored
green output stored after implementation
verification output stored
evidence manifest valid
complete-slice passes only after all evidence exists
```

---

## Scenario 8 — Scope change

During implementation, discover a missing requirement.

Must pass:

```text
implementation stops
scope-change.md created
affected artifacts marked stale
execution.md records return step
Codex returns to correct earlier skill
```

---

## Scenario 9 — Review catches issue

Introduce plaintext token storage.

Must pass:

```text
review identifies critical security issue
verification blocked
state review gate = blocked
execution.md records required fix
```

---

## Scenario 10 — Promotion

After finish:

```text
Promote feature.
```

Must pass:

```text
workspace promoted to .ai/features/<domain>/<slug>/
index.yaml regenerated
feature-card.md present
canonical docs updated by finish/promote skill
conflicting canonical feature aborts or archives as variant
```

---

# 24. Implementation milestones as vertical slices

Do not build all scaffolding first. Build working vertical slices.

## Slice 1 — Worktree + feature contract

Build:

```text
featurectl init
featurectl new
nfp-00-intake
nfp-01-context minimal
nfp-02-feature-contract
state.yaml
execution.md
apex.md
feature.md
```

Goal:

```text
User can create a feature contract and stop.
```

---

## Slice 2 — Architecture with doc loading

Build:

```text
nfp-03-architecture
docset loading
docs consulted in execution.md
provisional knowledge bootstrap
architecture.md
ADRs
diagrams
```

Goal:

```text
Feature contract → architecture → stop.
```

---

## Slice 3 — Tech design + slicing + readiness

Build:

```text
nfp-04-tech-design
nfp-05-slicing
nfp-06-readiness
slices.yaml validation
readiness validation
```

Goal:

```text
Full planning package, no code.
```

---

## Slice 4 — Gates + TDD evidence

Build:

```text
gate set approved
nfp-07-worktree status
nfp-08-tdd-implementation
evidence/ raw logs
complete-slice
```

Goal:

```text
First slice implemented with enforceable evidence.
```

---

## Slice 5 — Review + verification

Build:

```text
nfp-09-review
review tiers
subagent fallback
nfp-10-verification
critical issue blocking
```

Goal:

```text
Implementation cannot finish with critical review or failed verification.
```

---

## Slice 6 — Finish + promotion

Build:

```text
nfp-11-finish
feature-card.md
canonical docs update
nfp-12-promote
index regeneration
archive-as-variant
```

Goal:

```text
Feature becomes canonical memory.
```

---

## Slice 7 — Skill-power benchmark MVP

Build:

```text
pipelinebench offline mode
one toy environment
three scenarios
hard checks
soft score placeholders
candidate isolation
report.md
```

Goal:

```text
Weak skill versions can be detected before final manual validation.
```

---

# 25. Completion criteria

The project is complete when:

```text
1. Multi-skill Codex suite exists.
2. Every skill has version metadata.
3. Every feature starts in a worktree.
4. All feature artifacts live inside that worktree.
5. No approvals.yaml is used.
6. No handoff.md is used.
7. state.yaml is minimal machine state.
8. execution.md records run plan, approvals, docs consulted, decisions, and next step.
9. apex.md routes Codex to correct files.
10. featurectl.py stays deterministic and does not write narrative artifacts.
11. Context discovery is handled by an LLM skill using grep/file inspection.
12. Empty knowledge files are bootstrapped provisionally.
13. Readiness is simple and mostly delegates to featurectl validation.
14. Slices have TDD gates but no allowed/forbidden file enforcement.
15. Scope changes are handled explicitly.
16. Evidence stores raw command outputs and validates red-before-green order.
17. Review is split into deterministic and agentic layers.
18. Candidate skills are isolated outside .agents/skills.
19. Skill-power validation separates hard checks from soft scores.
20. Canonical feature memory explains motivation, architecture, module communication, contracts, implementation, tests, reviews, and evidence.
```

---

# 26. Executor task sequence

## Task 1 — Create foundation

```text
Create AGENTS.md, .gitignore, .ai base directories, .agents/pipeline-core scaffold, and .agents/skills scaffold.
Do not implement the full pipeline yet.
```

## Task 2 — Implement feature worktree creation

```text
Implement featurectl.py init/new/status.
Ensure featurectl new creates branch, worktree, feature workspace, apex.md, feature.yaml, state.yaml, and execution.md.
```

## Task 3 — Implement feature contract path

```text
Implement nfp-00-intake, nfp-01-context minimal, and nfp-02-feature-contract.
Validate one-artifact scenario.
```

## Task 4 — Implement architecture path

```text
Implement docset loading, provisional knowledge bootstrap, and nfp-03-architecture.
Validate docs consulted in execution.md.
```

## Task 5 — Implement tech design and slicing

```text
Implement nfp-04-tech-design, nfp-05-slicing, slices schema, and nfp-06-readiness.
Validate full planning without code.
```

## Task 6 — Implement gates and evidence

```text
Implement featurectl gate, mark-stale, record-evidence, complete-slice, and evidence manifest validation.
```

## Task 7 — Implement TDD slice execution

```text
Implement nfp-07-worktree and nfp-08-tdd-implementation.
Validate red-before-green evidence order.
```

## Task 8 — Implement review and verification

```text
Implement nfp-09-review and nfp-10-verification.
Split deterministic validation from agentic review.
Add critical issue blocking.
```

## Task 9 — Implement finish and promotion

```text
Implement nfp-11-finish and nfp-12-promote.
Generate feature-card.md, update canonical docs, regenerate index.yaml, and archive variants safely.
```

## Task 10 — Implement benchmark MVP

```text
Implement pipelinebench.py offline mode, one toy environment, three scenarios, hard checks, soft score placeholders, and report generation.
```

## Task 11 — Final validation

```text
Run automated tests.
Run manual validation scenarios.
Run benchmark MVP.
Fix weak skills through quarantine before promoting skill changes.
```

---

# 27. Final expected behavior

A feature planning run should look like this:

```text
User:
Create reset password. Build planning through implementation plan and stop.

Codex:
Creates a feature worktree.
Creates feature workspace inside the worktree.
Discovers existing auth/email/token patterns.
Asks blocking questions if needed.
Drafts feature contract.
Drafts architecture with module communication and ADRs.
Drafts technical design and contracts.
Creates TDD slices.
Writes execution.md summary.
Stops before implementation.
```

A later implementation run should look like this:

```text
User:
Approve planning and implement first slice.

Codex:
Verifies gates.
Records pre-red git state.
Writes failing test.
Runs red command.
Stores raw output.
Implements minimal code.
Runs green command.
Stores raw output.
Runs verification.
Stores evidence.
Marks slice complete.
Stops or continues based on user request.
```

The result is a controlled feature pipeline that avoids duplicated state, keeps work isolated in git worktrees, uses LLMs for reasoning and documentation, uses scripts only for deterministic safety, and leaves behind useful enterprise-grade feature memory.

[1]: https://developers.openai.com/codex/skills?utm_source=chatgpt.com 'Agent Skills – Codex'
[2]: https://developers.openai.com/codex/subagents?utm_source=chatgpt.com 'Subagents – Codex'
[3]: https://git-scm.com/docs/git-worktree?utm_source=chatgpt.com 'git-worktree Documentation - Git'
