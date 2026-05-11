# Core principle

The user should only do three things:

```text
1. Describe the feature.
2. Answer blocking questions.
3. Approve or request changes at gates.
```

The agent should do everything else:

```text
1. Select the workflow.
2. Read existing project/feature context.
3. Ask clarifying questions.
4. Create artifacts.
5. Enforce phase order.
6. Prevent premature coding.
7. Move to the next phase after approval.
8. Implement with TDD after build readiness.
9. Review and verify.
10. Update feature index.
```

So instead of exposing many commands, expose one natural workflow:

```text
“Let’s create a new feature: reset password.”
```

The agent responds by entering the **Native Feature Pipeline**.

---

# Desired conversational flow

Your example is exactly how I would design it.

## Step 1 — User describes feature

```text
User:
Let’s create a new feature: reset password.

Users should be able to request password reset by email.
They receive a link, open it, set a new password, and then can log in.
```

## Step 2 — Agent reviews input and asks only blocking questions

The agent should not immediately create architecture or write code.

It should first determine whether the product behavior is clear.

```text
Assistant:
I can start the reset password feature. Before drafting the feature contract, I need a few details that affect requirements and security:

1. Should unknown emails return the same response as known emails to prevent account enumeration?
2. How long should reset links remain valid?
3. Should using a reset link invalidate all previous reset links for that user?
4. Should users stay logged in after resetting their password, or must they log in again?
```

Important: the agent asks **grouped blocking questions**, not endless tiny questions.

## Step 3 — User answers

```text
User:
Unknown emails should return the same message.
Links expire after 30 minutes.
Using one link invalidates all previous links.
After reset, user must log in again.
```

## Step 4 — Agent creates `feature.md` draft and asks for approval

```text
Assistant:
Here is the proposed feature contract for “Reset Password”.

Feature: Reset Password

Intent:
Allow registered users to regain access to their account by requesting a secure password reset link by email.

Actors:
- Registered user
- Auth API
- Email service

Functional requirements:
- FR-001: A user can request a password reset by submitting an email address.
- FR-002: The public response must be identical for known and unknown email addresses.
- FR-003: A reset link expires after 30 minutes.
- FR-004: A reset token can be used only once.
- FR-005: Creating or using a reset token invalidates previous active reset tokens for that user.
- FR-006: After successfully resetting the password, the user must log in again.

Non-functional requirements:
- NFR-001: The system must not leak account existence.
- NFR-002: Reset tokens must not be stored in plaintext.
- NFR-003: Password reset attempts should be auditable.

Acceptance criteria:
- AC-001: Existing users can request a reset email.
- AC-002: Unknown emails receive the same public response as known emails.
- AC-003: Expired reset links cannot be used.
- AC-004: Reused reset links cannot be used.
- AC-005: After password reset, old reset tokens are invalidated.

Non-goals:
- Social login recovery is out of scope.
- Admin-initiated password reset is out of scope.

Approve this feature contract and continue to architecture, or send changes.
```

## Step 5 — User approves

```text
User:
Approve.
```

## Step 6 — Agent automatically moves to architecture

No need for the user to say:

```text
/architecture
```

The agent reads state and knows the next phase is architecture.

````text
Assistant:
Approved. I’ll now draft the architecture for the reset password feature.

Architecture: Reset Password

System components:
- Web app
- Auth API
- PasswordResetService
- PasswordResetTokenStore
- EmailService
- AuditLog

System flow:

```mermaid
sequenceDiagram
  actor User
  participant Web
  participant API as Auth API
  participant Reset as PasswordResetService
  participant Store as Token Store
  participant Email as Email Service

  User->>Web: Submit email
  Web->>API: POST /auth/password-reset/request
  API->>Reset: requestPasswordReset(email)
  Reset->>Store: Invalidate existing active tokens
  Reset->>Store: Store hashed reset token
  Reset->>Email: Send reset email
  API-->>Web: Generic success response
````

Architecture decisions:

- ADR-001: Store reset tokens hashed, not plaintext.
- ADR-002: Return identical public response for known and unknown email addresses.
- ADR-003: Invalidate previous active tokens when a new reset is requested.

Security considerations:

- Prevent account enumeration.
- Prevent token reuse.
- Prevent plaintext token exposure in storage.
- Audit reset attempts.

Approve this architecture and continue to technical design, or send changes.

````

That is the UX you want.

---

# The right abstraction

The pipeline should feel like:

```text
/feature new "Reset password"
````

or even just:

```text
Let’s build reset password.
```

But internally it should be a strict state machine:

```text
intake
→ feature_contract
→ feature_approval
→ architecture
→ architecture_approval
→ tech_design
→ tech_design_approval
→ execution_slicing
→ readiness_approval
→ worktree_setup
→ tdd_implementation
→ review
→ verification
→ pr_finish
→ feature_index_update
```

The user does **not** manually call those phases.

The agent advances automatically after approval.

---

# Artifact structure

I would use this structure:

```text
.ai/
  constitution.md

  features/
    index.yaml
    overview.md

    001-reset-password/
      feature.md
      architecture.md
      tech-design.md
      feature-card.md

      adrs/
        ADR-001-token-storage.md
        ADR-002-account-enumeration.md
        ADR-003-token-invalidation.md

      diagrams/
        context.mmd
        request-reset-sequence.mmd
        complete-reset-sequence.mmd

      contracts/
        api.openapi.yaml
        schemas/
          password-reset-request.schema.json
          password-reset-complete.schema.json

      slices.yaml
      state.yaml
      approvals.yaml
      evidence.md

      reviews/
        feature-review.md
        architecture-review.md
        tech-design-review.md
        code-review.md
        verification-review.md
```

The important addition here is:

```text
approvals.yaml
```

because approval is now part of the workflow.

---

# `state.yaml`

The agent uses this to know what to do next.

```yaml
feature_id: 'F001'
slug: 'reset-password'
title: 'Reset Password'

phase: 'architecture'

artifacts:
  feature: 'feature.md'
  architecture: 'architecture.md'
  tech_design: 'tech-design.md'
  slices: 'slices.yaml'
  evidence: 'evidence.md'

gates:
  feature_contract:
    status: 'approved'
    approved_by: 'user'
  architecture:
    status: 'drafting'
  tech_design:
    status: 'pending'
  slicing:
    status: 'pending'
  readiness:
    status: 'pending'
  implementation:
    status: 'pending'
  review:
    status: 'pending'
  verification:
    status: 'pending'

next_action: 'draft_architecture'
```

When the user says:

```text
Approve
```

the agent reads `state.yaml`, sees that the current phase is `architecture_approval`, records approval, and advances.

---

# `approvals.yaml`

This prevents invisible approvals.

```yaml
approvals:
  - gate: 'feature_contract'
    artifact: 'feature.md'
    status: 'approved'
    approved_at: '2026-05-01T10:30:00+02:00'
    approved_by: 'user'
    notes: 'Approved without changes'

  - gate: 'architecture'
    artifact: 'architecture.md'
    status: 'pending'
```

Approval becomes durable context.

This matters because later the agent can say:

```text
I cannot change token storage from hashed to plaintext because ADR-001 and the approved architecture require hashed storage.
```

---

# Agent behavior rules

The skill should contain strict rules like this:

```text
When a user asks to create a new feature, automatically start the Native Feature Pipeline.

Do not ask the user which phase to run.

Do not write implementation code before:
- feature.md is approved
- architecture.md is approved
- tech-design.md is approved
- slices.yaml is created
- build readiness gate is approved

At each approval gate:
- summarize the artifact
- show important requirements, assumptions, decisions, risks
- ask: “Approve and continue to <next phase>, or send changes?”

When the user approves:
- record approval
- update state
- immediately continue to the next phase

When the user requests changes:
- update the current artifact
- re-present the changed artifact
- ask for approval again

Ask clarifying questions only when missing information blocks correctness.
For non-blocking gaps, make explicit assumptions and record them.
```

This gives you the Superpowers-style enforcement.

---

# Gate behavior

## Gate 1 — Feature contract

Agent creates:

```text
feature.md
```

Agent asks:

```text
Approve this feature contract and continue to architecture, or send changes.
```

The agent cannot move to architecture before approval.

---

## Gate 2 — Architecture

Agent creates:

```text
architecture.md
diagrams/*.mmd
adrs/*.md
```

Agent asks:

```text
Approve this architecture and continue to technical design, or send changes.
```

The agent cannot move to tech design before approval.

---

## Gate 3 — Technical design

Agent creates:

```text
tech-design.md
contracts/*
```

Agent asks:

```text
Approve this technical design and continue to execution slicing, or send changes.
```

The agent cannot create implementation slices before approval.

---

## Gate 4 — Execution slicing and build readiness

Agent creates:

```text
slices.yaml
```

Each slice must include:

```text
requirement links
acceptance criteria links
allowed files
forbidden files
test to write first
red command
green command
verification commands
review focus
```

Agent asks:

```text
Approve this implementation plan and start the TDD build, or send changes.
```

After this approval, the agent can create a worktree and implement.

---

## Gate 5 — PR finish

After implementation, review, and verification:

```text
Agent:
The feature is implemented and verified.

Summary:
- Requirements implemented: FR-001 through FR-006
- Tests added: 8
- Verification: test, lint, typecheck, build passed
- Critical review issues: none
- Feature index updated

Approve PR summary, or request changes.
```

---

# Conversational state transitions

This is how the agent should handle user replies.

| User reply                      | Agent behavior                                                              |
| ------------------------------- | --------------------------------------------------------------------------- |
| “Approve”                       | Record current gate approval and move to next phase                         |
| “Approve, but change X”         | Apply change, record conditional approval, continue                         |
| “Change X”                      | Modify current artifact and ask for approval again                          |
| “Go back to architecture”       | Reopen architecture gate and mark downstream artifacts stale                |
| “Start coding” before readiness | Refuse gently and explain the missing gate                                  |
| “Skip architecture”             | Allowed only for explicitly tiny changes; otherwise agent should require it |
| “Continue”                      | Read `state.yaml` and execute next valid phase                              |
| “Status”                        | Show current phase, approved gates, blockers, next action                   |

Important behavior:

```text
If architecture changes, tech-design.md and slices.yaml become stale.
If feature.md changes, architecture.md, tech-design.md, and slices.yaml become stale.
```

The agent should track this.

---

# Staleness rules

This is critical.

If the user changes an upstream artifact, downstream artifacts must be invalidated.

```yaml
staleness_rules:
  feature_changed:
    stale:
      - architecture.md
      - tech-design.md
      - slices.yaml

  architecture_changed:
    stale:
      - tech-design.md
      - slices.yaml

  tech_design_changed:
    stale:
      - slices.yaml

  slices_changed:
    stale:
      - implementation_evidence
      - verification_review
```

Example:

```text
User:
Actually, reset links should expire after 10 minutes, not 30.

Assistant:
Updated feature.md. This changes FR-003, so architecture, technical design, and slices are now marked stale where they referenced 30 minutes. I’ll update those downstream artifacts before implementation continues.
```

That prevents hidden drift.

---

# The agent should collect relevant existing feature context automatically

Before drafting `feature.md`, the agent should read:

```text
.ai/constitution.md
.ai/features/index.yaml
.ai/features/overview.md
```

Then it should identify related features.

For reset password, it might find:

```text
F002 Login
F003 Email Verification
F004 Account Lockout
```

The agent should include this in the feature contract:

```markdown
## Related Existing Features

- F002 Login
  - Relevant because reset password changes authentication flow.
- F003 Email Verification
  - Relevant because it already uses EmailService.
- F004 Account Lockout
  - Relevant because reset password may interact with locked accounts.
```

This is important because it means the feature pipeline is not isolated. It can reuse previous architecture decisions and implementation patterns.

---

# Suggested assistant message format

At every phase, the assistant should use a predictable format.

```text
Phase: Feature Contract
Status: Draft ready

Created/updated:
- .ai/features/001-reset-password/feature.md

Important decisions:
- Unknown email receives generic response.
- Reset links expire after 30 minutes.
- Used reset links cannot be reused.

Assumptions:
- Email delivery service already exists.
- Password policy is already defined elsewhere.

Open blockers:
- None.

<artifact summary>

Approve this feature contract and continue to architecture, or send changes.
```

For architecture:

```text
Phase: Architecture
Status: Draft ready

Created/updated:
- architecture.md
- diagrams/request-reset-sequence.mmd
- diagrams/complete-reset-sequence.mmd
- adrs/ADR-001-token-storage.md
- adrs/ADR-002-account-enumeration.md

Key decisions:
- Store token hashes only.
- Return generic public response.
- Invalidate active tokens when a new one is issued.

<diagram + summary>

Approve this architecture and continue to technical design, or send changes.
```

For tech design:

```text
Phase: Technical Design
Status: Draft ready

Created/updated:
- tech-design.md
- contracts/api.openapi.yaml
- contracts/schemas/password-reset-request.schema.json

Core modules:
- PasswordResetController
- PasswordResetService
- PasswordResetTokenStore
- EmailService
- AuditLog

Approve this technical design and continue to execution slicing, or send changes.
```

This is simple for the user and strict for the agent.

---

# Implementation model inside the harness

You need one high-level skill:

```text
native-feature-pipeline
```

Not separate user-facing commands for each phase.

Internally, the skill has phase handlers:

```text
handle_intake()
handle_feature_contract()
handle_architecture()
handle_tech_design()
handle_slicing()
handle_readiness()
handle_worktree()
handle_implementation()
handle_review()
handle_verification()
handle_finish()
handle_index_update()
```

The user only sees:

```text
/feature new "Reset password"
```

or natural language:

```text
Let’s create reset password.
```

And:

```text
Approve
Continue
Change this
Status
```

---

# Minimal skill rules

The `SKILL.md` should include something like:

```markdown
# Native Feature Pipeline

Use this skill when the user wants to create a new feature or make a significant behavior change.

## User experience

The user should not manually run phases.

Drive the workflow yourself:

1. Collect missing information.
2. Draft the current artifact.
3. Ask for approval or changes.
4. On approval, automatically continue to the next phase.

## Approval gates

Required gates:

1. Feature contract
2. Architecture
3. Technical design
4. Execution slicing / build readiness
5. PR finish

Never implement before gates 1–4 are approved.

## Clarification policy

Ask only blocking questions.
Group questions.
Do not ask about implementation details before the feature contract is clear.
Record assumptions explicitly.

## Existing context policy

Before drafting the feature:

1. Read `.ai/constitution.md`.
2. Read `.ai/features/index.yaml`.
3. Read relevant feature cards.
4. Reuse existing patterns where appropriate.

## Artifact policy

Maintain:

- feature.md
- architecture.md
- tech-design.md
- slices.yaml
- state.yaml
- approvals.yaml
- evidence.md
- feature-card.md

## State policy

Always read `state.yaml` before acting.
Always update `state.yaml` after completing a phase.
If an upstream artifact changes, mark downstream artifacts stale.

## Implementation policy

Use TDD for every execution slice:

1. Write failing test.
2. Run red command.
3. Confirm expected failure.
4. Implement minimal code.
5. Run green command.
6. Refactor.
7. Run verification.
8. Record evidence.
9. Commit slice.
```

This is what turns the pipeline from “docs user has to manage” into “agent behavior.”

---

# What changes from the previous proposal

Before, we had this user-facing model:

```text
/feature new
/feature continue
/feature status
```

Now I would simplify further:

```text
User describes feature.
Agent starts pipeline.
User approves or changes.
Agent continues automatically.
```

`/feature continue` is still useful for resuming a session, but it should not be the normal way to advance every step.

The normal way should be:

```text
Approve.
```

And the agent moves forward.

---

# Final recommended flow

```text
User:
Let’s create reset password feature. <details>

Agent:
Reads project context.
Finds related features.
Asks only blocking questions.

User:
Answers.

Agent:
Drafts feature.md.
Asks approval.

User:
Approve.

Agent:
Creates architecture.md, diagrams, ADRs.
Asks approval.

User:
Approve.

Agent:
Creates tech-design.md and contracts.
Asks approval.

User:
Approve.

Agent:
Creates slices.yaml and build-readiness summary.
Asks approval to start implementation.

User:
Approve.

Agent:
Creates worktree.
Implements slice by slice using TDD.
Runs review.
Runs verification.
Creates PR summary.
Updates feature-card.md, index.yaml, overview.md.
Asks final approval.
```

That is the right product experience.

The pipeline is still strict, but the user is not managing it. The agent is.
