# Technical Design: Source Of Truth Hardening

## Change Delta

Add source-of-truth validators, update promotion/status behavior, make
`complete-slice` atomic, rewrite production skill reference roots, and tighten
project profile filters.

## Implementation Summary

`featurectl.py validate` will call a new repository-level validator that checks
canonical index, overview, canonical feature status, active workspace lifecycle,
and latest execution status. `cmd_complete_slice` will validate a proposed
manifest before writing commit metadata. Profile filtering will ignore generated
showcase output directories.

## Modules And Responsibilities

- `.agents/pipeline-core/scripts/featurectl.py`: validation, promotion,
  evidence completion, profile filtering.
- `.agents/skills/nfp-08-tdd-implementation/SKILL.md`: subagent fallback policy.
- `.agents/skills/nfp-09-review/SKILL.md`: reviewer fallback policy.
- `.agents/skills/nfp-12-promote/SKILL.md`: conflict wording.
- `tests/feature_pipeline/*`: regression coverage.

## Dependency And Ownership Plan

No new runtime dependencies. Tests continue using `unittest`, `pytest`, and
`PyYAML`, matching existing test helpers.

## Contracts

Validation blocker strings become the user-facing contract. `execution.md`
requires this section:

```markdown
## Latest Status

Current step:
Next recommended skill:
Blocking issues:
Last updated:
```

## API/Event/Schema Details

No public API changes. Existing `feature.yaml.status` values now use `draft`,
`complete`, `promoted`, or `archived` semantics during validation.

## Core Code Sketches

```python
def cmd_complete_slice(args):
    manifest = read_manifest()
    proposed = copy.deepcopy(manifest)
    add_commit_metadata(proposed)
    blockers = validate_slice_evidence_data(proposed)
    if blockers:
        fail_without_write()
    write_yaml(manifest_path, proposed)
```

## Data Model

- Canonical index entries must map to existing canonical directories.
- Complete canonical entries require canonical `feature.yaml.status != draft`.
- Active workspace lifecycle is checked against canonical feature keys.

## Error Handling

Validation accumulates blockers and prints all failures. Slice completion raises
without writing if evidence is invalid.

## Security Considerations

Generated path filters reduce the chance that benchmark output becomes
trusted architecture context.

## Test Strategy

- Unit tests for canonical overview/index drift.
- Unit tests for canonical `feature.yaml.status` drift.
- Unit tests for latest execution status mismatch.
- Unit tests for atomic `complete-slice`.
- Unit tests for profile filtering of generated showcase outputs.
- Text tests for skill reference consolidation and promotion wording.

## Migration Plan

Regenerate `.ai/features/overview.md` and current knowledge. Mark or repair
current historical active workspace states enough for validation to pass.

## Rollback Plan

Revert the feature commits. No irreversible migration is performed.

## Integration Notes

The changes are local to pipeline tooling and docs. Existing showcase scripts
continue to call `featurectl.py` the same way.

## Decision Traceability

- FR-001, FR-002, FR-003, FR-004 map to validation helpers and tests.
- FR-005 maps to `cmd_complete_slice`.
- FR-006, FR-007, FR-008 map to skill docs and methodology tests.
- FR-009 maps to project profile filters.
