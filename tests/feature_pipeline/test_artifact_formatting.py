import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".agents/pipeline-core/scripts/featurectl.py"


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
        paths = [
            ROOT / ".ai/knowledge/discovered-signals.md",
            ROOT / ".ai/knowledge/project-overview.md",
            ROOT / ".ai/features/index.yaml",
            ROOT / ".ai/features/overview.md",
        ]
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                content = path.read_text(encoding="utf-8")
                self.assertGreater(content.count("\n"), 4)
                long_lines = [line for line in content.splitlines() if len(line) > 220]
                self.assertEqual(long_lines, [])

    def test_source_controlled_python_files_are_readable(self):
        paths = [
            ROOT / ".agents/pipeline-core/scripts/featurectl.py",
            ROOT / ".agents/pipeline-core/scripts/pipelinebench.py",
            *sorted((ROOT / "tests/feature_pipeline").glob("*.py")),
        ]
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                content = path.read_text(encoding="utf-8")
                self.assertGreater(content.count("\n"), 10)
                long_lines = [f"{index}: {len(line)}" for index, line in enumerate(content.splitlines(), start=1) if len(line) > 220]
                self.assertEqual(long_lines, [])

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
        self.assertIn(".agents/pipeline-core/scripts/pipelinebench.py", module_map)
        self.assertIn("## Pipeline Artifact Flow", integration_map)
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
