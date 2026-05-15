# Gate Policy

Gate state lives in `state.yaml`. Gate history lives in `execution.md`.

Valid gate statuses:

- `pending`
- `drafted`
- `approved`
- `delegated`
- `blocked`
- `reopened`
- `stale`
- `complete`

Do not create `approvals.yaml`.

## Planning Versus Delivery Gates

Planning gates use `approved` or `delegated` to grant permission for the next
planning or implementation phase:

- `feature_contract`
- `architecture`
- `tech_design`
- `slicing_readiness`

Delivery gates use `complete` to prove that work actually finished:

- `implementation`
- `review`
- `verification`
- `finish`

`approved` or `delegated` on a delivery gate only means the phase may run. It
does not satisfy downstream dependencies. In particular:

- `review` requires `implementation: complete`.
- `verification` requires `review: complete`.
- `finish` requires `verification: complete`.

Completion gates must validate their own artifacts before they can be marked
complete:

- `implementation: complete` requires completed slices and valid evidence.
- `review: complete` requires machine-readable review findings with no critical
  blockers.
- `verification: complete` requires final verification output and a
  verification review.
- `finish: complete` requires a feature card, completed evidence, reviews, and
  verification.

## Scaffold-Only Artifacts

If a downstream artifact is created only to reserve a file path while earlier
questions are still blocked, mark it explicitly:

```text
Status: scaffold-only
```

Scaffold-only artifacts must not satisfy planning-package validation or gate
approval. Remove the marker only after the artifact contains source-grounded
content and its Docs Consulted entries reference real paths with `used_for` and
confidence.
