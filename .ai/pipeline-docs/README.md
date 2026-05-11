# Pipeline Documentation

This directory contains lightweight docsets loaded by Native Feature Pipeline
skills. Docsets provide step-specific reminders, methodology extraction docs,
shared policy references, and global standards; product and architecture prose
still belongs in feature artifacts written by the skills.

Each skill should call:

```bash
python .agents/pipeline-core/scripts/featurectl.py load-docset --workspace <workspace> --step <step>
```

Then it records only the docs it actually used in `execution.md` under
`Docs Consulted: <Step>`.
