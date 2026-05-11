# Subagent Review Policy

Subagents may perform bounded review, analysis, comparison, and risk discovery.
They must not approve gates, mutate `state.yaml`, or promote feature memory.

If subagents are unavailable, run the same review perspectives sequentially in
the main agent and write structured review artifacts.

Minimum enterprise review perspectives:

- spec compliance
- code quality
- security
- contract/API/schema
- test quality
- performance/regression risk
- architecture compliance
