# Upstream Lock

The current pipeline is synthesized from cloned upstream methodology families.
The clone directories under `methodology/upstream/` are local working
references and are ignored by Git; this lock file is the committed source of
truth for the exact revisions inspected.

| Local clone | Upstream URL | Revision | License | Native use |
| --- | --- | --- | --- | --- |
| `methodology/upstream/bmad-method` | `https://github.com/bmad-code-org/BMAD-METHOD.git` | `b5b33c08fa3ed094f994415887b963b56b68a292` | MIT | Role-oriented gates, planning/review separation, adversarial QA, established-project context loading |
| `methodology/upstream/spec-kit` | `https://github.com/github/spec-kit.git` | `0593565607bdfb363c43b70595dfbfecbc54bc31` | MIT | Constitution-first specs, clarify/plan/tasks flow, acceptance criteria traceability, workflow state |
| `methodology/upstream/openspec` | `https://github.com/Fission-AI/OpenSpec.git` | `053d8a59d587f3c027a06ad80503a6b43d4f2a92` | MIT | Change-scoped proposals, spec deltas, validation before apply, safe promotion semantics |
| `methodology/upstream/superpowers` | `https://github.com/obra/superpowers.git` | `f2cbfbefebbfef77321e4c9abc9e949826bea9d7` | MIT | Explicit skill triggering, red/green execution loops, focused review packets |
| `methodology/upstream/aidlc-workflows` | `https://github.com/awslabs/aidlc-workflows.git` | `6cd8d37c4f7d499c2faa617de5f5ff6252b9702d` | MIT | Intent-to-unit decomposition, domain/logical design split, human validation checkpoints |
| `methodology/upstream/specs-md` | `https://github.com/fabriqaai/specs.md.git` | `a8d11c58df6242649fdc9856f9190f20fbbd6935` | MIT | AI-DLC inspiration, bounded units, artifact-driven design, risk-aware validation |
| `methodology/upstream/shotgun` | `https://github.com/shotgun-sh/shotgun.git` | `4d344d5a46aafc815de441ff670d4131187f33e6` | MIT | Parallel execution discipline, architecture notes, run isolation patterns |
| `methodology/upstream/get-shit-done` | `https://github.com/glittercowboy/get-shit-done.git` | `dd49abd32f52bf9d0534213a2a9ab910fbf080df` | MIT | Ambiguity scoring, spec-phase gates, phase state, verification and security templates |
| `methodology/upstream/ccpm` | `https://github.com/automazeio/ccpm.git` | `7d7e4623bc6d4c0c9ba66ca6bfecd7e5261dc697` | MIT | Context/task decomposition, progress state, issue-style implementation slices |
| `methodology/upstream/claude-task-master` | `https://github.com/eyaltoledano/claude-task-master.git` | `c0c98d367c55296bfe69e65680625b6db437af02` | MIT | PRD-to-task dependency graph, complexity analysis, task update after scope changes |
| `methodology/upstream/roo-code` | `https://github.com/RooCodeInc/Roo-Code.git` | `ff16c9c297acde5b757eaa9e2bc340be46c33fb5` | Apache-2.0 | Mode/skill packaging, tool-aware workflows, guardrails for delegated automation |

Extracted methodology documents remain original synthesis. Do not copy upstream
text into shipped skills or generated artifacts unless the license review is
updated with the exact copied files and attribution requirements.
