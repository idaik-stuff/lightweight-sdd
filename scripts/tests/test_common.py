import json
import os
from pathlib import Path
import unittest

from support import Fixture
from sdd.common import ConfigError, inside, load_json, repo_paths, snapshot


class CommonTests(Fixture):
    def test_duplicate_json_keys_rejected(self):
        path = self.write("bad.json", '{"version": 1, "version": 2}')
        with self.assertRaises(ConfigError):
            load_json(path)

    def test_nonfinite_json_rejected(self):
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value):
                with self.assertRaises(ConfigError):
                    load_json(self.write("bad.json", '{"value": ' + value + '}'))

    def test_json_must_be_object(self):
        with self.assertRaises(ConfigError):
            load_json(self.write("bad.json", "[]"))

    def test_unsafe_paths_rejected(self):
        for name in ("../outside", "/etc/passwd", "x/../../y", "a\\b", "C:/temp", ""):
            with self.subTest(name=name), self.assertRaises(ConfigError):
                inside(self.root, name)

    def test_symlink_escape_rejected(self):
        (self.root / "outside").symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaises(ConfigError):
            inside(self.root, "outside/x")

    def test_snapshot_archive_records_limitation(self):
        result = snapshot(self.root)
        self.assertEqual(result["source"], "archive-framework-only")
        self.assertIsNone(result["head"])

    def test_snapshot_changes_with_content(self):
        before = snapshot(self.root)
        self.write("README.md", "# Changed\n")
        self.assertNotEqual(before, snapshot(self.root))

    def test_snapshot_ignores_local_evidence(self):
        before = snapshot(self.root)
        self.write(".sdd/results/report.json", "{}")
        self.assertEqual(before, snapshot(self.root))

    @unittest.skipIf(os.name == "nt", "Windows does not expose the POSIX executable bit used by this archive-mode test")
    def test_snapshot_hashes_executable_bit(self):
        path = self.write("scripts/example", "pass\n")
        path.chmod(0o644)
        before = snapshot(self.root)
        path.chmod(0o755)
        self.assertNotEqual(before, snapshot(self.root))

    def test_git_snapshot_includes_untracked(self):
        self.init_git()
        before = snapshot(self.root)
        self.write("new.txt", "new")
        self.assertNotEqual(before, snapshot(self.root))

    def test_git_snapshot_detects_index_only_change(self):
        self.init_git()
        original = (self.root / "README.md").read_text()
        before = snapshot(self.root)
        self.write("README.md", "# Staged\n")
        self.git("add", "README.md")
        self.write("README.md", original)
        self.assertNotEqual(before, snapshot(self.root))

    def test_tracked_results_blocked(self):
        self.init_git()
        self.write(".sdd/results/report.json", "{}")
        self.git("add", "-f", ".sdd/results/report.json")
        with self.assertRaises(ConfigError):
            snapshot(self.root)

    def test_submodule_index_blocked(self):
        head = self.init_git()
        self.git("update-index", "--add", "--cacheinfo", f"160000,{head},submodule")
        with self.assertRaisesRegex(ConfigError, "Submodule"):
            snapshot(self.root)

    def test_skip_worktree_blocked(self):
        self.init_git()
        self.git("update-index", "--skip-worktree", "README.md")
        with self.assertRaisesRegex(ConfigError, "skip-worktree"):
            snapshot(self.root)

    def test_assume_unchanged_blocked(self):
        self.init_git()
        self.git("update-index", "--assume-unchanged", "README.md")
        with self.assertRaisesRegex(ConfigError, "assume-unchanged"):
            snapshot(self.root)
