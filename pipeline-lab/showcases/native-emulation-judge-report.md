# Native Feature Build Judge Report

- Judge mode: `deterministic-llm-style`
- Generated at: `2026-05-11T23:19:46.019874+00:00`

## Run Comparison

| Run | Case Avg | Methodology Coverage | Overall | Status | Hard Failures |
| --- | ---: | ---: | ---: | --- | --- |
| `20260512-native-debug` | 0.614 | 1.000 | 0.807 | needs work | 0 |
| `20260512-methodology-batch1` | 0.754 | 1.000 | 0.877 | high quality | 0 |
| `20260512-methodology-batch2` | 0.914 | 1.000 | 0.957 | high quality | 0 |
| `20260512-methodology-batch3` | 1.000 | 1.000 | 1.000 | high quality | 0 |

## Case Scores

| Run | Feature | Score | Weakest | Status |
| --- | --- | ---: | --- | --- |
| `20260512-native-debug` | Twenty - Enterprise duplicate merge with preview, conflict rules, and rollback | 0.637 | review_evidence | needs work |
| `20260512-native-debug` | Medusa - B2B quote-to-order approval workflow | 0.602 | review_evidence | needs work |
| `20260512-native-debug` | Plane - GitHub sync conflict resolution and audit trail | 0.602 | review_evidence | needs work |
| `20260512-methodology-batch1` | Twenty - Enterprise duplicate merge with preview, conflict rules, and rollback | 0.754 | review_evidence | needs work |
| `20260512-methodology-batch1` | Medusa - B2B quote-to-order approval workflow | 0.754 | review_evidence | needs work |
| `20260512-methodology-batch1` | Plane - GitHub sync conflict resolution and audit trail | 0.754 | review_evidence | needs work |
| `20260512-methodology-batch2` | Twenty - Enterprise duplicate merge with preview, conflict rules, and rollback | 0.914 | review_evidence | high quality |
| `20260512-methodology-batch2` | Medusa - B2B quote-to-order approval workflow | 0.914 | review_evidence | high quality |
| `20260512-methodology-batch2` | Plane - GitHub sync conflict resolution and audit trail | 0.914 | review_evidence | high quality |
| `20260512-methodology-batch3` | Twenty - Enterprise duplicate merge with preview, conflict rules, and rollback | 1.000 | native_prompt_integrity | high quality |
| `20260512-methodology-batch3` | Medusa - B2B quote-to-order approval workflow | 1.000 | native_prompt_integrity | high quality |
| `20260512-methodology-batch3` | Plane - GitHub sync conflict resolution and audit trail | 1.000 | native_prompt_integrity | high quality |

## Methodology Coverage

| Run | Weak Dimensions |
| --- | --- |
| `20260512-native-debug` | none |
| `20260512-methodology-batch1` | none |
| `20260512-methodology-batch2` | none |
| `20260512-methodology-batch3` | none |

## Baseline Delta

- Baseline run: `20260512-native-debug` overall `0.807`
- Latest run: `20260512-methodology-batch3` overall `1.000`
- Delta: `+0.193`
