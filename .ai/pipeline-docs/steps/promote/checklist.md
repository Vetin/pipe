# Promote Checklist

- Validate finish state.
- Abort on canonical conflicts unless `archive-as-variant` is explicitly used.
- Copy workspace to `.ai/features/<domain>/<slug>/`.
- Regenerate `.ai/features/index.yaml`.
- Do not implement merge or replace conflict behavior in v1.
