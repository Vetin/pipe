import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FEATURECTL = ROOT / ".agents/pipeline-core/scripts/featurectl.py"


def run(cmd, cwd, check=True, timeout=None):
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )


@unittest.skipUnless(
    os.environ.get("RUN_REAL_CODEX_E2E") == "1",
    "set RUN_REAL_CODEX_E2E=1 to run the real Codex behavioral e2e test",
)
class RealCodexConversationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="real-codex-e2e-"))
        self.repo = self.tempdir / "repo"
        self.repo.mkdir()
        run(["git", "init", "-b", "main"], self.repo)
        run(["git", "config", "user.email", "real-codex-e2e@example.invalid"], self.repo)
        run(["git", "config", "user.name", "Real Codex E2E"], self.repo)
        (self.repo / "README.md").write_text("# Real Codex E2E Fixture\n", encoding="utf-8")
        (self.repo / "auth.py").write_text(
            "def login(email, password):\n    return email == 'user@example.com'\n",
            encoding="utf-8",
        )
        (self.repo / "test_auth.py").write_text(
            "import unittest\n\n"
            "from auth import login\n\n\n"
            "class AuthTests(unittest.TestCase):\n"
            "    def test_login(self):\n"
            "        self.assertTrue(login('user@example.com', 'password'))\n\n\n"
            "if __name__ == '__main__':\n"
            "    unittest.main()\n",
            encoding="utf-8",
        )
        self.install_pipeline_context()
        run(["git", "add", "."], self.repo)
        run(["git", "commit", "-m", "seed"], self.repo)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def install_pipeline_context(self):
        shutil.copy2(ROOT / "AGENTS.md", self.repo / "AGENTS.md")
        for dirname in (".agents", "skills"):
            shutil.copytree(ROOT / dirname, self.repo / dirname)
        (self.repo / ".ai").mkdir()
        shutil.copytree(ROOT / ".ai/pipeline-docs", self.repo / ".ai/pipeline-docs")
        shutil.copy2(ROOT / ".ai/constitution.md", self.repo / ".ai/constitution.md")

    def test_reset_password_planning_stop_prompt(self):
        prompt = (
            "Create reset password. Build planning through implementation plan and stop. "
            "Do not implement product code before gates. This is a real behavioral e2e "
            "check: no implementation code changed before gates."
        )
        codex_bin = os.environ.get("CODEX_BIN", "codex")
        timeout = int(os.environ.get("CODEX_E2E_TIMEOUT_SECONDS", "1800"))
        final_path = self.tempdir / "codex-final.txt"

        result = run(
            [codex_bin, "exec", "-C", str(self.repo), "-o", str(final_path), prompt],
            self.repo,
            check=False,
            timeout=timeout,
        )
        self.assertEqual(result.returncode, 0, result.stdout)

        workspaces = sorted((self.tempdir / "worktrees").glob("*/.ai/feature-workspaces/*/*"))
        self.assertTrue(workspaces, result.stdout)
        workspace = workspaces[0]
        for artifact in (
            "apex.md",
            "feature.yaml",
            "state.yaml",
            "execution.md",
            "feature.md",
            "architecture.md",
            "tech-design.md",
            "slices.yaml",
        ):
            self.assertTrue((workspace / artifact).exists(), artifact)

        execution = (workspace / "execution.md").read_text(encoding="utf-8")
        self.assertIn("Docs Consulted", execution)
        self.assertIn("Used for:", execution)
        self.assertNotIn("approvals.yaml", "\n".join(path.name for path in workspace.rglob("*")))
        self.assertNotIn("handoff.md", "\n".join(path.name for path in workspace.rglob("*")))

        planning = run(
            [os.environ.get("PYTHON", "python"), str(FEATURECTL), "validate", "--workspace", str(workspace), "--planning-package"],
            workspace.parents[4],
            check=False,
        )
        self.assertEqual(planning.returncode, 0, planning.stdout)

        implementation = run(
            [os.environ.get("PYTHON", "python"), str(FEATURECTL), "validate", "--workspace", str(workspace), "--implementation"],
            workspace.parents[4],
            check=False,
        )
        self.assertNotEqual(implementation.returncode, 0)


if __name__ == "__main__":
    unittest.main()
