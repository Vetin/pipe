# Evaluation Patterns

## What To Borrow

- Compare skill candidates outside active skills.
- Separate hard checks from soft scoring.
- Keep raw outputs and generated artifacts as review evidence.
- Run at least ten scenario iterations when claiming showcase stability.

## What To Reject

- Testing only the happy path.
- Promoting a skill based on a single anecdotal run.
- Placing candidate skills under `.agents/skills/`.

## Native Artifact Influence

`.agents/skill-lab/quarantine`, `.agents/skill-lab/accepted`,
`.agents/skill-lab/rejected`, `pipeline-lab/benchmarks`, `pipeline-lab/runs`,
and `pipeline-lab/scorecards`.

## Native Skill Influence

All `nfp-00` through `nfp-12` skills are subject to benchmark regression checks
before promotion, with implementation-heavy skills receiving extra scenario and
evidence review.

## Validation Rule Implied

`pipelinebench.py` must keep candidate skills isolated, report hard checks and
soft score placeholders, and generate repeatable benchmark reports.
