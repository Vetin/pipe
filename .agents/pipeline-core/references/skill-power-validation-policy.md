# Skill Power Validation Policy

Candidate skills must stay outside active skill discovery:

```text
.agents/skill-lab/quarantine/<skill-name>/<candidate-version>/SKILL.candidate.md
```

Do not name candidate files `SKILL.md`.

Before promoting a candidate skill, compare it against the active skill with:

- hard artifact checks
- soft quality scoring
- raw generated outputs
- regression notes
- at least one realistic scenario

Accepted and rejected candidates should keep a concise evaluation summary.
