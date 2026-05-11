# Planning Report: listmonk / Double Opt In Segment Onboarding

## Repo Snapshot
- Repo path: `/Users/egormasnankin/work/harness-pipeline/pipeline-lab/showcases/repos/listmonk`
- Remote: `https://github.com/knadh/listmonk.git`
- Base commit: `5898186`
- Pipeline workspace: `/Users/egormasnankin/work/harness-pipeline/pipeline-lab/showcases/repos/worktrees/subscribers-double-opt-in-segment-onboarding-run-listmonk-double-opt-in/.ai/feature-workspaces/subscribers/double-opt-in-segment-onboarding--run-listmonk-double-opt-in`
- Feature key: `subscribers/double-opt-in-segment-onboarding`
- Run ID: `run-listmonk-double-opt-in`

## Planning Scope
- Requested feature: Import subscribers into a pending segment, send confirmation, and move confirmed users to active segment.
- Implementation performed: no
- Source changes performed: no
- Stop point: planning package/readiness

## Context Summary
- Primary modules inspected: cmd, internal, models, tests
- Existing patterns reused: root manifests and candidate module names
- Test tooling detected: Makefile, README.md, go.mod

## Artifact Inventory
- `feature.md`: drafted with FR/NFR/AC IDs
- `architecture.md`: drafted with security, failure, observability, rollback, and ADR reference
- `tech-design.md`: drafted with contracts, data model, tests, migration, and rollback
- `slices.yaml`: drafted with 3 loop-ready TDD slices
- `execution.md`: docs consulted, planning evidence, and implementation boundary

## Gate State
- feature_contract: drafted
- architecture: drafted
- tech_design: drafted
- slicing_readiness: drafted
- implementation: blocked

## Validation
- Basic validation command: `featurectl.py validate --workspace <workspace>`
- Basic validation result: `0`
- Basic validation output:

```text
validation: pass
```

- Readiness validation command: `featurectl.py validate --workspace <workspace> --readiness`
- Readiness validation result: `1` (expected non-zero until gates are approved/delegated)
- Readiness validation output:

```text
validation: fail
- readiness requires feature_contract gate approved or delegated
- readiness requires architecture gate approved or delegated
- readiness requires tech_design gate approved or delegated
- readiness requires slicing_readiness gate approved or delegated
```

## Risks And Open Questions
- Security: authorization and audit history must be verified.
- Data/model: persistence changes need migration review.
- Compatibility: existing workflows may need transition guards.
- Product ambiguity: final approver/admin roles must be confirmed.
- Operational risk: retry, rollback, and observability must be validated before code.

## Proposed Implementation Handoff
- First slice: `S-001`
- Highest-risk slice: `S-002`
- Required approval/delegation before code: feature contract, architecture, technical design, slicing readiness
