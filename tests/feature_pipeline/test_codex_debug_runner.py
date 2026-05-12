import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEBUG_RUNNER = ROOT / "pipeline-lab/showcases/scripts/run_codex_debug_pipeline.py"


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def assert_no_absolute_path(testcase, path, forbidden_root):
    content = path.read_text(encoding="utf-8")
    testcase.assertNotIn(str(forbidden_root), content, f"{path} leaked {forbidden_root}")


class CodexDebugRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="codex-debug-test-"))
        self.repo = self.make_repo()
        self.config = self.write_case_config()
        self.output_dir = self.tempdir / "debug-runs"

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

    def test_mock_mode_runs_nested_e2e_and_validates_artifacts(self):
        result = run(
            [
                sys.executable,
                str(DEBUG_RUNNER),
                "--config",
                str(self.config),
                "--case",
                "toy-feature",
                "--run-id",
                "stable-debug",
                "--output-dir",
                str(self.output_dir),
                "--mode",
                "mock",
                "--clean",
            ],
            ROOT,
        )

        run_dir = self.output_dir / "stable-debug"
        summary = yaml.safe_load((run_dir / "summary.yaml").read_text(encoding="utf-8"))
        validation = (run_dir / "validation.md").read_text(encoding="utf-8")
        comparison = (run_dir / "comparison.md").read_text(encoding="utf-8")
        e2e_run = yaml.safe_load((run_dir / "e2e/toy-feature/stable-debug/run.yaml").read_text(encoding="utf-8"))
        repo = Path(e2e_run["repo"])

        self.assertIn("status: pass", result.stdout)
        self.assertEqual(summary["mode"], "mock")
        self.assertFalse(summary["uses_real_codex"])
        self.assertEqual(summary["status"], "pass")
        self.assertEqual(summary["case_count"], 1)
        self.assertTrue(summary["comparison"]["current_unit_tests_use_fake_codex"])
        self.assertEqual(summary["results"][0]["artifact_source"], "changed_files")
        self.assertEqual(e2e_run["execution_mode"], "mock")
        self.assertFalse(e2e_run["uses_real_codex"])
        self.assertTrue((repo / ".ai/feature-workspaces/debug/toy-feature/feature.md").exists())
        self.assertTrue((repo / ".ai/feature-workspaces/debug/toy-feature/architecture.md").exists())
        self.assertIn("0 | `pass`", validation)
        self.assertIn("Uses fake Codex: `true`", comparison)
        self.assertIn("explicit execution_mode", comparison)

    def test_clean_rerun_forwards_replacement_and_prompt_profile(self):
        base_cmd = [
            sys.executable,
            str(DEBUG_RUNNER),
            "--config",
            str(self.config),
            "--case",
            "toy-feature",
            "--run-id",
            "stable-rerun",
            "--output-dir",
            str(self.output_dir),
            "--mode",
            "mock",
            "--prompt-profile",
            "outcome-smoke",
            "--clean",
        ]

        first = run(base_cmd, ROOT)
        second = run(base_cmd, ROOT)

        run_dir = self.output_dir / "stable-rerun"
        summary = yaml.safe_load((run_dir / "summary.yaml").read_text(encoding="utf-8"))
        e2e_run = yaml.safe_load((run_dir / "e2e/toy-feature/stable-rerun/run.yaml").read_text(encoding="utf-8"))
        command = (run_dir / "debug-command.sh").read_text(encoding="utf-8")
        prompt = (run_dir / "e2e/toy-feature/stable-rerun/prompt.md").read_text(encoding="utf-8")

        self.assertIn("status: pass", first.stdout)
        self.assertIn("status: pass", second.stdout)
        self.assertEqual(summary["status"], "pass")
        self.assertEqual(e2e_run["prompt_profile"], "outcome-smoke")
        self.assertIn("--prompt-profile outcome-smoke", command)
        self.assertIn("--replace-existing-worktree", command)
        self.assertIn("bounded completion smoke case", prompt)
        self.assertNotIn("nfp-00-intake", prompt)
        self.assertNotIn("nfp-12-promote", prompt)

    def test_portable_output_removes_local_paths_from_reports(self):
        result = run(
            [
                sys.executable,
                str(DEBUG_RUNNER),
                "--config",
                str(self.config),
                "--case",
                "toy-feature",
                "--run-id",
                "portable-debug",
                "--output-dir",
                str(self.output_dir),
                "--mode",
                "mock",
                "--portable-output",
                "--clean",
            ],
            ROOT,
        )

        run_dir = self.output_dir / "portable-debug"
        summary = yaml.safe_load((run_dir / "summary.yaml").read_text(encoding="utf-8"))
        self.assertIn("status: pass", result.stdout)
        self.assertEqual(summary["path_mode"], "portable")
        self.assertIn("$RUN_DIR", (run_dir / "summary.yaml").read_text(encoding="utf-8"))
        self.assertIn("$WORK_ROOT", (run_dir / "summary.yaml").read_text(encoding="utf-8"))
        for artifact in (
            run_dir / "summary.yaml",
            run_dir / "validation.md",
            run_dir / "comparison.md",
            run_dir / "e2e/summary-portable-debug.yaml",
            run_dir / "e2e/commands-portable-debug.sh",
            run_dir / "e2e/toy-feature/portable-debug/run.yaml",
            run_dir / "e2e/toy-feature/portable-debug/prompt.md",
            run_dir / "e2e/toy-feature/portable-debug/codex-command.json",
            run_dir / "e2e/toy-feature/portable-debug/report.md",
        ):
            assert_no_absolute_path(self, artifact, self.tempdir)
            assert_no_absolute_path(self, artifact, ROOT)

    def test_real_mode_accepts_executable_shim_that_completes_artifacts(self):
        codex_shim = self.tempdir / "codex-completion-shim"
        codex_shim.write_text(
            """#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path

args = sys.argv[1:]
if not args or args[0] != "exec":
    raise SystemExit("shim only supports exec")
repo = Path(args[args.index("-C") + 1])
out = Path(args[args.index("-o") + 1])
prompt = args[-1]
case_match = re.search(r"Case id:\\s*([^\\n]+)", prompt)
branch_match = re.search(r"Target branch name:\\s*([^\\n]+)", prompt)
case_id = (case_match.group(1).strip() if case_match else "real-feature").replace("/", "-")
branch = branch_match.group(1).strip() if branch_match else "real-branch"
workspace = repo / ".ai" / "feature-workspaces" / "debug" / case_id
workspace.mkdir(parents=True, exist_ok=True)
artifacts = {
    "feature.md": f"# Feature: {case_id}\\n",
    "architecture.md": "# Architecture\\n\\n## Feature Topology\\n\\n```mermaid\\ngraph TD\\n  A --> B\\n```\\n",
    "tech-design.md": "# Technical Design\\n",
    "slices.yaml": "slices:\\n  - id: S-001\\n    status: complete\\n",
}
for name, content in artifacts.items():
    (workspace / name).write_text(content, encoding="utf-8")
(repo / "README.codex-real-shim.md").write_text("# Real shim completion\\n", encoding="utf-8")
subprocess.run(["git", "add", "."], cwd=repo, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
subprocess.run(["git", "commit", "-m", f"Complete {case_id}"], cwd=repo, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout.strip()
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(f"branch: {branch}\\ncommit: {commit}\\n", encoding="utf-8")
print(json.dumps({"repo": str(repo), "branch": branch, "commit": commit}))
""",
            encoding="utf-8",
        )
        codex_shim.chmod(0o755)

        result = run(
            [
                sys.executable,
                str(DEBUG_RUNNER),
                "--config",
                str(self.config),
                "--case",
                "toy-feature",
                "--run-id",
                "real-shim",
                "--output-dir",
                str(self.output_dir),
                "--mode",
                "real",
                "--codex-bin",
                str(codex_shim),
                "--prompt-profile",
                "outcome-smoke",
                "--clean",
            ],
            ROOT,
        )

        summary = yaml.safe_load((self.output_dir / "real-shim/summary.yaml").read_text(encoding="utf-8"))
        self.assertIn("uses_real_codex: true", result.stdout)
        self.assertEqual(summary["status"], "pass")
        self.assertTrue(summary["uses_real_codex"])
        self.assertEqual(summary["results"][0]["status"], "pass")
        self.assertEqual(summary["results"][0]["artifact_source"], "changed_files")
        self.assertNotIn("fake", summary["codex_bin"].lower())
        self.assertNotIn("mock", summary["codex_bin"].lower())

    def test_real_mode_fails_fast_when_codex_binary_is_missing(self):
        result = run(
            [
                sys.executable,
                str(DEBUG_RUNNER),
                "--config",
                str(self.config),
                "--case",
                "toy-feature",
                "--run-id",
                "missing-real",
                "--output-dir",
                str(self.output_dir),
                "--mode",
                "real",
                "--codex-bin",
                str(self.tempdir / "missing-codex"),
                "--clean",
            ],
            ROOT,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("real Codex executable is missing", result.stderr)
        self.assertFalse((self.output_dir / "missing-real/summary.yaml").exists())


if __name__ == "__main__":
    unittest.main()
