#!/usr/bin/env python3
"""Read-only file inventory. Python 3.10+, standard library only.

Public output deliberately excludes names and paths. Private output MUST stay on
the server. This script does not identify people or interpret EEG data.
"""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
from collections import Counter
from contextlib import ExitStack
from datetime import datetime, timezone


FORMATS = {
    ".set": "eeglab_header_or_dataset", ".fdt": "eeglab_binary",
    ".vhdr": "brainvision_header", ".vmrk": "brainvision_markers",
    ".eeg": "eeg_binary_unspecified", ".bdf": "bdf", ".edf": "edf",
    ".cnt": "cnt_unspecified", ".mff": "mff", ".fif": "fif",
    ".fif.gz": "compressed_fif", ".mat": "matlab_container",
    ".zip": "archive", ".rar": "archive", ".7z": "archive",
    ".tar": "archive", ".gz": "archive", ".bz2": "archive",
    ".csv": "tabular", ".tsv": "tabular", ".xlsx": "spreadsheet",
    ".xls": "spreadsheet", ".json": "metadata_or_other",
    ".xml": "metadata_or_other", ".txt": "text_unspecified",
    ".md": "document", ".pdf": "document", ".docx": "document",
    ".npy": "numpy_container", ".npz": "numpy_container",
    ".h5": "hdf5_container", ".hdf5": "hdf5_container",
}
PUBLIC_FILES = ("file_inventory.csv", "errors.csv", "summary.json")
ALIAS = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,31}\Z", re.ASCII)


class ConfigurationError(Exception):
    """Message must contain only safe constants / validated aliases."""


class ChangedDuringScanError(Exception):
    pass


def opaque(prefix):
    return prefix + "_" + secrets.token_hex(16)


def overlaps(left, right):
    return left == right or left in right.parents or right in left.parents


def is_linklike(path):
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    )


def has_link_component(path):
    for part in reversed((path, *path.parents)):
        try:
            if is_linklike(part):
                return True
        except FileNotFoundError:
            continue
    return False


def normal_path(value):
    # absolute() preserves symlink components for checking before resolve().
    path = Path(value).expanduser().absolute()
    if has_link_component(path):
        raise ConfigurationError("SYMLINK_OR_REPARSE_COMPONENT_NOT_ALLOWED")
    return path.resolve(strict=False)


def classify(path):
    name = path.name.lower()
    suffix = ".fif.gz" if name.endswith(".fif.gz") else path.suffix.lower()
    if suffix in FORMATS:
        return suffix, FORMATS[suffix]
    return "other", "other"


def parse_config(args):
    roots = []
    for item in args.root:
        alias, separator, value = item.partition("=")
        if not separator or not ALIAS.fullmatch(alias) or not value:
            raise ConfigurationError("ROOT_REQUIRES_SAFE_ALIAS_EQUALS_PATH")
        if alias in {a for a, _ in roots}:
            raise ConfigurationError("DUPLICATE_ROOT_ALIAS: " + alias)
        try:
            root = normal_path(value)
            if not root.is_dir():
                raise ConfigurationError("ROOT_NOT_DIRECTORY_OR_MISSING: " + alias)
            with os.scandir(root):
                pass
        except OSError as exc:
            raise ConfigurationError(
                "ROOT_UNAVAILABLE: " + alias + " (" + type(exc).__name__ + ")"
            ) from None
        for _, other in roots:
            if overlaps(root, other):
                raise ConfigurationError("RAW_ROOTS_MUST_NOT_OVERLAP")
        roots.append((alias, root))
    try:
        public = normal_path(args.out)
        private = normal_path(args.private_out)
        if public.exists() or private.exists():
            raise ConfigurationError("OUTPUT_TARGET_ALREADY_EXISTS")
        if overlaps(public, private):
            raise ConfigurationError("PUBLIC_AND_PRIVATE_OUTPUT_TREES_MUST_BE_SEPARATE")
        for _, root in roots:
            if overlaps(public, root) or overlaps(private, root):
                raise ConfigurationError("OUTPUT_OVERLAPS_RAW_ROOT")
    except OSError as exc:
        raise ConfigurationError("OUTPUT_PATH_INVALID (" + type(exc).__name__ + ")") from None
    return roots, public, private


def exclusive_text(path, mode):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    return os.fdopen(descriptor, "w", encoding="utf-8", newline="")


def fingerprint(path, initial):
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or (
            opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns
        ) != (initial.st_dev, initial.st_ino, initial.st_size, initial.st_mtime_ns):
            raise ChangedDuringScanError()
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
        final = os.fstat(stream.fileno())
        if (opened.st_size, opened.st_mtime_ns) != (final.st_size, final.st_mtime_ns):
            raise ChangedDuringScanError()
        if is_linklike(path):
            raise ChangedDuringScanError()
        current = path.lstat()
        if (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns) != (
            opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns
        ):
            raise ChangedDuringScanError()
        return digest.hexdigest()


def scan(roots, public, private, use_hash=False):
    # New directories only; never remove existing output or write into raw roots.
    private.mkdir(mode=0o700, parents=True, exist_ok=False)
    if os.name == "posix":
        private.chmod(0o700)
    public.mkdir(parents=True, exist_ok=False)
    counts = Counter(files_enumerated=0, successful_files=0, failed_files=0,
                     skipped_entries=0, entry_metadata_errors=0,
                     directory_errors=0, error_count=0)
    suffix_counts, format_counts, root_counts = Counter(), Counter(), Counter()
    directory_format_counts = Counter()
    hash_counts = Counter()
    with ExitStack() as stack:
        inventory_stream = stack.enter_context(exclusive_text(public / "file_inventory.csv", 0o644))
        public_error_stream = stack.enter_context(exclusive_text(public / "errors.csv", 0o644))
        map_stream = stack.enter_context(exclusive_text(private / "file_path_map.csv", 0o600))
        private_error_stream = stack.enter_context(exclusive_text(private / "errors_private.csv", 0o600))
        inventory = csv.writer(inventory_stream)
        columns = ["file_id", "root_alias", "suffix", "format_category", "size_bytes"]
        if use_hash:
            columns.append("sha256")
        inventory.writerow(columns)
        public_errors, path_map, private_errors = map(csv.writer, (
            public_error_stream, map_stream, private_error_stream
        ))
        public_errors.writerow(["error_id", "root_alias", "error_class", "stage"])
        path_map.writerow(["file_id", "root_alias", "relative_path", "absolute_path"])
        private_errors.writerow(["error_id", "root_alias", "absolute_path", "error_class", "stage", "detail"])

        def record_error(alias, path, exc, stage):
            error_id = opaque("err")
            counts["error_count"] += 1
            public_errors.writerow([error_id, alias, type(exc).__name__, stage])
            private_errors.writerow([error_id, alias, str(path), type(exc).__name__, stage, repr(exc)])

        for alias, root in roots:
            root_counts[alias] = 0
            pending = [root]
            while pending:
                directory = pending.pop()
                try:
                    if is_linklike(directory):
                        counts["skipped_entries"] += 1
                        continue
                    with os.scandir(directory) as entries:
                        for entry in entries:
                            path = Path(entry.path)
                            try:
                                # DirEntry.stat may expose a zero inode on Windows;
                                # lstat gives the identity needed for safe hashing.
                                info = path.lstat()
                                if stat.S_ISLNK(info.st_mode) or bool(
                                    getattr(info, "st_file_attributes", 0)
                                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
                                ):
                                    counts["skipped_entries"] += 1
                                    continue
                                if stat.S_ISDIR(info.st_mode):
                                    if path.suffix.lower() == ".mff":
                                        directory_format_counts["mff_directory"] += 1
                                    pending.append(path)
                                    continue
                                if not stat.S_ISREG(info.st_mode):
                                    counts["skipped_entries"] += 1
                                    continue
                            except OSError as exc:
                                counts["entry_metadata_errors"] += 1
                                record_error(alias, path, exc, "entry_metadata")
                                continue
                            file_id = opaque("file")
                            suffix, category = classify(path)
                            counts["files_enumerated"] += 1
                            root_counts[alias] += 1
                            suffix_counts[suffix] += 1
                            format_counts[category] += 1
                            path_map.writerow([file_id, alias, str(path.relative_to(root)), str(path)])
                            row = [file_id, alias, suffix, category, info.st_size]
                            good = True
                            if use_hash:
                                digest = ""
                                try:
                                    digest = fingerprint(path, info)
                                    hash_counts[digest] += 1
                                except (OSError, ChangedDuringScanError) as exc:
                                    counts["failed_files"] += 1
                                    good = False
                                    record_error(alias, path, exc, "sha256")
                                row.append(digest)
                            inventory.writerow(row)
                            if good:
                                counts["successful_files"] += 1
                except OSError as exc:
                    counts["directory_errors"] += 1
                    record_error(alias, directory, exc, "directory_enumeration")

    summary = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "complete": counts["error_count"] == 0,
        "completeness_scope": "All regular files reachable without traversing symlinks or reparse points; no content validation.",
        "counts": dict(counts),
        "files_by_root_alias": dict(root_counts),
        "files_by_suffix": dict(suffix_counts),
        "files_by_format_category": dict(format_counts),
        "directory_format_counts": dict(directory_format_counts),
        "configuration": {"root_aliases": [alias for alias, _ in roots],
                          "sha256": use_hash, "follow_links": False,
                          "out": "PUBLIC_OUTPUT", "private_out": "PRIVATE_OUTPUT"},
        "statistical_unit_notice": "FILE COUNTS ARE NOT PARTICIPANT COUNTS. No child IDs, sessions, conditions, cohort membership, or EEG-to-clinical matches were inferred.",
        "privacy_notice": "Private output contains source names, paths, and error details; keep it on the server and do not share it. Use neutral aliases such as A and B. Hashes can enable cross-dataset matching; review before sharing.",
        "interpretation_notice": "Suffixes only identify possible formats. No waveforms were loaded, no archives extracted, no records paired, and no software installed. BIDS compliance and readability were not validated.",
        "read_only_notice": "No source file contents were written. Reading metadata or hashes may update access times according to the filesystem. Run against a stable directory tree.",
        "public_files": list(PUBLIC_FILES),
    }
    if use_hash:
        summary["content_duplicate_summary"] = {
            "hash_groups_with_multiple_files": sum(number > 1 for number in hash_counts.values()),
            "files_in_duplicate_hash_groups": sum(number for number in hash_counts.values() if number > 1),
            "notice": "Identical content only; not evidence of the same person or repeated visits.",
        }
    with exclusive_text(public / "summary.json", 0o644) as stream:
        json.dump(summary, stream, indent=2, ensure_ascii=True)
        stream.write("\n")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Read-only, de-identified first-pass file inventory (no EEG interpretation).",
        epilog="Keep private output on the server. Use neutral root aliases, e.g. A and B. Exit: 0 complete; 1 incomplete scan; 2 configuration/output failure.",
    )
    parser.add_argument("--root", action="append", required=True, metavar="ALIAS=PATH",
                        help="Repeat for each explicit non-overlapping raw directory; neutral ASCII alias, max 32 characters.")
    parser.add_argument("--out", required=True, help="New public output directory, separate from all raw and private directories.")
    parser.add_argument("--private-out", required=True,
                        help="New private output directory for paths and error details; never share this directory.")
    parser.add_argument("--sha256", action="store_true", help="Optionally read file bytes to compute SHA-256. Default only reads metadata.")
    try:
        args = parser.parse_args(argv)
        roots, public, private = parse_config(args)
        summary = scan(roots, public, private, args.sha256)
    except ConfigurationError as exc:
        print("Configuration failed: " + str(exc), file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        # No raw exception text: it often embeds source names and paths.
        print("Inventory failed: " + type(exc).__name__ + ". Output may be partial; use new output directories for a retry.", file=sys.stderr)
        return 2
    print("Inventory " + ("complete." if summary["complete"] else "incomplete; review errors.csv and private details on server."))
    print("File counts are not participant counts. Keep private output on the server.")
    return 0 if summary["complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
