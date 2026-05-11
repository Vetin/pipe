import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".agents/pipeline-core/scripts/featurectl.py"

METHODOLOGY_FILES = [
    "methodology/extracted/methodology-summary.md",
    "methodology/extracted/upstream-pattern-map.md",
    "methodology/extracted/artifact-model.md",
    "methodology/extracted/workflow-and-gates.md",
    "methodology/extracted/context-and-doc-loading.md",
    "methodology/extracted/review-and-verification.md",
    "methodology/extracted/evaluation-patterns.md",
    "methodology/extracted/web-best-practices-20260512.md",
]

UPSTREAM_REPOS = {
    "bmad-method": "https://github.com/bmad-code-org/BMAD-METHOD.git",
    "spec-kit": "https://github.com/github/spec-kit.git",
    "openspec": "https://github.com/Fission-AI/OpenSpec.git",
    "superpowers": "https://github.com/obra/superpowers.git",
    "aidlc-workflows": "https://github.com/awslabs/aidlc-workflows.git",
    "specs-md": "https://github.com/fabriqaai/specs.md.git",
    "shotgun": "https://github.com/shotgun-sh/shotgun.git",
    "get-shit-done": "https://github.com/glittercowboy/get-shit-done.git",
    "ccpm": "https://github.com/automazeio/ccpm.git",
    "claude-task-master": "https://github.com/eyaltoledano/claude-task-master.git",
    "roo-code": "https://github.com/RooCodeInc/Roo-Code.git",
}

REFERENCE_FILES = [
    ".agents/pipeline-core/references/feature-identity-policy.md",
    ".agents/pipeline-core/references/quality-rubric.md",
    ".agents/pipeline-core/references/context-reuse-policy.md",
    ".agents/pipeline-core/references/subagent-review-policy.md",
    ".agents/pipeline-core/references/skill-power-validation-policy.md",
    ".agents/pipeline-core/references/native-skill-protocol.md",
]

TEMPLATE_FILES = [
    ".agents/pipeline-core/references/generated-templates/feature-template.md",
    ".agents/pipeline-core/references/generated-templates/architecture-template.md",
    ".agents/pipeline-core/references/generated-templates/tech-design-template.md",
    ".agents/pipeline-core/references/generated-templates/adr-template.md",
    ".agents/pipeline-core/references/generated-templates/slice-template.yaml",
    ".agents/pipeline-core/references/generated-templates/review-template.md",
    ".agents/pipeline-core/references/generated-templates/feature-card-template.md",
    ".agents/pipeline-core/references/generated-templates/feature-yaml-template.yaml",
    ".agents/pipeline-core/references/generated-templates/apex-template.md",
    ".agents/pipeline-core/references/generated-templates/execution-template.md",
    ".agents/pipeline-core/references/generated-templates/docset-template.yaml",
    ".agents/pipeline-core/references/generated-templates/benchmark-scenario-template.yaml",
    ".agents/pipeline-core/references/generated-templates/scorecard-template.yaml",
]

SCHEMA_FILES = [
    ".agents/pipeline-core/scripts/schemas/feature.schema.json",
    ".agents/pipeline-core/scripts/schemas/state.schema.json",
    ".agents/pipeline-core/scripts/schemas/docset.schema.json",
    ".agents/pipeline-core/scripts/schemas/review.schema.json",
]


class MethodologyContractTests(unittest.TestCase):
    def test_methodology_extraction_is_actionable(self):
        required_sections = [
            "## What To Borrow",
            "## What To Reject",
            "## Native Artifact Influence",
            "## Native Skill Influence",
            "## Validation Rule Implied",
        ]

        for rel in METHODOLOGY_FILES:
            with self.subTest(path=rel):
                path = ROOT / rel
                self.assertTrue(path.exists(), rel)
                content = path.read_text(encoding="utf-8")
                for section in required_sections:
                    self.assertIn(section, content)
                self.assertIn("nfp-", content)

    def test_shared_references_templates_and_schemas_exist(self):
        for rel in [*REFERENCE_FILES, *TEMPLATE_FILES, *SCHEMA_FILES]:
            with self.subTest(path=rel):
                path = ROOT / rel
                self.assertTrue(path.exists(), rel)
                self.assertGreater(len(path.read_text(encoding="utf-8").strip()), 20)

    def test_upstream_lock_records_cloned_methodologies_without_vendoring(self):
        lock = (ROOT / "methodology/UPSTREAM_LOCK.md").read_text(encoding="utf-8")
        license_review = (ROOT / "methodology/LICENSE_REVIEW.md").read_text(encoding="utf-8")
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

        self.assertIn("methodology/upstream/*", gitignore)
        self.assertIn("!methodology/upstream/.gitkeep", gitignore)
        for name, url in UPSTREAM_REPOS.items():
            with self.subTest(name=name):
                self.assertIn(f"methodology/upstream/{name}", lock)
                self.assertIn(url, lock)
                self.assertRegex(lock, rf"{name}.*`[0-9a-f]{{40}}`")
                self.assertIn(f"`{name}`", license_review)
                self.assertIn("No", license_review)

    def test_docset_index_loads_every_step_without_missing_docs(self):
        index_path = ROOT / ".ai/pipeline-docs/docset-index.yaml"
        index = yaml.safe_load(index_path.read_text(encoding="utf-8"))
        expected_steps = {
            "intake",
            "context",
            "feature-contract",
            "architecture",
            "tech-design",
            "slicing",
            "readiness",
            "worktree",
            "tdd-implementation",
            "review",
            "verification",
            "finish",
            "promote",
        }
        self.assertEqual(set(index["steps"]), expected_steps)

        with tempfile.TemporaryDirectory(prefix="docset-workspace-") as tempdir:
            workspace = Path(tempdir)
            for step, rel_docset in index["steps"].items():
                with self.subTest(step=step):
                    docset_path = ROOT / ".ai/pipeline-docs" / rel_docset
                    self.assertTrue(docset_path.exists(), rel_docset)
                    docset = yaml.safe_load(docset_path.read_text(encoding="utf-8"))
                    self.assertEqual(docset["artifact_contract_version"], "0.1.0")
                    self.assertEqual(docset["step"], step)
                    self.assertIn(".agents/pipeline-core/references/native-skill-protocol.md", docset["required_docs"])
                    self.assertTrue(
                        any(doc.startswith("methodology/extracted/") for doc in docset["required_docs"] + docset.get("optional_docs", [])),
                        f"{step} docset must reference methodology extraction",
                    )
                    for doc in docset["required_docs"]:
                        self.assertTrue((ROOT / doc).exists(), f"{step} missing required doc {doc}")

                    result = subprocess.run(
                        [sys.executable, str(SCRIPT), "load-docset", "--workspace", str(workspace), "--step", step],
                        cwd=ROOT,
                        check=True,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    self.assertIn("missing_docs:\n  none", result.stdout)

    def test_step_checklists_repeat_docs_consulted_contract(self):
        expected_labels = {
            "intake": "Intake",
            "context": "Context",
            "feature-contract": "Feature Contract",
            "architecture": "Architecture",
            "tech-design": "Technical Design",
            "slicing": "Slicing",
            "readiness": "Readiness",
            "worktree": "Worktree",
            "tdd-implementation": "TDD Implementation",
            "review": "Review",
            "verification": "Verification",
            "finish": "Finish",
            "promote": "Promote",
        }
        for step, label in expected_labels.items():
            with self.subTest(step=step):
                checklist = (ROOT / f".ai/pipeline-docs/steps/{step}/checklist.md").read_text(encoding="utf-8")
                self.assertIn(f"Docs Consulted: {label}", checklist)

    def test_native_skills_follow_shared_methodology_protocol(self):
        for skill_path in sorted((ROOT / ".agents/skills").glob("nfp-*/SKILL.md")):
            with self.subTest(skill=skill_path.parent.name):
                content = skill_path.read_text(encoding="utf-8")
                self.assertIn("pipeline_contract_version: '0.1.0'", content)
                self.assertIn("Methodology:", content)
                self.assertIn(".agents/pipeline-core/references/native-skill-protocol.md", content)
                self.assertIn("methodology/extracted/upstream-pattern-map.md", content)
                self.assertIn("featurectl.py load-docset", content)
                self.assertIn("Docs Consulted:", content)
                self.assertIn("methodology/extracted/", content)
                for artifact in ("apex.md", "feature.yaml", "state.yaml", "execution.md"):
                    self.assertIn(artifact, content)
                self.assertIn("featurectl.py validate", content)

    def test_review_schema_requires_traceable_findings(self):
        schema = yaml.safe_load((ROOT / ".agents/pipeline-core/scripts/schemas/review.schema.json").read_text(encoding="utf-8"))
        required = set(schema["required"])
        for field in (
            "linked_requirement_ids",
            "linked_slice_ids",
            "file_refs",
            "reproduction_or_reasoning",
            "fix_verification_command",
            "re_review_required",
        ):
            self.assertIn(field, required)


if __name__ == "__main__":
    unittest.main()
