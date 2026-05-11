# Web Best Practices 2026-05-12

This document records the current web-sourced methodology checks used to harden
the Native Feature Pipeline. It is synthesis only.

## What To Borrow

- OpenAI skill guidance: keep skills as reusable workflows with clear name,
  description, and `SKILL.md` instructions; use them when consistency,
  repeatable steps, strict formatting, or policy adherence matter.
- Spec Kit guidance: keep specification, plan, tasks, implementation,
  checklist/analyze, repository index, red-team, verify, and worktree concerns
  explicit. Brownfield bootstrap and repository indexing are first-class needs
  for existing codebases.
- OpenSpec guidance: describe a change as proposal, technical design,
  implementation tasks, and spec deltas before writing code; review and refine
  the plan before implementation to catch misalignment early.
- OpenSpec brownfield guidance: existing codebases need lightweight context
  discovery and specs that live in the repository rather than one-off chat
  plans.
- Context-grounded SDD research: add read-only repository probing hooks and
  validation hooks at each phase to reduce hallucinated APIs and architecture
  drift.
- BMAD ecosystem guidance: combine agents, workflows, and skills, but keep the
  installation and usage conversational so the user describes intent and the
  framework asks the right questions.

## What To Reject

- Direct skill scripting in showcase prompts. That validates obedience, not
  native workflow discovery.
- Large, ungrounded planning artifacts that do not cite repository evidence.
- Treating generated repository indexes as truth. They are maps to inspect, not
  architecture authority.
- Marking tasks complete without implementation, verification evidence, or
  review replay.
- One-size-fits-all ceremony for tiny changes; use lightweight native paths for
  small work and full gates for substantial features.

## Native Artifact Influence

- `.ai/knowledge/project-index.yaml` and `project-snapshot.md` provide the
  repository evidence map for brownfield feature work.
- `feature.md` remains the product contract and must contain testable behavior.
- `architecture.md` and `tech-design.md` must cite inspected modules rather
  than relying on generated summaries.
- `slices.yaml` must remain a dependency-aware implementation plan.
- `reviews/`, `evidence/`, and validation reports must show adversarial review,
  verification commands, and artifact-to-code traceability.

## Native Skill Influence

- `nfp-01-context` must run or consume project profiling before feature
  contract drafting when repository knowledge is missing or generic.
- `nfp-02-feature-contract` should behave like Spec Kit clarify/checklist:
  requirements must be measurable and ambiguity must be explicit.
- `nfp-03-architecture` and `nfp-04-tech-design` should behave like
  OpenSpec proposal/design: reviewable before code, grounded in existing
  modules and change impact.
- `nfp-05-slicing` and `nfp-08-tdd-implementation` should preserve dependency
  order, red/green evidence, and task completion integrity.
- `nfp-09-review` and `nfp-10-verification` should include red-team,
  security/replay/data-loss checks, exact commands, and blocked-validation
  residual risk.

## Init Bootstrap Influence

- `project-init` is the brownfield bootstrap skill. It runs before feature
  planning when knowledge is missing, stale, generic, or imported from a raw
  idea, executive research packet, or business-analysis document.
- The skill must produce a feature catalog and a `Current Feature Picture`
  section, but those entries are source maps rather than final truth.
- The context phase must verify at least the relevant cited files before
  converting init findings into feature, architecture, or technical design
  claims.
- Pipeline implementation artifacts, evidence directories, generated memory,
  and agent scaffolding should not pollute the product feature catalog.

## Three-Pass Init Validation

- Run project init across the real showcase repositories three times and compare
  source, test, documentation, contract, integration, feature-signal, and
  feature-catalog counts side by side.
- Fail the goal validator if any configured showcase repository cannot produce
  `.ai/knowledge/project-index.yaml`, `features-overview.md`, or a non-empty
  feature catalog.
- Treat stable repeated metrics as the minimum reproducibility bar before using
  init output in downstream feature-pipeline emulation.

## Validation Rule Implied

- A final pipeline health check must validate the best-three showcase features
  three times, compare active skills side by side, verify `/init` project
  profiling outputs, and map results back to `vision.md` and `plan.md`.
- The pipeline must fail validation when prompts enumerate direct internal
  skills, when final-round showcase scores regress, when project context is
  missing, or when a skill lacks the shared native protocol.

## Sources

- OpenAI Academy, "Skills": https://academy.openai.com/public/resources/skills
- GitHub Spec Kit README and extension catalog: https://github.com/github/spec-kit
- OpenSpec overview: https://openspec.dev/
- BMad Method overview: https://www.bmadcode.com/bmad-method/
- Spec Kit Agents context-grounding paper: https://arxiv.org/abs/2604.05278
