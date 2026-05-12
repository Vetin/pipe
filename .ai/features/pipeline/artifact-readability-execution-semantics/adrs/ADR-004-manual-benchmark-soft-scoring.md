# ADR-004: Manual Benchmark Soft Scoring

Status: accepted
Date: 2026-05-12

## Context

`pipelinebench.py` hard checks catch structure regressions, but they cannot rate
architecture clarity, module communication, ADR usefulness, reuse quality, or
review quality. Those are the dimensions needed to compare skill prompt
quality.

## Decision

`pipelinebench.py score-run` accepts optional `--soft-score-file` YAML. The file
contains reviewer-provided scores, max values, and comments. The benchmark
output stores the score details and aggregate summary, and
`generate-report` renders the values side by side with hard-check results.

## Consequences

Hard checks remain deterministic and offline. Soft scores become explicit local
review data that can be produced by humans or a future LLM judge without hiding
that qualitative layer inside the hard-check result.
