"""Synthetic-data-only tests; does not inspect the study's files."""

import contextlib
import csv
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "first_pass_inventory.py"
SPEC = importlib.util.spec_from_file_location("first_pass_inventory", SCRIPT)
inventory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.raw_a = self.base / "Alice_\u5f20\u4e09" / "raw"
        self.raw_b = self.base / "Bob_\u674e\u56db" / "raw"
        self.raw_a.mkdir(parents=True)
        self.raw_b.mkdir(parents=True)
        (self.raw_a / "\u5f20\u4e09.set").write_bytes(b"SYNTHETIC SAME CONTENT")
        (self.raw_a / "private.AliceSecret").write_bytes(b"unknown extension")
        (self.raw_b / "\u674e\u56db.edf").write_bytes(b"SYNTHETIC SAME CONTENT")
        self.public = self.base / "public"
        self.private = self.base / "private"

    def tearDown(self):
        self.temp.cleanup()

    def arguments(self):
        return ["--root", "A=" + str(self.raw_a), "--root", "B=" + str(self.raw_b),
                "--out", str(self.public), "--private-out", str(self.private)]

    def run_inventory(self, args=None):
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            code = inventory.main(args if args is not None else self.arguments())
        return code, captured.getvalue()

    def summary(self):
        return json.loads((self.public / "summary.json").read_text(encoding="utf-8"))

    def test_multiple_roots_privacy_and_no_source_byte_changes(self):
        before = {path: path.read_bytes() for root in (self.raw_a, self.raw_b) for path in root.rglob("*") if path.is_file()}
        code, terminal = self.run_inventory()
        self.assertEqual(code, 0, terminal)
        combined = terminal + "".join(path.read_text(encoding="utf-8") for path in self.public.iterdir())
        for private_word in ("Alice", "Bob", "\u5f20\u4e09", "\u674e\u56db", str(self.raw_a), str(self.base), "AliceSecret"):
            self.assertNotIn(private_word, combined)
        self.assertEqual(before, {path: path.read_bytes() for path in before})
        summary = self.summary()
        self.assertEqual(summary["counts"]["files_enumerated"], 3)
        self.assertEqual(summary["files_by_root_alias"], {"A": 2, "B": 1})
        self.assertIn("NOT PARTICIPANT", summary["statistical_unit_notice"])
        self.assertTrue(summary["complete"])
        self.assertIn("\u5f20\u4e09.set", (self.private / "file_path_map.csv").read_text(encoding="utf-8"))
        with (self.public / "file_inventory.csv").open(encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertNotIn("sha256", rows[0])
        self.assertEqual(len({row["file_id"] for row in rows}), 3)
        self.assertIn("other", {row["suffix"] for row in rows})

    def test_metadata_mode_does_not_read_file_content(self):
        with mock.patch.object(inventory, "fingerprint", side_effect=AssertionError("Must not read")):
            code, _ = self.run_inventory()
        self.assertEqual(code, 0)

    def test_existing_output_refused_without_overwrite(self):
        self.public.mkdir()
        sentinel = self.public / "keep.txt"
        sentinel.write_bytes(b"KEEP")
        code, terminal = self.run_inventory()
        self.assertEqual(code, 2)
        self.assertIn("ALREADY_EXISTS", terminal)
        self.assertEqual(sentinel.read_bytes(), b"KEEP")
        self.assertFalse(self.private.exists())

    def test_existing_private_output_refused(self):
        self.private.mkdir()
        code, terminal = self.run_inventory()
        self.assertEqual(code, 2, terminal)
        self.assertFalse(self.public.exists())

    def test_overlapping_raw_roots_refused(self):
        args = self.arguments()
        args[3] = "B=" + str(self.raw_a.parent)
        code, terminal = self.run_inventory(args)
        self.assertEqual(code, 2, terminal)
        self.assertIn("RAW_ROOTS_MUST_NOT_OVERLAP", terminal)

    def test_raw_overlap_and_output_tree_overlap_refused(self):
        for output, private in ((self.raw_a / "nested", self.private),
                                (self.public, self.raw_b / "nested"),
                                (self.public, self.public / "private")):
            args = ["--root", "A=" + str(self.raw_a), "--root", "B=" + str(self.raw_b),
                    "--out", str(output), "--private-out", str(private)]
            code, terminal = self.run_inventory(args)
            self.assertEqual(code, 2, terminal)
            self.assertFalse(output.exists())

    def test_duplicate_alias_and_unsafe_alias_refused(self):
        for alias in ("A", "\u5f20\u4e09", "A/../B", "x" * 33):
            args = self.arguments()
            args[3] = alias + "=" + str(self.raw_b)
            code, terminal = self.run_inventory(args)
            self.assertEqual(code, 2, terminal)
            self.assertFalse(self.public.exists())

    def test_missing_root_fails_without_exposing_path(self):
        args = self.arguments()
        args[1] = "A=" + str(self.base / "MissingPrivateName")
        code, terminal = self.run_inventory(args)
        self.assertEqual(code, 2)
        self.assertNotIn("MissingPrivateName", terminal)
        self.assertNotIn(str(self.base), terminal)
        self.assertFalse(self.public.exists())

    def test_unreadable_root_fails_explicitly(self):
        with mock.patch.object(inventory.os, "scandir", side_effect=PermissionError("Alice_\u5f20\u4e09 secret path")):
            code, terminal = self.run_inventory()
        self.assertEqual(code, 2)
        self.assertIn("ROOT_UNAVAILABLE", terminal)
        self.assertNotIn("Alice", terminal)
        self.assertFalse(self.public.exists())

    def test_traversal_permission_error_marks_incomplete(self):
        blocked = self.raw_a / "PrivateBlockedChild"
        blocked.mkdir()
        actual_scandir = os.scandir

        def controlled_scandir(path):
            if Path(path) == blocked:
                raise PermissionError("Alice_\u5f20\u4e09 at " + str(path))
            return actual_scandir(path)

        with mock.patch.object(inventory.os, "scandir", side_effect=controlled_scandir):
            code, terminal = self.run_inventory()
        self.assertEqual(code, 1, terminal)
        self.assertFalse(self.summary()["complete"])
        self.assertEqual(self.summary()["counts"]["directory_errors"], 1)
        public_errors = (self.public / "errors.csv").read_text(encoding="utf-8")
        self.assertIn("PermissionError", public_errors)
        self.assertNotIn("PrivateBlockedChild", public_errors)
        self.assertNotIn("Alice", public_errors)
        self.assertIn("PrivateBlockedChild", (self.private / "errors_private.csv").read_text(encoding="utf-8"))

    def test_hash_failure_marks_incomplete(self):
        with mock.patch.object(inventory, "fingerprint", side_effect=PermissionError("secret Alice")):
            code, terminal = self.run_inventory(self.arguments() + ["--sha256"])
        self.assertEqual(code, 1, terminal)
        summary = self.summary()
        self.assertFalse(summary["complete"])
        self.assertEqual(summary["counts"]["failed_files"], 3)
        self.assertEqual(summary["counts"]["successful_files"], 0)
        self.assertNotIn("Alice", (self.public / "errors.csv").read_text(encoding="utf-8"))

    def test_hash_only_reports_duplicate_content(self):
        code, terminal = self.run_inventory(self.arguments() + ["--sha256"])
        self.assertEqual(code, 0, terminal)
        duplicates = self.summary()["content_duplicate_summary"]
        self.assertEqual(duplicates["hash_groups_with_multiple_files"], 1)
        self.assertEqual(duplicates["files_in_duplicate_hash_groups"], 2)
        self.assertIn("not evidence of the same person", duplicates["notice"])

    def test_symlink_is_not_traversed(self):
        target = self.base / "outside"
        target.mkdir()
        (target / "OutsidePrivateName.edf").write_bytes(b"OUTSIDE")
        link = self.raw_a / "link"
        try:
            link.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("OS/account does not allow creating symlinks")
        code, terminal = self.run_inventory()
        self.assertEqual(code, 0, terminal)
        self.assertEqual(self.summary()["counts"]["files_enumerated"], 3)
        self.assertEqual(self.summary()["counts"]["skipped_entries"], 1)
        self.assertNotIn("OutsidePrivateName", (self.private / "file_path_map.csv").read_text(encoding="utf-8"))

    def test_symlink_root_refused(self):
        link = self.base / "raw_link"
        try:
            link.symlink_to(self.raw_a, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("OS/account does not allow creating symlinks")
        args = self.arguments()
        args[1] = "A=" + str(link)
        code, terminal = self.run_inventory(args)
        self.assertEqual(code, 2, terminal)

    @unittest.skipUnless(os.name == "nt", "Windows junction semantics only")
    def test_windows_junction_is_not_traversed(self):
        target = self.base / "junction_target"
        target.mkdir()
        (target / "OutsideName.edf").write_bytes(b"OUTSIDE")
        link = self.raw_a / "junction"
        # Test fixture only: create a junction in this test's temporary directory.
        quote = lambda value: "'" + str(value).replace("'", "''") + "'"
        command = "New-Item -ItemType Junction -Path " + quote(link) + " -Target " + quote(target) + " | Out-Null"
        try:
            result = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                                    capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except FileNotFoundError:
            self.skipTest("PowerShell unavailable for junction fixture")
        if result.returncode:
            self.skipTest("Account cannot create junction fixture")
        try:
            code, terminal = self.run_inventory()
            self.assertEqual(code, 0, terminal)
            self.assertEqual(self.summary()["counts"]["files_enumerated"], 3)
            self.assertEqual(self.summary()["counts"]["skipped_entries"], 1)
            self.assertNotIn("OutsideName", (self.private / "file_path_map.csv").read_text(encoding="utf-8"))
        finally:
            # Remove the junction itself only, never recursively touch its target.
            link.rmdir()
        self.assertEqual((target / "OutsideName.edf").read_bytes(), b"OUTSIDE")

    def test_mff_directories_and_companion_files_only_classified(self):
        mff = self.raw_a / "Patient.mff"
        mff.mkdir()
        (mff / "signal.bin").write_bytes(b"CONTENT")
        for suffix in (".fdt", ".vhdr", ".vmrk", ".eeg", ".bdf", ".cnt", ".fif", ".mat", ".zip", ".rar", ".7z"):
            (self.raw_b / ("Patient" + suffix)).write_bytes(b"CONTENT")
        code, terminal = self.run_inventory()
        self.assertEqual(code, 0, terminal)
        self.assertEqual(self.summary()["directory_format_counts"]["mff_directory"], 1)
        self.assertEqual(self.summary()["files_by_format_category"]["archive"], 3)

    @unittest.skipUnless(os.name == "posix", "POSIX permission semantics only")
    def test_private_permissions(self):
        code, terminal = self.run_inventory()
        self.assertEqual(code, 0, terminal)
        self.assertEqual(stat.S_IMODE(self.private.stat().st_mode), 0o700)
        for path in self.private.iterdir():
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)


if __name__ == "__main__":
    unittest.main()
