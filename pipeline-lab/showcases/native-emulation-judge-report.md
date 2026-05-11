# Native Feature Build Judge Report

- Judge mode: `deterministic-llm-style`
- Generated at: `2026-05-11T23:13:30.838368+00:00`

## Run Comparison

| Run | Case Avg | Methodology Coverage | Overall | Status | Hard Failures |
| --- | ---: | ---: | ---: | --- | --- |
| `20260512-native-debug` | 0.689 | 1.000 | 0.845 | needs work | 0 |
| `20260512-methodology-batch1` | 0.840 | 1.000 | 0.920 | high quality | 0 |
| `20260512-methodology-batch2` | 1.000 | 1.000 | 1.000 | high quality | 0 |

## Case Scores

| Run | Feature | Score | Weakest | Status |
| --- | --- | ---: | --- | --- |
| `20260512-native-debug` | Twenty - Enterprise duplicate merge with preview, conflict rules, and rollback | 0.712 | slicing_tdd | needs work |
| `20260512-native-debug` | Medusa - B2B quote-to-order approval workflow | 0.677 | slicing_tdd | needs work |
| `20260512-native-debug` | Plane - GitHub sync conflict resolution and audit trail | 0.677 | slicing_tdd | needs work |
| `20260512-methodology-batch1` | Twenty - Enterprise duplicate merge with preview, conflict rules, and rollback | 0.840 | slicing_tdd | needs work |
| `20260512-methodology-batch1` | Medusa - B2B quote-to-order approval workflow | 0.840 | slicing_tdd | needs work |
| `20260512-methodology-batch1` | Plane - GitHub sync conflict resolution and audit trail | 0.840 | slicing_tdd | needs work |
| `20260512-methodology-batch2` | Twenty - Enterprise duplicate merge with preview, conflict rules, and rollback | 1.000 | native_prompt_integrity | high quality |
| `20260512-methodology-batch2` | Medusa - B2B quote-to-order approval workflow | 1.000 | native_prompt_integrity | high quality |
| `20260512-methodology-batch2` | Plane - GitHub sync conflict resolution and audit trail | 1.000 | native_prompt_integrity | high quality |

## Methodology Coverage

| Run | Weak Dimensions |
| --- | --- |
| `20260512-native-debug` | none |
| `20260512-methodology-batch1` | none |
| `20260512-methodology-batch2` | none |

## Baseline Delta

- Baseline run: `20260512-native-debug` overall `0.845`
- Latest run: `20260512-methodology-batch2` overall `1.000`
- Delta: `+0.155`
