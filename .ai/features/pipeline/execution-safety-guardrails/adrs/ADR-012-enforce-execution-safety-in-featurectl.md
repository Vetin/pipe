# ADR-012: Enforce Execution Safety In Featurectl

## Status

Accepted for this feature.

## Context

The Native Feature Pipeline uses skills for high-level workflow guidance, but
machine state is mutated through `featurectl.py`. Review found that step and
gate commands could be used to jump ahead even when skill prose says not to.

## Decision

`featurectl.py` will enforce legal step transitions and gate dependency order.
Backward movement returns through `scope-change` so stale artifacts and event
history are recorded.

## Consequences

This makes unsafe shortcuts deterministic command failures. Some repair flows
may need to use `scope-change` explicitly instead of directly editing state or
jumping steps.
