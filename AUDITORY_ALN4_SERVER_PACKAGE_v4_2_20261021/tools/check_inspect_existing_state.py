#!/usr/bin/env python3
"""Synthetic temporary-repository checks; never modifies a real checkout."""

import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

sys.dont_write_bytecode = True
import inspect_existing_state as intake


def git(repo, *args):
    env = intake._environment()
    env.update(GIT_AUTHOR_NAME="Fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
               GIT_COMMITTER_NAME="Fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid")
    result = subprocess.run(["git", "-c", f"core.hooksPath={os.devnull}", "-C", str(repo), *args],
                            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=15, env=env)
    return result.stdout.decode().strip()


def expect_error(call, code):
    try:
        call()
    except intake.IntakeError as exc:
        assert str(exc) == code, str(exc)
    else:
        raise AssertionError(f"expected {code}")


def verify():
    checks = []
    with tempfile.TemporaryDirectory(prefix="aln42_git_intake_fixture_") as directory:
        root = Path(directory); repo = root / "repository"; repo.mkdir()
        git(repo, "init", "--quiet")
        for relative in intake.SOURCE_PATHS + intake.REPORT_PATHS:
            path = repo / relative; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("synthetic fixture only\n", encoding="utf-8")
        git(repo, "add", "--", "."); git(repo, "commit", "--quiet", "-m", "fixture baseline")
        baseline = git(repo, "rev-parse", "HEAD")
        index = repo / ".git/index"
        original_index = (hashlib.sha256(index.read_bytes()).hexdigest(), index.stat().st_mtime_ns)
        clean = intake.inspect(repo, baseline)
        assert clean["status"] == "LOCAL_BASELINE_MATCH"
        assert clean["baseline"]["available"] and clean["baseline"]["ancestor_of_head"]
        assert all(x["head_matches_baseline"] and x["worktree_matches_head"] for x in clean["files"])
        assert original_index == (hashlib.sha256(index.read_bytes()).hexdigest(), index.stat().st_mtime_ns)
        checks.append("clean_baseline_three_way_hashes_and_index_unchanged")

        missing = intake.inspect(repo, "f" * 40)
        assert missing["status"] == "NEEDS_RECONCILIATION" and not missing["baseline"]["available"]
        checks.append("missing_baseline_does_not_pass_or_fetch")

        changed_path = repo / intake.SOURCE_PATHS[0]
        changed_path.write_text("synthetic changed source\n", encoding="utf-8")
        dirty = intake.inspect(repo, baseline)
        assert dirty["status"] == "NEEDS_RECONCILIATION"
        assert dirty["files"][0]["head_matches_baseline"] and not dirty["files"][0]["worktree_matches_head"]
        assert any(e["path"] == intake.SOURCE_PATHS[0] for e in dirty["git_status"]["entries"])
        checks.append("changed_key_file_has_separate_worktree_hash_and_status")

        git(repo, "add", "--", intake.SOURCE_PATHS[0]); git(repo, "commit", "--quiet", "-m", "fixture descendant")
        descendant = intake.inspect(repo, baseline)
        assert descendant["baseline"]["ancestor_of_head"] and descendant["status"] == "NEEDS_RECONCILIATION"
        assert not descendant["files"][0]["head_matches_baseline"] and descendant["files"][0]["worktree_matches_head"]
        checks.append("committed_key_change_is_not_confused_with_worktree_change")

        detached_root = git(repo, "commit-tree", "HEAD^{tree}", "-m", "independent fixture root")
        nonancestor = intake.inspect(repo, detached_root)
        assert nonancestor["baseline"]["available"] and nonancestor["baseline"]["ancestor_of_head"] is False
        assert nonancestor["status"] == "NEEDS_RECONCILIATION"
        checks.append("available_nonancestor_requires_reconciliation")

        destination = root / "intake.json"
        intake.write_report(clean, destination)
        saved = destination.read_bytes()
        expect_error(lambda: intake.write_report(dirty, destination), "OUTPUT_ALREADY_EXISTS")
        assert destination.read_bytes() == saved
        expect_error(lambda: intake.write_report(clean, repo / "new.json"), "OUTPUT_MUST_BE_OUTSIDE_REPOSITORY_AND_GIT_DIRS")
        assert not (repo / "new.json").exists()
        link = root / "alias_to_repo"; link.symlink_to(repo, target_is_directory=True)
        expect_error(lambda: intake.write_report(clean, link / "new.json"), "OUTPUT_MUST_BE_OUTSIDE_REPOSITORY_AND_GIT_DIRS")
        checks.append("exclusive_output_and_realpath_outside_repo_enforced")

        with patch.object(intake.subprocess, "run", side_effect=subprocess.TimeoutExpired(
                ["git"], 15, stderr=b"sensitive-placeholder-must-not-be-exported")):
            timed = intake._git(repo, ["rev-parse", "HEAD"], "TEST")
        assert timed == {"returncode": None, "stdout": b"", "error": "TEST:TIMEOUT"}
        checks.append("timeout_discards_stderr")

        cli_output = root / "fixed_baseline_cli.json"
        with contextlib.redirect_stdout(io.StringIO()):
            exit_code = intake.main(["--repo", str(repo), "--output", str(cli_output)])
        cli = json.loads(cli_output.read_text())
        assert exit_code == 2 and cli["baseline"]["requested_commit"] == intake.BASELINE
        assert cli["scope"]["live_queue"] == "NOT_CHECKED"
        checks.append("cli_fixed_baseline_and_no_live_queue_claim")
    return {"status": "PASS", "checks_passed": len(checks), "checks": checks,
            "real_checkout_mutated": False, "network_or_queue_used": False}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, allow_nan=False))
