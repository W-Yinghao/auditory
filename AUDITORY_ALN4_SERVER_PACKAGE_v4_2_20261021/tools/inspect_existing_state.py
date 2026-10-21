#!/usr/bin/env python3
"""Read-only LOCAL Git intake; no production imports, network, or queue checks.

Usage: python inspect_existing_state.py --repo /path/to/auditory \
    --output /existing/directory/outside/repo/new_intake.json

The CLI baseline is fixed. inspect(repo, baseline=...) exists for synthetic
fixtures, not as a CLI bypass. Exit 0 means locally recorded without relevant
differences; exit 2 means reconciliation or an input/output error. Neither
exit code is permission to run jobs or evidence about a live server queue.
"""

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess


BASELINE = "5d2960eee61a75c048f6b6ee3cef8427d945c3cd"
SOURCE_ROOT = "auditory_alignment_v3/aln41"
SOURCE_PATHS = tuple(f"{SOURCE_ROOT}/{name}.py" for name in (
    "source", "timebank", "temporal_objectives_torch", "support", "cross_stim",
    "readout", "frozen", "analysis_r2"))
REPORT_PATHS = (
    "docs/auditory_alignment_v3/aln41/ROUND1_REPORT.md",
    "docs/auditory_alignment_v3/aln41/R2_PLAN.md",
    "docs/auditory_alignment_v3/aln41/R2_CROSS_STIM_DECISION.md",
    "docs/auditory_alignment_v3/aln36/R2_BINDING.md",
)
RELEVANT_PATHS = (SOURCE_ROOT, "docs/auditory_alignment_v3/aln41", REPORT_PATHS[-1])
GIT_TIMEOUT_SECONDS = 15


class IntakeError(Exception):
    """Contains fixed safe error codes only, never Git stderr or file contents."""


def _environment():
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("GIT_"):
            del env[key]
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_LAZY_FETCH": "1", "GIT_ALLOW_PROTOCOL": "",
        "GIT_NO_REPLACE_OBJECTS": "1", "LC_ALL": "C",
    })
    return env


def _git(repo, arguments, phase):
    # No shell. Disable fsmonitor hooks, index-refresh locks, lazy fetching and
    # every transport. Missing partial-clone objects remain unavailable.
    command = ["git", "--no-optional-locks", "-c", "core.fsmonitor=false",
               "-c", "core.untrackedCache=false", "-c", "protocol.allow=never",
               "-c", "credential.helper=", "-C", str(repo), *arguments]
    try:
        result = subprocess.run(command, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=GIT_TIMEOUT_SECONDS, env=_environment(), check=False)
    except subprocess.TimeoutExpired:
        return {"returncode": None, "stdout": b"", "error": f"{phase}:TIMEOUT"}
    except OSError:
        return {"returncode": None, "stdout": b"", "error": f"{phase}:GIT_UNAVAILABLE"}
    # stderr can contain configured URLs or credentials on a broken clone;
    # never serialize, print, or interpolate it, even for local command errors.
    return {"returncode": result.returncode, "stdout": result.stdout,
            "error": None if result.returncode == 0 else f"{phase}:GIT_EXIT_{result.returncode}"}


def _text(result):
    return result["stdout"].decode("utf-8", errors="surrogateescape").strip()


def _within(path, root):
    return path == root or root in path.parents


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _at_commit(repo, commit, relative):
    if commit is None:
        return {"status": "COMMIT_UNAVAILABLE", "git_blob_id": None, "sha256": None}
    listed = _git(repo, ["ls-tree", "-z", "--full-tree", commit, "--", relative], "LS_TREE")
    if listed["returncode"] != 0:
        return {"status": "TREE_UNAVAILABLE", "git_blob_id": None, "sha256": None,
                "error": listed["error"]}
    entries = listed["stdout"].split(b"\0")
    entry = next((row for row in entries if row and row.split(b"\t", 1)[-1] == relative.encode()), None)
    if entry is None:
        return {"status": "MISSING_AT_COMMIT", "git_blob_id": None, "sha256": None}
    mode, kind, oid = entry.split(b"\t", 1)[0].decode("ascii").split()
    if kind != "blob":
        return {"status": "NOT_A_BLOB", "git_blob_id": oid, "sha256": None, "mode": mode}
    shown = _git(repo, ["show", "--no-ext-diff", "--no-textconv", f"{commit}:{relative}"], "SHOW_BLOB")
    result = {"status": "READ" if shown["returncode"] == 0 else "BLOB_UNAVAILABLE",
              "git_blob_id": oid, "sha256": None, "mode": mode}
    if shown["returncode"] == 0:
        result.update(sha256=_digest(shown["stdout"]), bytes=len(shown["stdout"]))
    else:
        result["error"] = shown["error"]
    return result


def _worktree_file(root, relative):
    path = root / relative
    try:
        if not _within(path.resolve(strict=False), root):
            return {"status": "OUTSIDE_WORKTREE_NOT_READ", "exists": path.exists(), "sha256": None}
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode):
            return {"status": "NONREGULAR_NOT_READ", "exists": True, "sha256": None}
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return {"status": "READ", "exists": True, "sha256": digest.hexdigest(), "bytes": info.st_size}
    except FileNotFoundError:
        return {"status": "MISSING", "exists": False, "sha256": None}
    except OSError:
        return {"status": "UNREADABLE", "exists": None, "sha256": None}


def _status_entries(raw):
    entries, rows, i = [], raw.split(b"\0"), 0
    while i < len(rows):
        row = rows[i]; i += 1
        if not row:
            continue
        if len(row) < 4 or row[2:3] != b" ":
            raise IntakeError("STATUS_FORMAT_UNRECOGNIZED")
        xy = row[:2].decode("ascii")
        item = {"xy": xy, "path": os.fsdecode(row[3:])}
        if "R" in xy or "C" in xy:
            if i >= len(rows) or not rows[i]:
                raise IntakeError("STATUS_RENAME_FORMAT_UNRECOGNIZED")
            item["original_path"] = os.fsdecode(rows[i]); i += 1
        entries.append(item)
    return entries


def inspect(repo, baseline=BASELINE):
    """Inspect local objects and files only. Custom baseline is for fixtures."""
    if not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", baseline):
        raise IntakeError("INVALID_BASELINE_OBJECT_ID")
    requested = Path(repo).resolve(strict=True)
    if not requested.is_dir():
        raise IntakeError("REPO_MUST_BE_A_DIRECTORY")
    report = {
        "schema_version": "aln4.existing_local_state.v1", "status": "NEEDS_RECONCILIATION",
        "repository": {"requested_path": str(requested), "worktree_root": None,
                       "git_dir": None, "git_common_dir": None, "head_commit": None},
        "baseline": {"requested_commit": baseline, "available": False, "ancestor_of_head": None},
        "files": [], "reasons": [],
        "scope": {"local_files_and_git_only": True, "live_queue": "NOT_CHECKED",
                  "server_private_assets": "NOT_CHECKED", "run_authorization": "NOT_ESTABLISHED",
                  "network_transports_disabled": True, "lazy_fetch_disabled": True,
                  "git_stderr_recorded": False, "production_modules_imported": False},
    }
    top = _git(requested, ["rev-parse", "--show-toplevel"], "WORKTREE_ROOT")
    if top["returncode"] != 0:
        report["reasons"].append(top["error"])
        return report
    root = Path(_text(top)).resolve(strict=True)
    report["repository"]["worktree_root"] = str(root)
    for field, option in (("git_dir", "--absolute-git-dir"), ("git_common_dir", "--git-common-dir")):
        result = _git(root, ["rev-parse", option], field.upper())
        if result["returncode"] == 0:
            candidate = Path(_text(result))
            report["repository"][field] = str((root / candidate).resolve())
        else:
            report["reasons"].append(result["error"])
    shallow = _git(root, ["rev-parse", "--is-shallow-repository"], "SHALLOW_STATUS")
    report["repository"]["shallow"] = _text(shallow) == "true" if shallow["returncode"] == 0 else None
    head_result = _git(root, ["rev-parse", "--verify", "HEAD^{commit}"], "HEAD")
    head = _text(head_result) if head_result["returncode"] == 0 else None
    report["repository"]["head_commit"] = head
    if head is None:
        report["reasons"].append(head_result["error"])
    base_result = _git(root, ["cat-file", "-e", f"{baseline}^{{commit}}"], "BASELINE_COMMIT")
    available = base_result["returncode"] == 0
    report["baseline"].update(available=available, equals_head=available and head == baseline)
    if not available:
        report["reasons"].append("BASELINE_NOT_AVAILABLE_LOCALLY")
        report["baseline"]["error"] = base_result["error"]
    if available and head:
        ancestor = _git(root, ["merge-base", "--is-ancestor", baseline, head], "BASELINE_ANCESTRY")
        report["baseline"]["ancestor_of_head"] = (ancestor["returncode"] == 0
                                                      if ancestor["returncode"] in (0, 1) else None)
        if ancestor["returncode"] != 0:
            report["reasons"].append("BASELINE_NOT_CONFIRMED_ANCESTOR_OF_HEAD")

    for path in SOURCE_PATHS + REPORT_PATHS:
        base = _at_commit(root, baseline if available else None, path)
        current = _at_commit(root, head, path)
        disk = _worktree_file(root, path)
        base_match = (current["sha256"] == base["sha256"] and current.get("mode") == base.get("mode")
                      if current["sha256"] and base["sha256"] else None)
        disk_match = disk["sha256"] == current["sha256"] if disk["sha256"] and current["sha256"] else None
        report["files"].append({"path": path, "kind": "SOURCE" if path in SOURCE_PATHS else "REPORT",
                                "baseline": base, "head": current, "worktree": disk,
                                "head_matches_baseline": base_match, "worktree_matches_head": disk_match})
        if base["status"] != "READ" or current["status"] != "READ" or disk["status"] != "READ":
            report["reasons"].append(f"KEY_PATH_UNAVAILABLE:{path}")
        if base_match is False:
            report["reasons"].append(f"HEAD_DIFFERS_FROM_BASELINE:{path}")
        if disk_match is False:
            report["reasons"].append(f"WORKTREE_DIFFERS_FROM_HEAD:{path}")

    status = _git(root, ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--", *RELEVANT_PATHS], "STATUS")
    entries = _status_entries(status["stdout"]) if status["returncode"] == 0 else []
    report["git_status"] = {"relevant_pathspecs": list(RELEVANT_PATHS), "complete": status["returncode"] == 0,
                            "entry_count": len(entries), "counts_by_xy": dict(Counter(x["xy"] for x in entries)),
                            "entries": entries, "unrelated_paths_not_listed": True}
    if status["returncode"] != 0:
        report["reasons"].append(status["error"])
    elif entries:
        report["reasons"].append("RELEVANT_WORKTREE_OR_INDEX_CHANGES")
    if not report["reasons"]:
        report["status"] = "LOCAL_BASELINE_MATCH" if head == baseline else "LOCAL_DESCENDANT_RECORDED"
    return report


def write_report(report, output):
    """Only permitted mutation: exclusively create one JSON outside repository."""
    original = Path(output)
    if original.exists() or original.is_symlink():
        raise IntakeError("OUTPUT_ALREADY_EXISTS")
    destination = original.resolve(strict=False)
    if not destination.parent.is_dir():
        raise IntakeError("OUTPUT_PARENT_MUST_EXIST")
    for field in ("requested_path", "worktree_root", "git_dir", "git_common_dir"):
        value = report["repository"].get(field)
        if value and _within(destination, Path(value).resolve()):
            raise IntakeError("OUTPUT_MUST_BE_OUTSIDE_REPOSITORY_AND_GIT_DIRS")
    encoded = json.dumps(report, ensure_ascii=True, indent=2, allow_nan=False) + "\n"
    try:
        with destination.open("x", encoding="utf-8") as handle:
            handle.write(encoded)
    except FileExistsError:
        raise IntakeError("OUTPUT_ALREADY_EXISTS") from None
    except OSError:
        raise IntakeError("OUTPUT_CREATE_FAILED") from None
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        report = inspect(args.repo)  # Fixed BASELINE; no CLI baseline option.
        destination = write_report(report, args.output)
    except (IntakeError, OSError) as exc:
        code = str(exc) if isinstance(exc, IntakeError) else "LOCAL_PATH_UNAVAILABLE"
        parser.exit(2, f"inspect_existing_state: {code}\n")
    print(json.dumps({"status": report["status"], "output": str(destination),
                      "live_queue": "NOT_CHECKED"}, allow_nan=False))
    return 2 if report["status"] == "NEEDS_RECONCILIATION" else 0


if __name__ == "__main__":
    raise SystemExit(main())
