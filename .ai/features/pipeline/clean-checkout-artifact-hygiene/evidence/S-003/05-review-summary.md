Retry spec review: pass. The wrapper/core split still preserves featurectl.py and pipelinebench.py command contracts, and init --profile-project no longer creates .ai/knowledge/*.generated.md sidecars when curated knowledge docs exist.

Retry code-quality review: pass. The generator change removes status-noise artifacts without overwriting curated docs. Artifact-formatting tests enforce no checked-in generated sidecars, wrapper readability, core module existence, and line-length limits.

Retry verification: pass. Full tests/feature_pipeline suite passed after the generator adjustment, along with CLI smoke coverage and goal validation.