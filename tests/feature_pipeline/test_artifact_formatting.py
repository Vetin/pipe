import subprocess
import sys
import tempfile
import unittest
import py_compile
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".agents/pipeline-core/scripts/featurectl.py"
PIPELINEBENCH = ROOT / ".agents/pipeline-core/scripts/pipelinebench.py"
FEATURECTL_CORE = ROOT / ".agents/pipeline-core/scripts/featurectl_core"
PIPELINEBENCH_CORE = ROOT / ".agents/pipeline-core/scripts/pipelinebench_core"


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class ArtifactFormattingTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory(prefix="artifact-formatting-")
        self.repo = self.make_repo(Path(self.tempdir.name))

    def tearDown(self):
        self.tempdir.cleanup()

    def make_repo(self, tempdir):
        repo = tempdir / "repo"
        repo.mkdir()
        run(["git", "init", "-b", "main"], repo)
        run(["git", "config", "user.email", "test@example.com"], repo)
        run(["git", "config", "user.name", "Test User"], repo)
        (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
        (repo / "docs").mkdir()
        (repo / "docs/features.md").write_text("# Feature: Enterprise Approval Dashboard\n", encoding="utf-8")
        (repo / "pipeline-lab").mkdir()
        (repo / "pipeline-lab/README.md").write_text("# Pipeline Lab\n", encoding="utf-8")
        (repo / "src/features/billing").mkdir(parents=True)
        (repo / "src/features/billing/service.py").write_text("def bill(): pass\n", encoding="utf-8")
        run(["git", "add", "."], repo)
        run(["git", "commit", "-m", "initial"], repo)
        return repo

    def test_generated_yaml_and_markdown_are_readable(self):
        run([sys.executable, str(SCRIPT), "init", "--profile-project"], self.repo)
        run(
            [
                sys.executable,
                str(SCRIPT),
                "new",
                "--domain",
                "auth",
                "--title",
                "Readable Reset Flow",
                "--run-id",
                "run-readable",
            ],
            self.repo,
        )

        yaml_paths = [
            self.repo / ".ai/features/index.yaml",
            self.repo / "../worktrees/auth-readable-reset-flow-run-readable/.ai/feature-workspaces/auth/readable-reset-flow--run-readable/feature.yaml",
            self.repo / "../worktrees/auth-readable-reset-flow-run-readable/.ai/feature-workspaces/auth/readable-reset-flow--run-readable/state.yaml",
        ]
        for path in yaml_paths:
            with self.subTest(path=path.name):
                content = path.read_text(encoding="utf-8")
                self.assertGreaterEqual(content.count("\n"), 2)
                self.assertNotIn("{", content)
                self.assertNotIn("features: [{", content)

        markdown_paths = sorted((self.repo / ".ai/knowledge").glob("*.md"))
        self.assertTrue(markdown_paths)
        for path in markdown_paths:
            with self.subTest(path=path.name):
                content = path.read_text(encoding="utf-8")
                self.assertRegex(content, r"(?m)^## ")
                long_lines = [line for line in content.splitlines() if len(line) > 220]
                self.assertEqual(long_lines, [])

    def test_source_controlled_pipeline_artifacts_have_readable_line_lengths(self):
        self.assertEqual(sorted((ROOT / ".ai/knowledge").glob("*.generated.md")), [])
        paths = [
            ROOT / ".gitignore",
            ROOT / ".ai/knowledge/discovered-signals.md",
            ROOT / ".ai/knowledge/project-overview.md",
            ROOT / ".ai/knowledge/profile-examples.yaml",
            ROOT / ".ai/features/index.yaml",
            ROOT / ".ai/features/overview.md",
            ROOT / ".ai/features/pipeline/portable-artifact-consistency/feature-card.md",
            ROOT / ".ai/features/pipeline/portable-artifact-consistency/execution.md",
            ROOT / ".ai/features/pipeline/portable-artifact-consistency/evidence/manifest.yaml",
        ]
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                content = path.read_text(encoding="utf-8")
                self.assertGreater(content.count("\n"), 4)
                long_lines = [line for line in content.splitlines() if len(line) > 220]
                self.assertEqual(long_lines, [])

    def test_canonical_and_knowledge_artifacts_are_readable(self):
        paths = [
            ROOT / ".ai/features/index.yaml",
            ROOT / ".ai/features/overview.md",
            *sorted((ROOT / ".ai/knowledge").glob("*.md")),
            *sorted((ROOT / ".ai/knowledge").glob("*.yaml")),
            *sorted((ROOT / ".ai/features").glob("*/*/feature.yaml")),
            *sorted((ROOT / ".ai/features").glob("*/*/state.yaml")),
            *sorted((ROOT / ".ai/features").glob("*/*/feature-card.md")),
            *sorted((ROOT / ".ai/features").glob("*/*/execution.md")),
            *sorted((ROOT / ".ai/features").glob("*/*/evidence/manifest.yaml")),
            *sorted((ROOT / ".ai/features").glob("*/*/reviews/*.yaml")),
            *sorted((ROOT / ".ai/features").glob("*/*/reviews/*.md")),
        ]
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                content = path.read_text(encoding="utf-8")
                self.assertGreater(content.count("\n"), 4)
                long_lines = [
                    f"{index}: {len(line)}"
                    for index, line in enumerate(content.splitlines(), start=1)
                    if len(line) > 220
                ]
                self.assertEqual(long_lines, [])

    def test_curated_markdown_uses_reviewable_line_lengths(self):
        paths = [
            *sorted((ROOT / ".ai/knowledge").glob("*.md")),
            *sorted((ROOT / ".ai/features").glob("*/*/feature-card.md")),
            *sorted((ROOT / ".ai/features").glob("*/*/execution.md")),
            *sorted((ROOT / ".ai/features").glob("*/*/reviews/*.md")),
        ]
        self.assertTrue(paths)
        for path in paths:
            in_code = False
            failures = []
            for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if line.startswith("```"):
                    in_code = not in_code
                if in_code or line.startswith("|"):
                    continue
                if len(line) > 180:
                    failures.append(f"{index}: {len(line)}")
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertEqual(failures, [])

    def test_knowledge_docs_have_sections_and_no_known_typos(self):
        for path in sorted((ROOT / ".ai/knowledge").glob("*.md")):
            content = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertIn("## ", content)
                self.assertNotIn("evidence//", content)

    def test_gitignore_is_line_based(self):
        lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        required = {
            "pipeline-lab/runs/",
            "pipeline-lab/showcases/repos/",
            "worktrees/",
            ".ai/logs/",
            "__pycache__/",
            ".pytest_cache/",
        }
        self.assertTrue(required.issubset(set(lines)))
        self.assertFalse(any(" " in line and not line.startswith("#") for line in lines if line.strip()))

    def test_source_controlled_python_files_are_readable(self):
        paths = [
            ROOT / ".agents/pipeline-core/scripts/featurectl.py",
            ROOT / ".agents/pipeline-core/scripts/pipelinebench.py",
            *sorted((ROOT / ".agents/pipeline-core/scripts/featurectl_core").glob("*.py")),
            *sorted((ROOT / ".agents/pipeline-core/scripts/pipelinebench_core").glob("*.py")),
            *sorted((ROOT / "tests/feature_pipeline").glob("*.py")),
        ]
        for path in paths:
            if path.name == "__init__.py":
                continue
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                content = path.read_text(encoding="utf-8")
                minimum_newlines = 5 if path.parent.name == "scripts" else 10
                self.assertGreater(content.count("\n"), minimum_newlines)
                py_compile.compile(str(path), doraise=True)
                long_lines = [f"{index}: {len(line)}" for index, line in enumerate(content.splitlines(), start=1) if len(line) > 220]
                self.assertEqual(long_lines, [])

    def test_pipeline_cli_wrappers_execute_real_commands(self):
        featurectl_help = run([sys.executable, str(SCRIPT), "--help"], ROOT)
        pipelinebench_help = run([sys.executable, str(PIPELINEBENCH), "--help"], ROOT)
        scenarios = run([sys.executable, str(PIPELINEBENCH), "list-scenarios"], ROOT)

        self.assertIn("usage: featurectl.py", featurectl_help.stdout)
        self.assertIn("status", featurectl_help.stdout)
        self.assertIn("usage: pipelinebench.py", pipelinebench_help.stdout)
        self.assertIn("score-run", pipelinebench_help.stdout)
        self.assertIn("auth-reset-password", scenarios.stdout)

    def test_pipeline_cli_scripts_are_thin_wrappers(self):
        wrappers = {
            ROOT / ".agents/pipeline-core/scripts/featurectl.py": "featurectl_core.cli",
            ROOT / ".agents/pipeline-core/scripts/pipelinebench.py": "pipelinebench_core.cli",
        }
        for path, import_target in wrappers.items():
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                content = path.read_text(encoding="utf-8")
                self.assertLess(content.count("\n"), 40)
                self.assertIn(import_target, content)
                self.assertIn("raise SystemExit(main())", content)
        self.assertTrue((ROOT / ".agents/pipeline-core/scripts/featurectl_core/cli.py").exists())
        self.assertTrue((ROOT / ".agents/pipeline-core/scripts/pipelinebench_core/cli.py").exists())

    def test_core_implementations_are_split_by_responsibility(self):
        featurectl_modules = {
            "formatting.py",
            "events.py",
            "profile.py",
            "validation.py",
            "evidence.py",
            "promotion.py",
        }
        pipelinebench_modules = {
            "scenarios.py",
            "score.py",
            "report.py",
            "candidates.py",
            "showcases.py",
        }
        self.assertTrue(featurectl_modules.issubset({path.name for path in FEATURECTL_CORE.glob("*.py")}))
        self.assertTrue(pipelinebench_modules.issubset({path.name for path in PIPELINEBENCH_CORE.glob("*.py")}))

        limits = {
            FEATURECTL_CORE / "cli.py": 1500,
            PIPELINEBENCH_CORE / "cli.py": 260,
        }
        for path, limit in limits.items():
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                line_count = len(path.read_text(encoding="utf-8").splitlines())
                self.assertLessEqual(line_count, limit)

    def test_change_label_only_manifests_declare_identity_policy(self):
        manifests = [
            *sorted((ROOT / ".ai/features").glob("*/*/evidence/manifest.yaml")),
            *sorted((ROOT / ".ai/feature-workspaces").glob("*/*/evidence/manifest.yaml")),
        ]
        self.assertTrue(manifests)
        for path in manifests:
            manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
            slices = manifest.get("slices") or {}
            has_change_label_only = any(
                isinstance(entry, dict) and "change_label" in entry and "diff_hash" not in entry
                for entry in slices.values()
            )
            if has_change_label_only:
                with self.subTest(path=path.relative_to(ROOT).as_posix()):
                    self.assertIn("completion_identity_policy", manifest)
                    self.assertTrue(
                        manifest.get("legacy_tolerance", {}).get("missing_diff_hash_when_change_label_present")
                    )

    def test_source_controlled_knowledge_docs_capture_pipeline_lifecycle(self):
        architecture = (ROOT / ".ai/knowledge/architecture-overview.md").read_text(encoding="utf-8")
        module_map = (ROOT / ".ai/knowledge/module-map.md").read_text(encoding="utf-8")
        integration_map = (ROOT / ".ai/knowledge/integration-map.md").read_text(encoding="utf-8")
        adr_index = (ROOT / ".ai/knowledge/adr-index.md").read_text(encoding="utf-8")

        for expected in (
            "## Control Plane",
            "## Artifact Lifecycle",
            "featurectl.py",
            "pipelinebench.py",
            "feature workspace",
            "canonical feature memory",
            "evidence lifecycle",
        ):
            self.assertIn(expected, architecture)
        self.assertIn("## Pipeline Control Modules", module_map)
        self.assertIn(".agents/pipeline-core/scripts/featurectl.py", module_map)
        self.assertIn(".agents/pipeline-core/scripts/featurectl_core/cli.py", module_map)
        self.assertIn(".agents/pipeline-core/scripts/pipelinebench.py", module_map)
        self.assertIn(".agents/pipeline-core/scripts/pipelinebench_core/cli.py", module_map)
        self.assertIn("## Pipeline Artifact Flow", integration_map)
        self.assertIn("featurectl.py wrapper -> featurectl_core", integration_map)
        self.assertIn("feature workspace -> canonical feature memory", integration_map)
        for adr in (
            "ADR-001 Promoted Readonly Workspaces",
            "ADR-002 Canonical Memory And Lab Signals",
            "ADR-003 Execution Event Log Semantics",
            "ADR-004 Manual Benchmark Soft Scoring",
        ):
            self.assertIn(adr, adr_index)


if __name__ == "__main__":
    unittest.main()
