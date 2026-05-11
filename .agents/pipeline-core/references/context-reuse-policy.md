# Context Reuse Policy

Prefer local evidence in this order:

1. `apex.md`, `feature.yaml`, `state.yaml`, and `execution.md`
2. `.ai/knowledge/*`
3. `.ai/features/*`
4. repository docs and ADRs
5. source tree and tests
6. package manifests and contracts

When knowledge is missing, write provisional docs with source paths,
confidence, and human-review status. Do not claim architecture facts without an
inspected source.
