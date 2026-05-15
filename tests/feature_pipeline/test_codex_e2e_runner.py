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

    def write_template_case_config(self, prompt_profile=None):
        template = self.tempdir / "toy-template"
        template.mkdir()
        (template / "README.md").write_text("# Toy Template\n", encoding="utf-8")
        (template / "app.py").write_text('def greeting():\n    return "hello"\n', encoding="utf-8")
        case = {
            "title": "Toy Template Feature",
            "domain": "toy",
            "original_codebase": {
                "template_path": "toy-template",
                "base_ref": "HEAD",
            },
            "target_branch": "nfp/toy-template-feature",
            "feature_request": "Add a stable greeting feature to the template repository.",
            "expected_result": "Artifacts, implementation notes, tests, and final summary are produced.",
        }
        if prompt_profile:
            case["prompt_profile"] = prompt_profile
        config = self.tempdir / "template-cases.yaml"
        config.write_text(
            yaml.safe_dump(
                {
                    "artifact_contract_version": "0.1.0",
                    "cases": {"toy-template-feature": case},
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        return config, template

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
    "fresh_worktree": "fresh feature worktree" in prompt and "do not implement in the base checkout" in prompt,
    "has_agents_policy": "AGENTS.md" in prompt,
    "has_skills_context": "`skills`" in prompt,
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
        self.assertEqual(manifest["execution_mode"], "mock")
        self.assertFalse(manifest["uses_real_codex"])
        self.assertFalse(manifest["timed_out"])
        self.assertEqual(manifest["timeout_seconds"], 1800)
        self.assertTrue(Path(manifest["repo"]).is_dir())
        self.assertEqual(manifest["source_repo"], str(self.repo.resolve()))
        self.assertEqual(manifest["source_repo_kind"], "repo_path")
        self.assertEqual(manifest["prompt_profile"], "full-native")
        self.assertEqual(manifest["pipeline_fidelity"], "full")
        self.assertFalse(manifest["not_valid_for_full_pipeline_readiness"])
        self.assertEqual(manifest["path_mode"], "actual")
        self.assertIn("/worktrees/", manifest["repo"])
        self.assertIn(str(self.fake_codex), command[0])
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", command)
        self.assertIn('"has_feature": true', output)
        self.assertIn('"has_native_pipeline": true', output)
        self.assertIn('"no_direct_skill_invocations": true', output)
        self.assertIn('"fresh_worktree": true', output)
        self.assertIn('"has_agents_policy": true', output)
        self.assertIn('"has_skills_context": true', output)
        self.assertIn("branch: nfp/toy-feature", report)
        self.assertIn("- Pipeline fidelity: `full`", report)
        self.assertIn("- Valid for full pipeline readiness: `true`", report)
        self.assertIn("AGENTS.md", prompt)
        self.assertIn("fresh feature worktree", prompt)
        self.assertIn("do not implement in the base checkout", prompt)
        self.assertNotIn("Read and follow every NFP skill doc in order", prompt)
        self.assertNotIn("nfp-00-intake", prompt)
        self.assertNotIn("nfp-12-promote", prompt)
        self.assertTrue((Path(manifest["repo"]) / "AGENTS.md").exists())
        self.assertTrue((Path(manifest["repo"]) / ".agents/pipeline-core/references").exists())
        self.assertTrue((self.output_dir / "summary-stable-test.yaml").exists())
        self.assertTrue((self.output_dir / "commands-stable-test.sh").exists())

    def test_template_source_is_materialized_as_clean_git_repo(self):
        config, template = self.write_template_case_config(prompt_profile="outcome-smoke")

        run(
            [
                sys.executable,
                str(RUNNER),
                "--config",
                str(config),
                "--case",
                "toy-template-feature",
                "--run-id",
                "template-run",
                "--output-dir",
                str(self.output_dir),
                "--codex-bin",
                str(self.fake_codex),
                "--dry-run",
            ],
            ROOT,
        )

        run_dir = self.output_dir / "toy-template-feature/template-run"
        manifest = yaml.safe_load((run_dir / "run.yaml").read_text(encoding="utf-8"))
        source_repo = self.output_dir / "_source-repos/toy-template-feature/template-run"
        prompt = (run_dir / "prompt.md").read_text(encoding="utf-8")

        self.assertEqual(manifest["source_repo"], str(source_repo.resolve()))
        self.assertEqual(manifest["source_repo_kind"], "template_path")
        self.assertEqual(manifest["prompt_profile"], "outcome-smoke")
        self.assertEqual(manifest["pipeline_fidelity"], "partial")
        self.assertTrue(manifest["not_valid_for_full_pipeline_readiness"])
        self.assertEqual(manifest["path_mode"], "actual")
        report = (run_dir / "report.md").read_text(encoding="utf-8")
        self.assertIn("- Pipeline fidelity: `partial`", report)
        self.assertIn("- Valid for full pipeline readiness: `false`", report)
        self.assertTrue((source_repo / ".git").exists())
        self.assertEqual((source_repo / "README.md").read_text(encoding="utf-8"), "# Toy Template\n")
        self.assertEqual(run(["git", "status", "--short"], source_repo).stdout.strip(), "")
        self.assertTrue(run(["git", "rev-parse", "HEAD"], source_repo).stdout.strip())
        self.assertIn("bounded completion", prompt)
        self.assertIn("AGENTS.md", prompt)
        self.assertIn(".agents", prompt)
        self.assertIn(".ai/pipeline-docs", prompt)
        self.assertIn("normal user feature request", prompt)
        self.assertIn("current worktree is already provisioned", prompt)
        self.assertIn("do not create another worktree", prompt)
        self.assertIn("do not perform exhaustive pipeline expansion", prompt)
        self.assertIn(".ai/feature-workspaces/debug/toy-template-feature", prompt)
        self.assertIn("feature.md", prompt)
        self.assertIn("architecture.md", prompt)
        self.assertIn("tech-design.md", prompt)
        self.assertIn("slices.yaml", prompt)
        self.assertIn("smallest code and test change", prompt)
        self.assertIn("Run focused validation", prompt)
        self.assertIn("Commit the result", prompt)
        self.assertNotIn("Progress through these outcomes", prompt)
        self.assertNotIn("nfp-00-intake", prompt)
        self.assertNotIn("nfp-12-promote", prompt)
        self.assertEqual((template / "README.md").read_text(encoding="utf-8"), "# Toy Template\n")

    def test_case_source_must_define_exactly_one_repo_or_template(self):
        invalid_config = self.tempdir / "invalid-cases.yaml"
        invalid_config.write_text(
            yaml.safe_dump(
                {
                    "artifact_contract_version": "0.1.0",
                    "cases": {
                        "both": {
                            "original_codebase": {
                                "repo_path": "toy-repo",
                                "template_path": "toy-template",
                            },
                            "feature_request": "Do a thing.",
                        },
                        "neither": {
                            "original_codebase": {},
                            "feature_request": "Do a thing.",
                        },
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        for case_id in ("both", "neither"):
            result = run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--config",
                    str(invalid_config),
                    "--case",
                    case_id,
                    "--run-id",
                    f"invalid-{case_id}",
                    "--output-dir",
                    str(self.output_dir),
                    "--dry-run",
                ],
                ROOT,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exactly one of original_codebase.repo_path or original_codebase.template_path", result.stderr)

    def test_repeated_run_requires_explicit_worktree_replacement(self):
        base_args = [
            sys.executable,
            str(RUNNER),
            "--config",
            str(self.config),
            "--case",
            "toy-feature",
            "--run-id",
            "repeat",
            "--output-dir",
            str(self.output_dir),
            "--codex-bin",
            str(self.fake_codex),
            "--dry-run",
        ]
        run(base_args, ROOT)

        result = run(base_args, ROOT, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--replace-existing-worktree", result.stderr)

        replaced = run([*base_args, "--replace-existing-worktree"], ROOT)
        self.assertIn("returncode: 0", replaced.stdout)

    def test_prompt_profile_cli_override_wins_over_case_profile(self):
        config, _template = self.write_template_case_config(prompt_profile="full-native")

        run(
            [
                sys.executable,
                str(RUNNER),
                "--config",
                str(config),
                "--case",
                "toy-template-feature",
                "--run-id",
                "profile-override",
                "--output-dir",
                str(self.output_dir),
                "--codex-bin",
                str(self.fake_codex),
                "--prompt-profile",
                "outcome-smoke",
                "--dry-run",
            ],
            ROOT,
        )

        run_dir = self.output_dir / "toy-template-feature/profile-override"
        manifest = yaml.safe_load((run_dir / "run.yaml").read_text(encoding="utf-8"))
        prompt = (run_dir / "prompt.md").read_text(encoding="utf-8")
        self.assertEqual(manifest["prompt_profile"], "outcome-smoke")
        self.assertIn("bounded completion", prompt)
        self.assertIn("current worktree is already provisioned", prompt)
        self.assertIn(".ai/feature-workspaces/debug/toy-template-feature", prompt)
        self.assertNotIn("Progress through these outcomes", prompt)
        self.assertNotIn("nfp-00-intake", prompt)
        self.assertNotIn("nfp-12-promote", prompt)

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
        self.assertEqual(manifest["execution_mode"], "dry-run")
        self.assertFalse(manifest["uses_real_codex"])
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

    def test_runner_uses_fresh_git_worktree_commands(self):
        content = RUNNER.read_text(encoding="utf-8")

        self.assertIn('"worktree"', content)
        self.assertIn('"add"', content)
        self.assertIn("prepare_worktree", content)


if __name__ == "__main__":
    unittest.main()
