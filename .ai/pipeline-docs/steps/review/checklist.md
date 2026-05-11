# Review Checklist

- Run base `featurectl.py validate` before writing review files.
- Perform review at the requested tier.
- Use adversarial lenses and actively search for defects.
- Separate hard blocking findings from soft residual concerns.
- If no findings exist, write a note-level zero-finding justification with
  evidence.
- Use severity `critical`, `major`, `minor`, or `note`.
- Mark critical blocking findings as blocking.
- Record `Docs Consulted: Review` in `execution.md`.
- Run `featurectl.py validate --review` after review files exist.
- Stop verification while critical blocking findings remain.
