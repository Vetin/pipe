# Methodology Lenses

Use these lenses when a Native Feature Pipeline skill needs stronger judgment
than a checklist can provide. They synthesize the upstream methodology clones
without copying their prompts or process text.

## Adaptive Rigor

Classify the request before deciding how much ceremony to apply:

| Level | Use when | Required behavior |
| --- | --- | --- |
| Minimal | Small, local, low-risk change with obvious tests. | Keep artifacts concise, but still record requirements, test, evidence, and finish state. |
| Standard | Normal product feature or cross-module change. | Run the full planning path through readiness before implementation. |
| Comprehensive | Security, data loss, irreversible mutation, public API, compliance, billing, auth, migrations, or unclear business rules. | Stop on unresolved ambiguity, require explicit risk gates, ADRs, rollback, adversarial review, and final verification evidence. |

If the rigor level is uncertain, choose the higher level and explain why in
`execution.md`.

## Ambiguity Taxonomy

Score ambiguity before drafting irreversible plans. Use a 0.00 to 1.00 score
where 0.00 is fully clear and 1.00 is unsafe to proceed.

| Dimension | Questions to resolve |
| --- | --- |
| Functional scope | What behavior is in, out, and conditional? |
| Domain/data model | What entities, states, invariants, retention, and ownership rules matter? |
| UX/workflow | Who acts, in what order, with what visible feedback and failure paths? |
| Integrations/contracts | Which APIs, events, schemas, jobs, or external systems are affected? |
| Security/privacy/RBAC | Who may read, preview, mutate, approve, retry, or roll back? |
| Failure/edge cases | What retries, stale data, concurrency, idempotency, and rollback paths exist? |
| Non-functional constraints | What performance, scale, observability, compliance, and migration constraints apply? |
| Completion signals | What test, UAT, evidence, and promotion criteria prove done? |

Gate policy:

- `<= 0.20`: proceed with recorded assumptions.
- `0.21..0.40`: proceed only if unclear dimensions are low risk and explicitly
  deferred.
- `> 0.40`: ask blocking questions or return to intake/context.
- Any unresolved security, destructive, public-contract, compliance, or data
  ownership ambiguity blocks implementation even if the total score is low.

## Clarification Discipline

- Ask at most five blocking questions before drafting the next artifact.
- Ask the highest-impact question first; group only tightly related questions.
- Record each question as answered, assumed, deferred, or blocking.
- If the user answer is vague, re-score ambiguity before proceeding.
- When a design direction is genuinely open, present two or three approach
  options with tradeoffs instead of hiding the choice in implementation.

## Brownfield Research

Before adding behavior, ask "does this already exist?" and inspect source-backed
evidence:

- existing feature cards, docs, ADRs, contracts, migrations, tests, and module
  names;
- repository-generated `.ai/knowledge` files, treated as source maps rather
  than truth;
- at least three cited paths for substantial features when the repository has
  enough files;
- current feature picture and reuse opportunities.

Every product, architecture, or design claim derived from generated knowledge
must cite or mention the source path that was read.

## Elicitation Lenses

Use these as second-pass checks when the artifact feels plausible but thin:

- pre-mortem: why would this feature fail in production?
- inversion: what must never happen?
- first principles: which invariant is actually required?
- red team/blue team: how can the design be broken, then defended?
- stakeholder map: who gains, loses, approves, audits, or supports this?
- existing-solution scan: what can be reused instead of newly invented?

## Task Graph Lens

Slices are executable units, not prose bullets. Each slice should expose:

- requirement and acceptance-criteria links;
- dependency chain and critical path impact;
- priority, complexity, and confidence;
- expected touchpoints and file ownership;
- conflict risk with adjacent work;
- test strategy, red command, expected failure, green command, and independent
  verification;
- rollback point and failure triage notes.

## Evidence And Review Lens

- Red evidence must precede green evidence.
- A completion claim requires the exact command, result, and artifact path.
- A zero-finding review must explain what was inspected and why no blocking
  issue remains.
- Track hard findings separately from soft concerns.
- Record verification debt when a check cannot be run.
- Promotion requires fresh final verification after the last implementation or
  review fix.

## Subagent Implementation Lens

- Treat implementation as a controller workflow: one fresh implementer subagent
  per slice, then spec-compliance review, then code-quality review.
- Do not run implementation subagents in parallel; finish the current slice and
  both reviews before starting the next slice.
- Include full task text and artifact context in each subagent prompt. Do not
  make implementers infer their assignment from the entire plan.
- Send reviewer findings back to the same implementer and repeat spec review
  before code-quality review until both approve.
- If subagents are unavailable, record a blocker instead of silently switching
  to direct implementation.

## Eval Lens

Reusable showcase and skill validations should behave like isolated eval runs:

- stable run id, input feature, repository target, prompt style, timeout or
  stop condition, generated artifacts, scorecard, and report path;
- no direct internal skill invocation list in native prompts;
- baseline-vs-after comparison;
- hard failures for missing required artifacts and soft scores for quality;
- judge dimensions that can later be replaced by a real LLM judge.
