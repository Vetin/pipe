# Native Feature Pipeline Validation

Date: 2026-05-11

## Automated Validation

Command:

```bash
python -m unittest discover -s tests/feature_pipeline
```

Result:

```text
Ran 47 tests in 13.227s
OK
```

Coverage highlights:

- worktree-first feature creation
- feature contract one-artifact stop
- docset loading and provisional knowledge policy
- architecture, technical design, slicing, and readiness validation
- gates, staleness, evidence ordering, and slice completion
- worktree implementation guard
- review and verification blocking
- finish and promotion, including archive-as-variant conflicts
- offline benchmark scoring and candidate skill isolation

## Real Example Validation

Executed in a temporary clone to avoid leaving branches or worktrees in this
repository.

Commands exercised:

```bash
python .agents/pipeline-core/scripts/featurectl.py new \
  --domain auth \
  --title "Reset Password" \
  --run-id run-20260511-real

python .agents/pipeline-core/scripts/featurectl.py validate \
  --workspace <temp-workspace> \
  --readiness

python .agents/pipeline-core/scripts/pipelinebench.py score-run \
  --workspace <temp-workspace> \
  --scenario auth-reset-password \
  --output <temp-score.yaml>
```

Observed result:

```text
feature_key: auth/reset-password
branch: feature/auth-reset-password-run-20260511-real
worktree: ../worktrees/auth-reset-password-run-20260511-real
workspace: .ai/feature-workspaces/auth/reset-password--run-20260511-real
next_step: nfp-01-context
validation: pass
hard_passed: true
hard_score: 5/5
```

## Benchmark MVP

Command:

```bash
python .agents/pipeline-core/scripts/pipelinebench.py list-scenarios
```

Result:

```text
auth-reset-password
frontend-settings
webhook-integration
```

Soft scores remain explicit offline placeholders. Candidate skill scoring is
accepted only for `.agents/skill-lab/quarantine/**/SKILL.candidate.md`.
