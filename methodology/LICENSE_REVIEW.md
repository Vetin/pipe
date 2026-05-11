# License Review

The extracted methodology files are original summaries, not copied upstream
text. They describe delivery patterns at a high level and are safe to ship with
the pipeline.

The upstream repositories have been cloned locally for inspection only. Clone
contents are ignored by Git; the committed repository stores only URLs, SHAs,
license names, and original synthesis.

| Source | License file reviewed | Effective license | Copied upstream text? | Pipeline use |
| --- | --- | --- | --- | --- |
| `bmad-method` | `methodology/upstream/bmad-method/LICENSE` | MIT | No | Behavioral inspiration for role gates, planning/review split |
| `spec-kit` | `methodology/upstream/spec-kit/LICENSE` | MIT | No | Behavioral inspiration for specs, clarify/plan/tasks, constitution gates |
| `openspec` | `methodology/upstream/openspec/LICENSE` | MIT | No | Behavioral inspiration for change proposals and safe apply/promote |
| `superpowers` | `methodology/upstream/superpowers/LICENSE` | MIT | No | Behavioral inspiration for skills, TDD loops, review packets |
| `aidlc-workflows` | `methodology/upstream/aidlc-workflows/LICENSE` | MIT | No | Behavioral inspiration for intent/unit/design validation |
| `specs-md` | `methodology/upstream/specs-md/LICENSE` | MIT | No | Behavioral inspiration for AI-DLC artifact flow |
| `shotgun` | `methodology/upstream/shotgun/LICENSE` | MIT | No | Behavioral inspiration for isolated parallel execution |
| `get-shit-done` | `methodology/upstream/get-shit-done/LICENSE` | MIT | No | Behavioral inspiration for ambiguity scoring and verification templates |
| `ccpm` | `methodology/upstream/ccpm/LICENSE` | MIT | No | Behavioral inspiration for dependency-aware task decomposition |
| `claude-task-master` | `methodology/upstream/claude-task-master/LICENSE` | MIT | No | Behavioral inspiration for task graph and complexity updates |
| `roo-code` | `methodology/upstream/roo-code/LICENSE` | Apache-2.0 | No | Behavioral inspiration for mode/skill packaging and guardrails |

Before vendoring any upstream repositories or docs snapshots into committed
content, record:

- upstream URL
- revision or release
- license
- copied files
- allowed use
- required attribution
- removal plan if the license is incompatible
