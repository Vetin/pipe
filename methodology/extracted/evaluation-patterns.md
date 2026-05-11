# Evaluation Patterns

## What To Borrow

- Compare skill candidates outside active skills.
- Separate hard checks from soft scoring.
- Keep raw outputs and generated artifacts as review evidence.
- Run at least ten scenario iterations when claiming showcase stability.
- Run multi-round prompt improvement loops. A stable case should show the
  initial prompt, identified gaps, improved prompt, and final high-quality
  artifacts.
- Score artifact quality, architecture grounding, slice executability, review
  strictness, evidence quality, and native invocation separately so weaknesses
  are visible.
- Use high-complexity real-product scenarios because simple examples hide
  failures in contracts, migrations, permissions, background jobs, and rollback.

## What To Reject

- Testing only the happy path.
- Promoting a skill based on a single anecdotal run.
- Placing candidate skills under `.agents/skills/`.
- Calling internal skills directly in showcase prompts and then claiming native
  discovery was validated.
- Accepting a high score when artifacts lack repo-specific modules, risks,
  tests, or verification commands.

## Native Artifact Influence

`.agents/skill-lab/quarantine`, `.agents/skill-lab/accepted`,
`.agents/skill-lab/rejected`, `pipeline-lab/benchmarks`, `pipeline-lab/runs`,
and `pipeline-lab/scorecards`.
`pipeline-lab/showcases/native-emulation-runs/` stores native prompt
iterations, generated artifacts, scorecards, and comparison reports for
`features.md`.

## Native Skill Influence

All `nfp-00` through `nfp-12` skills are subject to benchmark regression checks
before promotion, with implementation-heavy skills receiving extra scenario and
evidence review.
Native emulation adds a separate check: prompts must not contain direct
`nfp-00` through `nfp-12` invocation lists.

## Validation Rule Implied

`pipelinebench.py` must keep candidate skills isolated, report hard checks and
soft score placeholders, and generate repeatable benchmark reports.
For the `features.md` showcase set, the best-three cases must reach production
quality by the final round and preserve the prompt-improvement trail.
