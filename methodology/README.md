# Methodology Source Map

This directory records the upstream delivery methods that inspired the Native
Feature Pipeline. Local clones live under `methodology/upstream/` for
inspection and are ignored by Git; `UPSTREAM_LOCK.md` records the exact source
URL, revision, license, and native behavior borrowed from each repository.

The repo does not execute those methods directly. Each extraction document
states what to borrow, what to reject, which native artifact or skill it
influences, and which deterministic validation rule follows.

The implementation should prefer concise native artifacts over copying a full
external framework into every feature run.
