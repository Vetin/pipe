# Pipeline Goal Validation

- Native run: `/Users/egormasnankin/work/harness-pipeline/pipeline-lab/showcases/native-emulation-runs/20260512-native-debug`
- Init profile run: `/Users/egormasnankin/work/harness-pipeline/pipeline-lab/showcases/init-profile-runs/20260512-init-profile`
- Repeated passes: `3`
- Generated at: `2026-05-11T23:49:22.982152+00:00`

## Pass Summary

| Pass | Status | Failed Checks |
| ---: | --- | ---: |
| 1 | pass | 0 |
| 2 | pass | 0 |
| 3 | pass | 0 |

## Skill Side By Side

| Skill | Status | Detail |
| --- | --- | --- |
| `nfp-00-intake` | pass | shared protocol present |
| `nfp-01-context` | pass | shared protocol present |
| `nfp-02-feature-contract` | pass | shared protocol present |
| `nfp-03-architecture` | pass | shared protocol present |
| `nfp-04-tech-design` | pass | shared protocol present |
| `nfp-05-slicing` | pass | shared protocol present |
| `nfp-06-readiness` | pass | shared protocol present |
| `nfp-07-worktree` | pass | shared protocol present |
| `nfp-08-tdd-implementation` | pass | shared protocol present |
| `nfp-09-review` | pass | shared protocol present |
| `nfp-10-verification` | pass | shared protocol present |
| `nfp-11-finish` | pass | shared protocol present |
| `nfp-12-promote` | pass | shared protocol present |
| `architecture_mermaid_topology` | pass | architecture skill requires Mermaid topology and shared knowledge impact |
| `finish_shared_knowledge_updates` | pass | finish skill requires shared knowledge update reporting |
| `tdd_superpowers_subagent_flow` | pass | mandatory Superpowers subagent flow present |
| `project-init` | pass | /init profile protocol present |

## All Checks

### Pass 1
- `pass` `vision_user_flow`: user only describes, answers, and approves gates
- `pass` `vision_native_workflow`: native workflow hides internal phase commands
- `pass` `plan_artifact_graph`: plan requires artifact graph and validation layer
- `pass` `plan_project_context`: plan requires living knowledge and brownfield bootstrap
- `pass` `plan_validation_lab`: plan requires repeatable skill validation
- `pass` `native_prompt_style`: showcase prompts are native user requests
- `pass` `no_direct_skill_invocations`: showcase prompts avoid direct skill invocation list
- `pass` `best_three_count`: three best showcase cases are present
- `pass` `medusa-b2b-quote-to-order-approval-workflow_three_rounds`: rounds 1, 2, 3 are present
- `pass` `medusa-b2b-quote-to-order-approval-workflow_score_improves`: scores: [0.771, 0.89, 0.964]
- `pass` `medusa-b2b-quote-to-order-approval-workflow_production_score`: final score: 0.964
- `pass` `medusa-b2b-quote-to-order-approval-workflow_round3_artifacts`: round 3 artifacts exist
- `pass` `plane-github-sync-conflict-resolution-and-audit-trail_three_rounds`: rounds 1, 2, 3 are present
- `pass` `plane-github-sync-conflict-resolution-and-audit-trail_score_improves`: scores: [0.771, 0.89, 0.964]
- `pass` `plane-github-sync-conflict-resolution-and-audit-trail_production_score`: final score: 0.964
- `pass` `plane-github-sync-conflict-resolution-and-audit-trail_round3_artifacts`: round 3 artifacts exist
- `pass` `twenty-enterprise-duplicate-merge-with-preview-conflict-rules-and-rollback_three_rounds`: rounds 1, 2, 3 are present
- `pass` `twenty-enterprise-duplicate-merge-with-preview-conflict-rules-and-rollback_score_improves`: scores: [0.771, 0.89, 0.964]
- `pass` `twenty-enterprise-duplicate-merge-with-preview-conflict-rules-and-rollback_production_score`: final score: 0.964
- `pass` `twenty-enterprise-duplicate-merge-with-preview-conflict-rules-and-rollback_round3_artifacts`: round 3 artifacts exist
- `pass` `init_project_index_exists`: project-index.yaml exists
- `pass` `init_project_snapshot_exists`: project-snapshot.md exists
- `pass` `init_source_count`: source files: 15
- `pass` `init_test_count`: test files: 33
- `pass` `init_feature_signals`: feature signals extracted
- `pass` `init_feature_catalog`: feature catalog extracted
- `pass` `init_current_feature_picture`: features overview describes current feature picture
- `pass` `context_skill_uses_profile`: context skill invokes project profiling when knowledge is sparse
- `pass` `init_showcase_summary_exists`: init showcase summary exists
- `pass` `init_showcase_report_exists`: init showcase report exists
- `pass` `init_showcase_three_passes`: passes: 3
- `pass` `init_showcase_ten_cases`: cases: 10
- `pass` `init_showcase_all_results`: results: 30 expected: 30
- `pass` `init_showcase_no_failures`: failures: 0
- `pass` `init_showcase_stable`: all repos stable across repeated init passes
- `pass` `init_showcase_feature_catalogs`: every init run produced a feature catalog
- `pass` `skill_count`: found 13 nfp skills
- `pass` `skill_nfp-00-intake`: shared protocol present
- `pass` `skill_nfp-01-context`: shared protocol present
- `pass` `skill_nfp-02-feature-contract`: shared protocol present
- `pass` `skill_nfp-03-architecture`: shared protocol present
- `pass` `skill_nfp-04-tech-design`: shared protocol present
- `pass` `skill_nfp-05-slicing`: shared protocol present
- `pass` `skill_nfp-06-readiness`: shared protocol present
- `pass` `skill_nfp-07-worktree`: shared protocol present
- `pass` `skill_nfp-08-tdd-implementation`: shared protocol present
- `pass` `skill_nfp-09-review`: shared protocol present
- `pass` `skill_nfp-10-verification`: shared protocol present
- `pass` `skill_nfp-11-finish`: shared protocol present
- `pass` `skill_nfp-12-promote`: shared protocol present
- `pass` `skill_architecture_mermaid_topology`: architecture skill requires Mermaid topology and shared knowledge impact
- `pass` `skill_finish_shared_knowledge_updates`: finish skill requires shared knowledge update reporting
- `pass` `skill_tdd_superpowers_subagent_flow`: mandatory Superpowers subagent flow present
- `pass` `skill_project-init`: /init profile protocol present
- `pass` `web_best_practices_doc`: web best-practices synthesis exists
- `pass` `web_source_https://academy.openai.com/public/resources/skills`: source recorded: https://academy.openai.com/public/resources/skills
- `pass` `web_source_https://github.com/github/spec-kit`: source recorded: https://github.com/github/spec-kit
- `pass` `web_source_https://openspec.dev/`: source recorded: https://openspec.dev/
- `pass` `web_source_https://www.bmadcode.com/bmad-method/`: source recorded: https://www.bmadcode.com/bmad-method/
- `pass` `web_source_https://arxiv.org/abs/2604.05278`: source recorded: https://arxiv.org/abs/2604.05278
- `pass` `web_doc_## What To Borrow`: ## What To Borrow present
- `pass` `web_doc_## What To Reject`: ## What To Reject present
- `pass` `web_doc_## Native Artifact Influence`: ## Native Artifact Influence present
- `pass` `web_doc_## Native Skill Influence`: ## Native Skill Influence present
- `pass` `web_doc_## Init Bootstrap Influence`: ## Init Bootstrap Influence present
- `pass` `web_doc_## Three-Pass Init Validation`: ## Three-Pass Init Validation present
- `pass` `web_doc_## Validation Rule Implied`: ## Validation Rule Implied present

### Pass 2
- `pass` `vision_user_flow`: user only describes, answers, and approves gates
- `pass` `vision_native_workflow`: native workflow hides internal phase commands
- `pass` `plan_artifact_graph`: plan requires artifact graph and validation layer
- `pass` `plan_project_context`: plan requires living knowledge and brownfield bootstrap
- `pass` `plan_validation_lab`: plan requires repeatable skill validation
- `pass` `native_prompt_style`: showcase prompts are native user requests
- `pass` `no_direct_skill_invocations`: showcase prompts avoid direct skill invocation list
- `pass` `best_three_count`: three best showcase cases are present
- `pass` `medusa-b2b-quote-to-order-approval-workflow_three_rounds`: rounds 1, 2, 3 are present
- `pass` `medusa-b2b-quote-to-order-approval-workflow_score_improves`: scores: [0.771, 0.89, 0.964]
- `pass` `medusa-b2b-quote-to-order-approval-workflow_production_score`: final score: 0.964
- `pass` `medusa-b2b-quote-to-order-approval-workflow_round3_artifacts`: round 3 artifacts exist
- `pass` `plane-github-sync-conflict-resolution-and-audit-trail_three_rounds`: rounds 1, 2, 3 are present
- `pass` `plane-github-sync-conflict-resolution-and-audit-trail_score_improves`: scores: [0.771, 0.89, 0.964]
- `pass` `plane-github-sync-conflict-resolution-and-audit-trail_production_score`: final score: 0.964
- `pass` `plane-github-sync-conflict-resolution-and-audit-trail_round3_artifacts`: round 3 artifacts exist
- `pass` `twenty-enterprise-duplicate-merge-with-preview-conflict-rules-and-rollback_three_rounds`: rounds 1, 2, 3 are present
- `pass` `twenty-enterprise-duplicate-merge-with-preview-conflict-rules-and-rollback_score_improves`: scores: [0.771, 0.89, 0.964]
- `pass` `twenty-enterprise-duplicate-merge-with-preview-conflict-rules-and-rollback_production_score`: final score: 0.964
- `pass` `twenty-enterprise-duplicate-merge-with-preview-conflict-rules-and-rollback_round3_artifacts`: round 3 artifacts exist
- `pass` `init_project_index_exists`: project-index.yaml exists
- `pass` `init_project_snapshot_exists`: project-snapshot.md exists
- `pass` `init_source_count`: source files: 15
- `pass` `init_test_count`: test files: 33
- `pass` `init_feature_signals`: feature signals extracted
- `pass` `init_feature_catalog`: feature catalog extracted
- `pass` `init_current_feature_picture`: features overview describes current feature picture
- `pass` `context_skill_uses_profile`: context skill invokes project profiling when knowledge is sparse
- `pass` `init_showcase_summary_exists`: init showcase summary exists
- `pass` `init_showcase_report_exists`: init showcase report exists
- `pass` `init_showcase_three_passes`: passes: 3
- `pass` `init_showcase_ten_cases`: cases: 10
- `pass` `init_showcase_all_results`: results: 30 expected: 30
- `pass` `init_showcase_no_failures`: failures: 0
- `pass` `init_showcase_stable`: all repos stable across repeated init passes
- `pass` `init_showcase_feature_catalogs`: every init run produced a feature catalog
- `pass` `skill_count`: found 13 nfp skills
- `pass` `skill_nfp-00-intake`: shared protocol present
- `pass` `skill_nfp-01-context`: shared protocol present
- `pass` `skill_nfp-02-feature-contract`: shared protocol present
- `pass` `skill_nfp-03-architecture`: shared protocol present
- `pass` `skill_nfp-04-tech-design`: shared protocol present
- `pass` `skill_nfp-05-slicing`: shared protocol present
- `pass` `skill_nfp-06-readiness`: shared protocol present
- `pass` `skill_nfp-07-worktree`: shared protocol present
- `pass` `skill_nfp-08-tdd-implementation`: shared protocol present
- `pass` `skill_nfp-09-review`: shared protocol present
- `pass` `skill_nfp-10-verification`: shared protocol present
- `pass` `skill_nfp-11-finish`: shared protocol present
- `pass` `skill_nfp-12-promote`: shared protocol present
- `pass` `skill_architecture_mermaid_topology`: architecture skill requires Mermaid topology and shared knowledge impact
- `pass` `skill_finish_shared_knowledge_updates`: finish skill requires shared knowledge update reporting
- `pass` `skill_tdd_superpowers_subagent_flow`: mandatory Superpowers subagent flow present
- `pass` `skill_project-init`: /init profile protocol present
- `pass` `web_best_practices_doc`: web best-practices synthesis exists
- `pass` `web_source_https://academy.openai.com/public/resources/skills`: source recorded: https://academy.openai.com/public/resources/skills
- `pass` `web_source_https://github.com/github/spec-kit`: source recorded: https://github.com/github/spec-kit
- `pass` `web_source_https://openspec.dev/`: source recorded: https://openspec.dev/
- `pass` `web_source_https://www.bmadcode.com/bmad-method/`: source recorded: https://www.bmadcode.com/bmad-method/
- `pass` `web_source_https://arxiv.org/abs/2604.05278`: source recorded: https://arxiv.org/abs/2604.05278
- `pass` `web_doc_## What To Borrow`: ## What To Borrow present
- `pass` `web_doc_## What To Reject`: ## What To Reject present
- `pass` `web_doc_## Native Artifact Influence`: ## Native Artifact Influence present
- `pass` `web_doc_## Native Skill Influence`: ## Native Skill Influence present
- `pass` `web_doc_## Init Bootstrap Influence`: ## Init Bootstrap Influence present
- `pass` `web_doc_## Three-Pass Init Validation`: ## Three-Pass Init Validation present
- `pass` `web_doc_## Validation Rule Implied`: ## Validation Rule Implied present

### Pass 3
- `pass` `vision_user_flow`: user only describes, answers, and approves gates
- `pass` `vision_native_workflow`: native workflow hides internal phase commands
- `pass` `plan_artifact_graph`: plan requires artifact graph and validation layer
- `pass` `plan_project_context`: plan requires living knowledge and brownfield bootstrap
- `pass` `plan_validation_lab`: plan requires repeatable skill validation
- `pass` `native_prompt_style`: showcase prompts are native user requests
- `pass` `no_direct_skill_invocations`: showcase prompts avoid direct skill invocation list
- `pass` `best_three_count`: three best showcase cases are present
- `pass` `medusa-b2b-quote-to-order-approval-workflow_three_rounds`: rounds 1, 2, 3 are present
- `pass` `medusa-b2b-quote-to-order-approval-workflow_score_improves`: scores: [0.771, 0.89, 0.964]
- `pass` `medusa-b2b-quote-to-order-approval-workflow_production_score`: final score: 0.964
- `pass` `medusa-b2b-quote-to-order-approval-workflow_round3_artifacts`: round 3 artifacts exist
- `pass` `plane-github-sync-conflict-resolution-and-audit-trail_three_rounds`: rounds 1, 2, 3 are present
- `pass` `plane-github-sync-conflict-resolution-and-audit-trail_score_improves`: scores: [0.771, 0.89, 0.964]
- `pass` `plane-github-sync-conflict-resolution-and-audit-trail_production_score`: final score: 0.964
- `pass` `plane-github-sync-conflict-resolution-and-audit-trail_round3_artifacts`: round 3 artifacts exist
- `pass` `twenty-enterprise-duplicate-merge-with-preview-conflict-rules-and-rollback_three_rounds`: rounds 1, 2, 3 are present
- `pass` `twenty-enterprise-duplicate-merge-with-preview-conflict-rules-and-rollback_score_improves`: scores: [0.771, 0.89, 0.964]
- `pass` `twenty-enterprise-duplicate-merge-with-preview-conflict-rules-and-rollback_production_score`: final score: 0.964
- `pass` `twenty-enterprise-duplicate-merge-with-preview-conflict-rules-and-rollback_round3_artifacts`: round 3 artifacts exist
- `pass` `init_project_index_exists`: project-index.yaml exists
- `pass` `init_project_snapshot_exists`: project-snapshot.md exists
- `pass` `init_source_count`: source files: 15
- `pass` `init_test_count`: test files: 33
- `pass` `init_feature_signals`: feature signals extracted
- `pass` `init_feature_catalog`: feature catalog extracted
- `pass` `init_current_feature_picture`: features overview describes current feature picture
- `pass` `context_skill_uses_profile`: context skill invokes project profiling when knowledge is sparse
- `pass` `init_showcase_summary_exists`: init showcase summary exists
- `pass` `init_showcase_report_exists`: init showcase report exists
- `pass` `init_showcase_three_passes`: passes: 3
- `pass` `init_showcase_ten_cases`: cases: 10
- `pass` `init_showcase_all_results`: results: 30 expected: 30
- `pass` `init_showcase_no_failures`: failures: 0
- `pass` `init_showcase_stable`: all repos stable across repeated init passes
- `pass` `init_showcase_feature_catalogs`: every init run produced a feature catalog
- `pass` `skill_count`: found 13 nfp skills
- `pass` `skill_nfp-00-intake`: shared protocol present
- `pass` `skill_nfp-01-context`: shared protocol present
- `pass` `skill_nfp-02-feature-contract`: shared protocol present
- `pass` `skill_nfp-03-architecture`: shared protocol present
- `pass` `skill_nfp-04-tech-design`: shared protocol present
- `pass` `skill_nfp-05-slicing`: shared protocol present
- `pass` `skill_nfp-06-readiness`: shared protocol present
- `pass` `skill_nfp-07-worktree`: shared protocol present
- `pass` `skill_nfp-08-tdd-implementation`: shared protocol present
- `pass` `skill_nfp-09-review`: shared protocol present
- `pass` `skill_nfp-10-verification`: shared protocol present
- `pass` `skill_nfp-11-finish`: shared protocol present
- `pass` `skill_nfp-12-promote`: shared protocol present
- `pass` `skill_architecture_mermaid_topology`: architecture skill requires Mermaid topology and shared knowledge impact
- `pass` `skill_finish_shared_knowledge_updates`: finish skill requires shared knowledge update reporting
- `pass` `skill_tdd_superpowers_subagent_flow`: mandatory Superpowers subagent flow present
- `pass` `skill_project-init`: /init profile protocol present
- `pass` `web_best_practices_doc`: web best-practices synthesis exists
- `pass` `web_source_https://academy.openai.com/public/resources/skills`: source recorded: https://academy.openai.com/public/resources/skills
- `pass` `web_source_https://github.com/github/spec-kit`: source recorded: https://github.com/github/spec-kit
- `pass` `web_source_https://openspec.dev/`: source recorded: https://openspec.dev/
- `pass` `web_source_https://www.bmadcode.com/bmad-method/`: source recorded: https://www.bmadcode.com/bmad-method/
- `pass` `web_source_https://arxiv.org/abs/2604.05278`: source recorded: https://arxiv.org/abs/2604.05278
- `pass` `web_doc_## What To Borrow`: ## What To Borrow present
- `pass` `web_doc_## What To Reject`: ## What To Reject present
- `pass` `web_doc_## Native Artifact Influence`: ## Native Artifact Influence present
- `pass` `web_doc_## Native Skill Influence`: ## Native Skill Influence present
- `pass` `web_doc_## Init Bootstrap Influence`: ## Init Bootstrap Influence present
- `pass` `web_doc_## Three-Pass Init Validation`: ## Three-Pass Init Validation present
- `pass` `web_doc_## Validation Rule Implied`: ## Validation Rule Implied present
