# Verification Review

## Manual Validation

- `python .agents/pipeline-core/scripts/featurectl.py --help`
  - Result: passed.
  - Validated: wrapper executes real CLI code and prints featurectl commands.
- `python .agents/pipeline-core/scripts/pipelinebench.py --help`
  - Result: passed.
  - Validated: benchmark wrapper executes real CLI code and prints commands.
- `python .agents/pipeline-core/scripts/pipelinebench.py list-scenarios`
  - Result: passed.
  - Validated: benchmark scenario loading still works from the wrapper.
- `python -m unittest discover -s tests/feature_pipeline`
  - Result: passed, 149 tests.
  - Validated: standard library clean-checkout suite remains green.
- `python -m pytest tests/feature_pipeline -q`
  - Result: passed, 149 tests and 228 subtests.
  - Validated: pytest suite remains green after profile split and event changes.
- `python pipeline-lab/showcases/scripts/validate_pipeline_goals.py --passes 3 --report /tmp/pipeline-goal-validation-public-raw.md`
  - Result: passed with zero failures.
  - Validated: plan, vision, skills, init profiling, and showcase goal checks still pass.
- `git diff --check`
  - Result: passed.
  - Validated: no whitespace errors.

## Verification Debt

- `python -m black --check .agents tests pipeline-lab` was not run because `black`
  is not installed in this checkout.
- Residual risk is accepted for this feature because source readability is now
  guarded by no-dependency tests that compile Python files, execute wrapper
  commands, require readable checked-in artifacts, and enforce line-length limits.

## Failure Loop

- Initial final verification failed in `test_init_profile_showcases.py` because
  `run_init_profile_showcases.py` still read `feature_catalog` and
  `feature_signals` from `project-index.yaml`.
- Fix: the showcase runner now reads compact project metadata from
  `project-index.yaml` and feature signal/catalog data from
  `discovered-signals.md`.
- Recheck: targeted init-profile and goal-validation tests passed before the
  final full verification pass.
