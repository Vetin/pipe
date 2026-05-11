# Promote Checklist

- Validate finish state.
- Record `Docs Consulted: Promote` in `execution.md`.
- Recheck source revision, manual validation, verification debt, claim
  provenance, and rollback guidance.
- Abort on canonical conflicts unless `archive-as-variant` is explicitly used.
- Copy workspace to `.ai/features/<domain>/<slug>/`.
- Regenerate `.ai/features/index.yaml`.
- Do not implement merge or replace conflict behavior in v1.
