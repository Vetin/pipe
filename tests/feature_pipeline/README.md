# Feature Pipeline Test Taxonomy

This directory contains deterministic tests for the Native Feature Pipeline.
The groups below describe what each class of test proves.

## Featurectl Unit Tests

- `test_featurectl_core.py`
- `test_gate_status.py`
- `test_gates_and_evidence.py`
- `test_state_machine.py`
- `test_worktree_status.py`
- `test_worktree_rules.py`

These tests cover command behavior, state transitions, gate dependencies,
artifact validation, evidence ordering, and worktree isolation.

## Artifact Validation Tests

- `test_artifact_formatting.py`
- `test_docset_loading.py`
- `test_planning_readiness.py`
- `test_review_blocking.py`
- `test_review_verification.py`
- `test_finish_promote.py`

These tests prove source-controlled artifacts are readable, docs are loaded,
planning packages are structurally valid, review findings block unsafe progress,
and promotion preserves canonical memory.

## Skill Contract Tests

- `test_agents_policy.py`
- `test_context_skill.py`
- `test_methodology_contract.py`
- `test_skill_contracts.py`

These tests check repository policy, skill contract shape, context discovery
rules, methodology references, and mandatory docs-consulted behavior.

## Mock Codex Runner Tests

- `test_codex_e2e_runner.py`
- `test_codex_debug_runner.py`
- `test_native_feature_emulation.py`
- `test_native_feature_judge.py`

These tests validate prompt shape, runner wiring, debug artifact generation, and
offline native-feature emulation without invoking a real Codex process.

## Real Codex E2E Tests

- `test_real_codex_conversation.py`

This opt-in suite is gated by `RUN_REAL_CODEX_E2E=1` and validates real
conversational behavior from user prompt to feature workspace artifacts.

## Pipelinebench Tests

- `test_pipelinebench.py`
- `test_pipelinebench_offline.py`

These tests cover offline hard checks, manual soft-score input, report
generation, candidate isolation, public raw checks, and benchmark scenario
commands.

## Manual Preflight Tests

- `test_manual_check_preflight.py`

These tests keep manual-check documentation, pass criteria, and preflight
commands aligned with the active pipeline contract.
