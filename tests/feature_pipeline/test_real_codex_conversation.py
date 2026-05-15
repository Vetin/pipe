import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
FEATURECTL = ROOT / ".agents/pipeline-core/scripts/featurectl.py"
PRODUCT_PATHS = ("auth.py", "test_auth.py", "package.json", "pyproject.toml", "requirements.txt")


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
        self.product_snapshots = {
            rel_path: (self.repo / rel_path).read_text(encoding="utf-8")
            for rel_path in PRODUCT_PATHS
            if (self.repo / rel_path).exists()
        }

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def install_pipeline_context(self):
        shutil.copy2(ROOT / "AGENTS.md", self.repo / "AGENTS.md")
        for dirname in (".agents", "skills"):
            shutil.copytree(ROOT / dirname, self.repo / dirname)
        (self.repo / ".ai").mkdir()
        shutil.copytree(ROOT / ".ai/pipeline-docs", self.repo / ".ai/pipeline-docs")
        shutil.copy2(ROOT / ".ai/constitution.md", self.repo / ".ai/constitution.md")

    def test_under_specified_reset_password_prompt_stops_for_blocking_questions(self):
        prompt = (
            "Create reset password. Build planning through implementation plan and stop. "
            "Do not implement product code before gates."
        )
        result, final_path = self.run_codex_prompt(prompt)
        self.assertEqual(result.returncode, 0, result.stdout)

        workspaces = sorted((self.tempdir / "worktrees").glob("*/.ai/feature-workspaces/*/*"))
        if not workspaces:
            final_text = final_path.read_text(encoding="utf-8") if final_path.exists() else result.stdout
            self.assert_contains_clarification_signal(final_text)
            self.assert_product_files_unchanged(self.repo)
            return

        workspace = workspaces[0]
        feature_worktree = self.feature_worktree_for(workspace)
        self.assert_product_files_unchanged(feature_worktree)
        self.assert_no_product_diff(feature_worktree)
        execution = (workspace / "execution.md").read_text(encoding="utf-8")
        state = yaml.safe_load((workspace / "state.yaml").read_text(encoding="utf-8"))
        final_text = final_path.read_text(encoding="utf-8") if final_path.exists() else ""

        self.assert_contains_clarification_signal(execution + "\n" + final_text)
        gates = state.get("gates", {})
        self.assertNotIn(gates.get("feature_contract"), {"approved", "delegated", "complete"})
        self.assertNotIn(gates.get("architecture"), {"approved", "delegated", "complete"})
        self.assertNotIn(gates.get("slicing_readiness"), {"approved", "delegated", "complete"})

    def test_specified_reset_password_prompt_drafts_planning_package_without_code_changes(self):
        prompt = (
            "Create reset password. Users request a reset by email. Unknown emails return "
            "the same public response. Reset tokens expire after 30 minutes, are single-use, "
            "previous active tokens are invalidated, and the user must log in again after "
            "reset. Build planning through implementation plan and stop. Do not implement "
            "product code before gates. This check requires no implementation code changed before gates."
        )
        result, _final_path = self.run_codex_prompt(prompt)
        self.assertEqual(result.returncode, 0, result.stdout)

        workspaces = sorted((self.tempdir / "worktrees").glob("*/.ai/feature-workspaces/*/*"))
        self.assertTrue(workspaces, result.stdout)
        workspace = workspaces[0]
        feature_worktree = self.feature_worktree_for(workspace)
        self.assertTrue((feature_worktree / ".git").exists() or (feature_worktree / ".git").is_file())
        self.assert_product_files_unchanged(feature_worktree)
        self.assert_no_product_diff(feature_worktree)

        for artifact in (
            "apex.md",
            "feature.yaml",
            "state.yaml",
            "execution.md",
            "events.yaml",
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

        state = yaml.safe_load((workspace / "state.yaml").read_text(encoding="utf-8"))
        feature = yaml.safe_load((workspace / "feature.yaml").read_text(encoding="utf-8"))
        events = yaml.safe_load((workspace / "events.yaml").read_text(encoding="utf-8"))
        self.assertNotIn(state["gates"].get("implementation"), {"approved", "delegated", "complete"})
        self.assertTrue(events["events"])
        self.assertEqual(events["feature_key"], feature["feature_key"])

        planning = run(
            [os.environ.get("PYTHON", "python"), str(FEATURECTL), "validate", "--workspace", str(workspace), "--planning-package"],
            feature_worktree,
            check=False,
        )
        self.assertEqual(planning.returncode, 0, planning.stdout)

        implementation = run(
            [os.environ.get("PYTHON", "python"), str(FEATURECTL), "validate", "--workspace", str(workspace), "--implementation"],
            feature_worktree,
            check=False,
        )
        self.assertNotEqual(implementation.returncode, 0)

    def run_codex_prompt(self, prompt):
        codex_bin = os.environ.get("CODEX_BIN", "codex")
        timeout = int(os.environ.get("CODEX_E2E_TIMEOUT_SECONDS", "1800"))
        final_path = self.tempdir / "codex-final.txt"
        result = run(
            [codex_bin, "exec", "-C", str(self.repo), "-o", str(final_path), prompt],
            self.repo,
            check=False,
            timeout=timeout,
        )
        return result, final_path

    def feature_worktree_for(self, workspace):
        feature_worktree = workspace.parents[3]
        self.assertTrue((feature_worktree / ".git").exists() or (feature_worktree / ".git").is_file())
        return feature_worktree

    def assert_product_files_unchanged(self, checkout):
        for rel_path, before in self.product_snapshots.items():
            self.assertEqual((checkout / rel_path).read_text(encoding="utf-8"), before, rel_path)

    def assert_no_product_diff(self, checkout):
        status = run(["git", "status", "--short", "--untracked-files=all", "--", *PRODUCT_PATHS], checkout)
        self.assertEqual(status.stdout.strip(), "")

    def assert_contains_clarification_signal(self, text):
        lower = text.lower()
        self.assertTrue(
            any(token in lower for token in ("clarifying", "blocking question", "open question", "token expiry", "single-use")),
            text,
        )


if __name__ == "__main__":
    unittest.main()
