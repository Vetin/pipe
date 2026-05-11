import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "pipeline-lab/showcases/scripts/run_codex_e2e_case.py"
CONFIG = ROOT / "pipeline-lab/showcases/codex-e2e-cases.yaml"


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class CodexE2ERunnerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="codex-e2e-test-"))
        self.repo = self.make_repo()
        self.config = self.write_case_config()
        self.fake_codex = self.write_fake_codex()
        self.output_dir = self.tempdir / "runs"

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def make_repo(self):
        repo = self.tempdir / "toy-repo"
        repo.mkdir()
        run(["git", "init", "-b", "main"], repo)
        run(["git", "config", "user.email", "test@example.com"], repo)
        run(["git", "config", "user.name", "Test User"], repo)
        (repo / "README.md").write_text("# Toy Repo\n", encoding="utf-8")
        run(["git", "add", "."], repo)
        run(["git", "commit", "-m", "seed"], repo)
        return repo

    def write_case_config(self):
        config = self.tempdir / "cases.yaml"
        config.write_text(
            yaml.safe_dump(
                {
                    "artifact_contract_version": "0.1.0",
                    "cases": {
                        "toy-feature": {
                            "title": "Toy Feature",
                            "domain": "toy",
                            "original_codebase": {
                                "repo_path": "toy-repo",
                                "base_ref": "HEAD",
                            },
                            "target_branch": "nfp/toy-feature",
                            "feature_request": "Add a stable greeting feature to the toy repository.",
                            "expected_result": "Artifacts, implementation notes, tests, and final summary are produced.",
                        }
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        return config

    def write_fake_codex(self):
        fake = self.tempdir / "fake-codex.py"
        fake.write_text(
            """#!/usr/bin/env python3
import json
import sys
from pathlib import Path

args = sys.argv[1:]
assert args[0] == "exec", args
repo = args[args.index("-C") + 1]
out = Path(args[args.index("-o") + 1])
prompt = args[-1]
out.write_text("branch: nfp/toy-feature\\ncommit: fake123\\n")
print(json.dumps({
    "repo": repo,
    "has_feature": "stable greeting feature" in prompt,
    "has_native_pipeline": "normal user feature request" in prompt and "Progress through these outcomes" in prompt,
    "no_direct_skill_invocations": "nfp-00-intake" not in prompt and "nfp-12-promote" not in prompt,
    "in_place": "Do not create a git worktree" in prompt,
}))
""",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        return fake

    def test_default_case_file_contains_stable_real_repo_cases(self):
        config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))

        self.assertEqual(len(config["cases"]), 10)
        for case_id, case in config["cases"].items():
            self.assertIn("original_codebase", case, case_id)
            self.assertIn("repo_path", case["original_codebase"], case_id)
            self.assertIn("feature_request", case, case_id)
            self.assertIn("target_branch", case, case_id)

    def test_runner_invokes_local_codex_and_writes_review_artifacts(self):
        result = run(
            [
                sys.executable,
                str(RUNNER),
                "--config",
                str(self.config),
                "--case",
                "toy-feature",
                "--run-id",
                "stable-test",
                "--output-dir",
                str(self.output_dir),
                "--codex-bin",
                str(self.fake_codex),
            ],
            ROOT,
        )

        run_dir = self.output_dir / "toy-feature/stable-test"
        manifest = yaml.safe_load((run_dir / "run.yaml").read_text(encoding="utf-8"))
        command = json.loads((run_dir / "codex-command.json").read_text(encoding="utf-8"))
        output = (run_dir / "codex-output.log").read_text(encoding="utf-8")
        report = (run_dir / "report.md").read_text(encoding="utf-8")
        prompt = (run_dir / "prompt.md").read_text(encoding="utf-8")

        self.assertIn("returncode: 0", result.stdout)
        self.assertEqual(manifest["returncode"], 0)
        self.assertEqual(manifest["repo"], str(self.repo.resolve()))
        self.assertIn(str(self.fake_codex), command[0])
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", command)
        self.assertIn('"has_feature": true', output)
        self.assertIn('"has_native_pipeline": true', output)
        self.assertIn('"no_direct_skill_invocations": true', output)
        self.assertIn("branch: nfp/toy-feature", report)
        self.assertIn("Do not create a git worktree", prompt)
        self.assertNotIn("Read and follow every NFP skill doc in order", prompt)
        self.assertNotIn("nfp-00-intake", prompt)
        self.assertNotIn("nfp-12-promote", prompt)
        self.assertTrue((self.output_dir / "summary-stable-test.yaml").exists())
        self.assertTrue((self.output_dir / "commands-stable-test.sh").exists())

    def test_dry_run_writes_prompt_without_invoking_codex(self):
        result = run(
            [
                sys.executable,
                str(RUNNER),
                "--config",
                str(self.config),
                "--case",
                "toy-feature",
                "--run-id",
                "dry",
                "--output-dir",
                str(self.output_dir),
                "--codex-bin",
                str(self.tempdir / "missing-codex"),
                "--dry-run",
            ],
            ROOT,
        )

        run_dir = self.output_dir / "toy-feature/dry"
        manifest = yaml.safe_load((run_dir / "run.yaml").read_text(encoding="utf-8"))
        self.assertIn("dry run: codex was not invoked", (run_dir / "codex-output.log").read_text(encoding="utf-8"))
        self.assertEqual(manifest["returncode"], 0)
        self.assertIn("summary:", result.stdout)

    def test_dirty_repo_is_rejected_before_codex_invocation(self):
        (self.repo / "README.md").write_text("# Dirty Repo\n", encoding="utf-8")

        result = run(
            [
                sys.executable,
                str(RUNNER),
                "--config",
                str(self.config),
                "--case",
                "toy-feature",
                "--run-id",
                "dirty",
                "--output-dir",
                str(self.output_dir),
                "--codex-bin",
                str(self.fake_codex),
            ],
            ROOT,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("repository is not clean", result.stderr)
        self.assertFalse((self.output_dir / "toy-feature/dirty/codex-output.log").exists())

    def test_runner_does_not_use_git_worktree_commands(self):
        content = RUNNER.read_text(encoding="utf-8")

        self.assertNotIn('"worktree"', content)
        self.assertNotIn("git worktree add", content)


if __name__ == "__main__":
    unittest.main()
