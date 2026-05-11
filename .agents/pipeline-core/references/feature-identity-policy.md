# Feature Identity Policy

Feature identity is semantic and stable:

- `feature_key`: `<domain>/<slug>`
- local IDs: `FR-001`, `NFR-001`, `AC-001`, `ADR-001`, `S-001`
- cross-feature references: `<feature_key>#<local-id>`

Scripts may scaffold identity files, but skills own naming judgment when the
user request is ambiguous. Stop and ask when the domain or feature intent cannot
be inferred safely.
