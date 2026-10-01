import json
import os
from pathlib import Path
import unittest

from support import Fixture, ROOT
from sdd.changes import assess, changed_paths, load_rules, matches
from sdd.common import ConfigError


class ChangeTests(Fixture):
    def test_missing_git_is_error(self):
        with self.assertRaises(ConfigError):
            assess(self.root, "HEAD", "L0")

    def test_invalid_base_is_error_not_empty_pass(self):
        self.init_git()
        with self.assertRaises(ConfigError):
            assess(self.root, "does-not-exist", "L0")

    def test_option_injection_base_rejected(self):
        self.init_git()
        with self.assertRaises(ConfigError):
            assess(self.root, "--help", "L0")

    def test_empty_changes_blocked(self):
        base = self.init_git()
        self.assertEqual(assess(self.root, base, "L0")["status"], "blocked")

    def test_working_staged_untracked_and_deleted_paths(self):
        self.write("delete.md", "delete")
        base = self.init_git()
        self.write("README.md", "changed")
        self.git("add", "README.md")
        self.write("unstaged.txt", "new")
        (self.root / "delete.md").unlink()
        paths, _ = changed_paths(self.root, base)
        self.assertEqual(set(paths), {"README.md", "delete.md", "unstaged.txt"})

    def test_committed_branch_change_included(self):
        base = self.init_git()
        self.write("branch.txt", "committed")
        self.git("add", ".")
        self.git("commit", "-qm", "Branch change")
        paths, _ = changed_paths(self.root, base)
        self.assertIn("branch.txt", paths)

    def test_staged_change_masked_by_worktree_is_included(self):
        base = self.init_git()
        old = (self.root / "README.md").read_text()
        self.write("README.md", "staged")
        self.git("add", "README.md")
        self.write("README.md", old)
        self.assertIn("README.md", changed_paths(self.root, base)[0])

    def test_rename_out_of_sensitive_path_still_matches(self):
        self.write("api/public.txt", "contract")
        base = self.init_git()
        self.git("mv", "api/public.txt", "moved.txt")
        report = assess(self.root, base, "L1")
        self.assertEqual(report["detected_floor"], "L3")
        self.assertEqual(set(report["paths"]), {"api/public.txt", "moved.txt"})
        self.assertEqual(report["status"], "failed")

    def test_new_untracked_sensitive_path_raises_floor(self):
        base = self.init_git()
        self.write("api/new.txt", "contract")
        self.assertEqual(assess(self.root, base, "L0")["required_level"], "L3")

    @unittest.skipIf(os.name == "nt", "Windows filenames cannot contain newline characters")
    def test_filename_spaces_and_newlines_preserved(self):
        base = self.init_git()
        self.write("api/a b\nc.txt", "contract")
        self.assertIn("api/a b\nc.txt", changed_paths(self.root, base)[0])

    def test_no_match_does_not_lower_declared_level(self):
        base = self.init_git()
        ident = self.change(level="L3")
        report = assess(self.root, base, "L3", ident, "broad")
        self.assertEqual(report["detected_floor"], "L0")
        self.assertEqual(report["required_level"], "L3")
        self.assertEqual(report["status"], "passed")

    def test_l3_focused_fails(self):
        base = self.init_git()
        ident = self.change(level="L3")
        self.assertEqual(assess(self.root, base, "L3", ident, "focused")["status"], "failed")

    def test_l2_requires_change_documents(self):
        base = self.init_git()
        self.write("README.md", "change")
        self.assertEqual(assess(self.root, base, "L2")["status"], "failed")

    def test_spec_level_mismatch_fails(self):
        base = self.init_git()
        ident = self.change("L2")
        report = assess(self.root, base, "L3", ident, "broad")
        self.assertIn("The spec's Level differs", " ".join(report["errors"]))

    def test_results_not_treated_as_changes(self):
        base = self.init_git()
        self.write(".sdd/results/report.json", "{}")
        self.assertEqual(changed_paths(self.root, base)[0], [])

    def test_no_git_writes(self):
        base = self.init_git()
        self.write("README.md", "change")
        before = self.git("status", "--porcelain")
        assess(self.root, base, "L1")
        self.assertEqual(before, self.git("status", "--porcelain"))

    def test_root_and_nested_patterns(self):
        for path in ("openapi.yaml", "service/openapi.yaml", "deep/service/openapi.yaml"):
            with self.subTest(path=path):
                self.assertTrue(matches(path, "**/openapi*.yaml"))
        self.assertFalse(matches("service/private.json", "**/openapi*.json"))

    def test_duplicate_rule_id_rejected(self):
        data = json.loads((self.root / ".sdd/risk-rules.json").read_text())
        data["rules"].append(data["rules"][0])
        self.rules(data)
        with self.assertRaises(ConfigError):
            load_rules(self.root)

    def test_shipped_rules_are_valid(self):
        self.assertGreater(len(load_rules(ROOT)), 0)

    def test_invalid_minimum_level_type_rejected_cleanly(self):
        data = json.loads((self.root / ".sdd/risk-rules.json").read_text())
        data["rules"][0]["minimum_level"] = []
        self.rules(data)
        with self.assertRaises(ConfigError):
            load_rules(self.root)

    def test_conflicted_worktree_blocked(self):
        base = self.init_git()
        initial = self.git("branch", "--show-current")
        self.git("checkout", "-qb", "other")
        self.write("README.md", "other branch")
        self.git("add", "README.md")
        self.git("commit", "-qm", "Other")
        self.git("checkout", "-q", initial)
        self.write("README.md", "initial branch")
        self.git("add", "README.md")
        self.git("commit", "-qm", "Initial")
        self.git("merge", "other", check=False)
        with self.assertRaisesRegex(ConfigError, "Unresolved merge conflicts"):
            changed_paths(self.root, base)
