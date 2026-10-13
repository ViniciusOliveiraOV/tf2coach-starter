from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.demo_sync import LIMIT_BYTES, copy_demo, discover_demo_dirs, is_open_by_any_process, sync_once


class DemoSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source_dir = self.root / "tf" / "tf2coach"
        self.source_dir.mkdir(parents=True)
        self.destination = self.root / "repo" / "data" / "demos"
        self.source = self.source_dir / "match.dem"
        self.source.write_bytes(b"completed demo bytes")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_copy_completed_demo_and_preserve_source(self) -> None:
        result = copy_demo(self.source, self.destination, is_open=lambda *_args, **_kwargs: False)
        copied = self.destination / self.source.name
        self.assertEqual(result, "copied")
        self.assertEqual(copied.read_bytes(), self.source.read_bytes())
        self.assertTrue(self.source.exists())

    def test_sync_once_copies_new_files_from_demo_directory(self) -> None:
        outcomes = sync_once([self.source_dir], self.destination, is_open=lambda *_a, **_k: False)
        self.assertEqual(outcomes, [(self.source, "copied")])
        self.assertEqual((self.destination / self.source.name).read_bytes(), self.source.read_bytes())

    def test_integrity_mismatch_is_not_published(self) -> None:
        good_hash = hashlib.sha256(self.source.read_bytes()).hexdigest()
        with patch("scripts.demo_sync._sha256_file", side_effect=(good_hash, "wrong-copy-hash")):
            result = copy_demo(self.source, self.destination, is_open=lambda *_a, **_k: False)
        self.assertEqual(result, "integrity_error")
        self.assertFalse((self.destination / self.source.name).exists())
        self.assertEqual(self.source.read_bytes(), b"completed demo bytes")

    def test_open_demo_is_never_copied(self) -> None:
        result = copy_demo(self.source, self.destination, is_open=lambda *_args, **_kwargs: True)
        self.assertEqual(result, "open")
        self.assertFalse(self.destination.exists())

    def test_file_reopened_during_copy_is_not_published(self) -> None:
        checks = iter((False, False, True))
        result = copy_demo(self.source, self.destination, is_open=lambda *_a, **_k: next(checks))
        self.assertEqual(result, "open")
        self.assertFalse((self.destination / self.source.name).exists())
        self.assertTrue(self.source.exists())

    def test_idempotent_same_file_and_no_overwrite_on_name_collision(self) -> None:
        self.destination.mkdir(parents=True)
        existing = self.destination / self.source.name
        existing.write_bytes(self.source.read_bytes())
        self.assertEqual(copy_demo(self.source, self.destination, is_open=lambda *_a, **_k: False), "duplicate")
        existing.write_bytes(b"different content")
        self.assertEqual(copy_demo(self.source, self.destination, is_open=lambda *_a, **_k: False), "conflict")
        self.assertEqual(existing.read_bytes(), b"different content")

    def test_same_content_under_another_name_is_not_duplicated(self) -> None:
        self.destination.mkdir(parents=True)
        (self.destination / "already-there.dem").write_bytes(self.source.read_bytes())
        self.assertEqual(copy_demo(self.source, self.destination, is_open=lambda *_a, **_k: False), "duplicate")
        self.assertFalse((self.destination / self.source.name).exists())

    def test_copy_respects_hard_2_gibibyte_limit_without_deleting(self) -> None:
        self.destination.mkdir(parents=True)
        old = self.destination / "old.dem"
        old.write_bytes(b"retained")
        result = copy_demo(
            self.source,
            self.destination,
            limit_bytes=old.stat().st_size + self.source.stat().st_size - 1,
            is_open=lambda *_a, **_k: False,
        )
        self.assertEqual(result, "limit")
        self.assertTrue(old.exists())
        self.assertFalse((self.destination / self.source.name).exists())
        self.assertEqual(LIMIT_BYTES, 2 * 1024**3)

    def test_rejects_non_demo_and_symlink(self) -> None:
        txt = self.source_dir / "notes.txt"
        txt.write_text("not a demo")
        self.assertEqual(copy_demo(txt, self.destination, is_open=lambda *_a, **_k: False), "ignored")
        link = self.source_dir / "linked.dem"
        link.symlink_to(self.source)
        self.assertEqual(copy_demo(link, self.destination, is_open=lambda *_a, **_k: False), "ignored")

    def test_proc_descriptor_check_detects_open_file(self) -> None:
        with self.source.open("rb"):
            self.assertTrue(is_open_by_any_process(self.source))
        self.assertFalse(is_open_by_any_process(self.source))

    def test_discovery_includes_secondary_steam_library(self) -> None:
        primary = self.root / "Steam"
        steamapps = primary / "steamapps"
        steamapps.mkdir(parents=True)
        vdf = steamapps / "libraryfolders.vdf"
        vdf.write_text(
            '"libraryfolders" {\n'
            f'  "0" {{ "path" "{primary}" }}\n'
            '  "1" { "path" "/secondary/Games\\\\Library" }\n'
            '}\n'
        )
        expected_primary = primary / "steamapps/common/Team Fortress 2/tf/tf2coach"
        expected_secondary = Path("/secondary/Games/Library/steamapps/common/Team Fortress 2/tf/tf2coach")
        actual = discover_demo_dirs([primary], library_file=vdf)
        self.assertEqual(actual, [expected_primary, expected_secondary])


if __name__ == "__main__":
    unittest.main()
