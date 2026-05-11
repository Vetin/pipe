# Native Feature Build Judge Report

- Judge mode: `deterministic-llm-style`
- Generated at: `2026-05-11T23:06:00.585978+00:00`

## Run Comparison

| Run | Case Avg | Methodology Coverage | Overall | Status | Hard Failures |
| --- | ---: | ---: | ---: | --- | --- |
| `20260512-native-debug` | 0.828 | 1.000 | 0.914 | high quality | 0 |
| `20260512-methodology-batch1` | 0.980 | 1.000 | 0.990 | high quality | 0 |

## Case Scores

| Run | Feature | Score | Weakest | Status |
| --- | --- | ---: | --- | --- |
| `20260512-native-debug` | Twenty - Enterprise duplicate merge with preview, conflict rules, and rollback | 0.852 | contract_clarity | needs work |
| `20260512-native-debug` | Medusa - B2B quote-to-order approval workflow | 0.816 | contract_clarity | needs work |
| `20260512-native-debug` | Plane - GitHub sync conflict resolution and audit trail | 0.816 | contract_clarity | needs work |
| `20260512-methodology-batch1` | Twenty - Enterprise duplicate merge with preview, conflict rules, and rollback | 0.980 | architecture_design | high quality |
| `20260512-methodology-batch1` | Medusa - B2B quote-to-order approval workflow | 0.980 | architecture_design | high quality |
| `20260512-methodology-batch1` | Plane - GitHub sync conflict resolution and audit trail | 0.980 | architecture_design | high quality |

## Methodology Coverage

| Run | Weak Dimensions |
| --- | --- |
| `20260512-native-debug` | none |
| `20260512-methodology-batch1` | none |

## Baseline Delta

- Baseline run: `20260512-native-debug` overall `0.914`
- Latest run: `20260512-methodology-batch1` overall `0.990`
- Delta: `+0.076`
