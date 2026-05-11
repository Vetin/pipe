# Workflow State Machine

Native Feature Pipeline steps advance in this order:

```text
intake
context
feature_contract
architecture
tech_design
slicing
readiness
worktree
tdd_implementation
review
verification
finish
promote
```

Implementation is blocked until feature contract, architecture, technical design,
and slicing readiness are approved or delegated.
