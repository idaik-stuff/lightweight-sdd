"""Installer tests: this checkout is the source, fixture repositories are the targets."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import unittest
from unittest import mock

from support import Fixture, ROOT
from sdd import install
from sdd.install import MIGRATION, main, run

README = "# Product\n\n## Commands\n\nNone yet.\n"


def source_is_checkout():
    result = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.returncode == 0 and Path(result.stdout.strip()).resolve() == ROOT.resolve()


def can_symlink(folder):
    try:
        os.symlink("missing-target", folder / "probe-link")
    except (OSError, NotImplementedError):
        return False
    os.unlink(folder / "probe-link")
    return True


@unittest.skipUnless(source_is_checkout(), "The installer needs a framework Git checkout as its source")
class InstallTests(Fixture):
    def setUp(self):
        super().setUp()
        for name in (".sdd/verification.json", ".sdd/risk-rules.json"):
            (self.root / name).unlink()
        (self.root / ".sdd").rmdir()
        (self.root / ".gitignore").unlink()
        (self.root / "README.md").unlink()
        self.write("LICENSE", "MIT\n")
        self.init_git()
        self.git("checkout", "-q", "-b", "chg-000-install-sdd")

    def install(self, clients="claude", dry_run=False, target=None):
        # Development checkouts are dirty by nature; the dirty-source refusal has its own test.
        with contextlib.redirect_stdout(io.StringIO()):
            return run(target or self.root, clients, dry_run, allow_dirty_source=True)

    def files(self):
        return sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob("*")
                      if p.is_file() and ".git" not in p.relative_to(self.root).parts)

    def snapshot(self):
        return {p: hashlib.sha256((self.root / p).read_bytes()).hexdigest() for p in self.files()}

    def commit(self, message="Install"):
        self.git("add", "-A")
        self.git("commit", "-qm", message)

    def assert_refused(self, clients="claude", **kwargs):
        before = self.snapshot()
        code, report = self.install(clients, **kwargs)
        self.assertNotEqual(code, 0)
        self.assertEqual(self.snapshot(), before)
        return report

    def collisions(self, report):
        return [path for kind, path in report["actions"] if kind == "collision"]

    def test_fresh_install_for_one_client(self):
        code, report = self.install("claude")
        self.assertEqual((code, report["status"], report["mode"]), (0, "done", "install"))
        files = set(self.files())
        for path in ("AGENTS.md", "CLAUDE.md", ".claude/skills/sdd-implement/SKILL.md",
                     ".claude/agents/sdd-independent-review.md", ".agents/workflows/spec/SKILL.md",
                     ".agents/review/independent-review.md", ".agents/evals/scenarios.md",
                     ".github/workflows/sdd.yml", "scripts/verify", "scripts/hooks/pre-push",
                     "docs/development/commands.md", "docs/templates/spec.md", "docs/project-rules.md",
                     "docs/product/brief.md", ".sdd/verification.json", ".sdd/install.json", "README.md"):
            with self.subTest(path=path):
                self.assertIn(path, files)
        for prefix in (".agents/tools/", ".agents/adapters/", ".agents/skills/", ".cursor/", ".codex/",
                       ".github/agents/", "docs/manual/", "docs/specs/CHG-"):
            with self.subTest(excluded=prefix):
                self.assertFalse([p for p in files if p.startswith(prefix)])
        for path in ("scripts/install", "scripts/sdd/install.py", "scripts/tests/test_install.py",
                     "CHANGELOG.md", ".github/copilot-instructions.md"):
            with self.subTest(excluded=path):
                self.assertNotIn(path, files)
        self.assertEqual((self.root / "LICENSE").read_text(), "MIT\n")
        self.assertIn("## Commands", (self.root / "README.md").read_text())
        record = json.loads((self.root / ".sdd/install.json").read_text())
        head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], stdout=subprocess.PIPE, text=True).stdout.strip()
        self.assertEqual((record["clients"], record["framework_commit"]), (["claude"], head))
        self.assertTrue(record["framework_version"])
        self.assertIn("AGENTS.md", record["files"])
        self.assertNotIn("docs/product/brief.md", record["files"])
        checks = json.loads((self.root / ".sdd/verification.json").read_text())["checks"]
        self.assertFalse({"adapters", "adapter-tests"} & {c["id"] for c in checks})
        owners = (self.root / ".github/CODEOWNERS.example").read_text()
        self.assertIn("/.claude/", owners)
        self.assertNotIn("/.cursor/", owners)

    @unittest.skipIf(os.name == "nt", "POSIX permission bits")
    def test_written_files_have_checkout_permissions(self):
        self.assertEqual(self.install()[0], 0)
        self.assertEqual(stat.S_IMODE((self.root / "AGENTS.md").stat().st_mode), 0o644)
        self.assertEqual(stat.S_IMODE((self.root / "scripts/hooks/pre-push").stat().st_mode), 0o755)

    def test_client_selection(self):
        code, _ = self.install("codex,cursor")
        self.assertEqual(code, 0)
        files = set(self.files())
        self.assertIn(".agents/skills/sdd-plan/SKILL.md", files)
        self.assertIn(".codex/agents/sdd-independent-review.toml", files)
        self.assertIn(".cursor/agents/sdd-independent-review.md", files)
        self.assertFalse([p for p in files if p.startswith((".claude/", ".github/agents/"))])
        self.assertNotIn("CLAUDE.md", files)

    def test_installed_product_passes_its_own_checks(self):
        self.assertEqual(self.install("claude")[0], 0)
        for argv in (["scripts/check-docs"], ["scripts/verify", "focused", "--target", "framework"]):
            with self.subTest(argv=argv):
                result = subprocess.run([sys.executable, *argv], cwd=self.root, env=self.git_env(),
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_refuses_default_branch(self):
        self.git("checkout", "-q", self.default_branch)
        self.assertIn("default branch", self.assert_refused()["reason"])

    def test_refuses_dirty_worktree(self):
        self.write("notes.txt", "draft")
        self.assertIn("uncommitted", self.assert_refused()["reason"])

    def test_refuses_unknown_client_and_nested_target(self):
        self.assertIn("Choose one or more", self.assert_refused("claude,vim")["reason"])
        self.write("sub/keep.txt", "x"); self.commit("sub")
        code, report = self.install(target=self.root / "sub")
        self.assertEqual(code, 2)
        self.assertIn("repository root", report["reason"])

    def test_refuses_the_framework_checkout_itself(self):
        with mock.patch.object(install, "target_checks", wraps=install.target_checks):
            code, report = self.install(target=ROOT)
        self.assertEqual(code, 2)
        self.assertIn("framework checkout itself", report["reason"])

    def test_refuses_dirty_source_without_flag(self):
        real = install.git

        def dirty(root, *args):
            if Path(root) == ROOT and args[:1] == ("status",):
                return b"?? stray-notes.txt\n"
            return real(root, *args)

        before = self.snapshot()
        with mock.patch.object(install, "git", dirty), contextlib.redirect_stdout(io.StringIO()):
            code, report = run(self.root, "claude", False)
        self.assertEqual(code, 2)
        self.assertIn("--allow-dirty-source", report["reason"])
        self.assertEqual(self.snapshot(), before)

    def test_collisions_are_listed_and_nothing_is_written(self):
        self.write("AGENTS.md", "# Our own rules\n")
        self.write("README.md", "# Product\n\nNo commands section.\n")
        self.write(".gitignore", "node_modules/\n")
        self.write(".gitattributes", "*.png binary\n")
        self.commit("existing files")
        report = self.assert_refused()
        collisions = self.collisions(report)
        self.assertIn("AGENTS.md", collisions)
        self.assertTrue(any(c.startswith("README.md") for c in collisions))
        self.assertTrue(any(c.startswith(".gitignore") for c in collisions))
        self.assertTrue(any(c.startswith(".gitattributes") for c in collisions))
        dry = self.assert_refused(dry_run=True)
        self.assertEqual(dry["actions"], report["actions"])

    def test_file_where_a_directory_is_needed_is_a_collision(self):
        self.write("scripts", "not a directory\n"); self.commit("file named scripts")
        report = self.assert_refused()
        self.assertTrue(any(c.startswith("scripts/verify (scripts is not a directory)") for c in self.collisions(report)))

    def test_symlinks_are_collisions(self):
        if not can_symlink(self.root):
            self.skipTest("Symlinks are not available")
        os.symlink("../outside", self.root / ".gitignore")
        (self.root / "elsewhere").mkdir(); self.write("elsewhere/keep.txt", "x")
        os.symlink("elsewhere", self.root / "docs")
        self.commit("links")
        collisions = self.collisions(self.assert_refused())
        self.assertTrue(any(c.startswith(".gitignore (symlink") for c in collisions))
        self.assertTrue(any(c.startswith("docs/") and "symlink at docs" in c for c in collisions))

    def test_dry_run_reports_and_writes_nothing(self):
        before = self.snapshot()
        code, report = self.install(dry_run=True)
        self.assertEqual((code, report["status"]), (0, "dry-run"))
        self.assertTrue(any(kind == "create" for kind, _ in report["actions"]))
        self.assertEqual(self.snapshot(), before)
        self.git("checkout", "-q", self.default_branch)
        self.assertEqual(self.assert_refused(dry_run=True)["status"], "refused")

    def test_unrelated_sdd_directory_is_refused(self):
        self.write(".sdd/notes.txt", "other tool\n"); self.commit("other .sdd")
        self.assertIn("not a framework installation", self.assert_refused()["reason"])

    def test_framework_1_0_target_needs_migration(self):
        self.write("scripts/sdd/__init__.py", "")
        self.write(".agents/tools/sync_adapters.py", "# old generator\n")
        self.write(".sdd/verification.json", json.dumps({"checks": [{"id": "adapters"}]}))
        self.write("AGENTS.md", "# Rules\n\nOur own rule.\n")
        self.commit("1.0.0 layout")
        self.assertEqual(self.assert_refused()["reason"], MIGRATION)
        self.assertIn("product-risk-rules.json", MIGRATION)

    def test_migrated_1_0_target_upgrades_and_gains_missing_stubs(self):
        self.write("scripts/sdd/__init__.py", "")
        self.write(".sdd/verification.json", json.dumps({"checks": [{"id": "docs"}]}))
        self.write("README.md", README)
        self.commit("migrated 1.0.0 layout")
        self.assertIn("--clients", self.assert_refused(None)["reason"])
        code, report = self.install("claude")
        self.assertEqual((code, report["mode"]), (0, "upgrade"))
        self.assertTrue((self.root / "docs/project-rules.md").is_file())
        self.assertEqual(json.loads((self.root / ".sdd/verification.json").read_text()), {"checks": [{"id": "docs"}]})

    def test_upgrade_keeps_product_files_and_recorded_clients(self):
        self.assertEqual(self.install("claude,codex")[0], 0)
        self.commit()
        product = {"docs/product/brief.md": "# Brief\n\nOur product.\n", "docs/project-rules.md": "Rule one.\n",
                   "README.md": README + "\nMore.\n", "scripts/build.sh": "echo build\n"}
        for path, content in product.items():
            self.write(path, content)
        verification = json.loads((self.root / ".sdd/verification.json").read_text())
        verification["checks"].append({"id": "unit", "kind": "product", "argv": ["{python}", "-c", "pass"],
                                        "timeout_seconds": 5})
        verification["profiles"]["product"]["focused"].append("unit")
        self.write(".sdd/verification.json", json.dumps(verification))
        self.write("docs/templates/spec.md", "locally edited\n")
        (self.root / "docs/adr/README.md").unlink()
        self.commit("product work")
        kept = {p: (self.root / p).read_bytes() for p in list(product) + [".sdd/verification.json"]}
        code, report = self.install(None)
        self.assertEqual((code, report["mode"], report["clients"]), (0, "upgrade", ["claude", "codex"]))
        for path, content in kept.items():
            with self.subTest(path=path):
                self.assertEqual((self.root / path).read_bytes(), content)
        self.assertEqual((self.root / "docs/templates/spec.md").read_bytes(), (ROOT / "docs/templates/spec.md").read_bytes())
        self.assertTrue((self.root / "docs/adr/README.md").is_file())
        self.assertFalse([path for kind, path in report["actions"] if kind == "orphan"])
        self.assertIn(("record", ".sdd/install.json"), report["actions"])
        record = json.loads((self.root / ".sdd/install.json").read_text())
        self.assertEqual(record["clients"], ["claude", "codex"])
        self.assertIn(".codex/agents/sdd-independent-review.toml", record["files"])

    def test_clean_source_ships_tracked_files_only(self):
        # The untracked listing is mocked (nothing is written into the framework checkout):
        # a clean source must not consult it, or reading the nonexistent stray file would fail.
        real, real_list = install.git, install.git_list

        def clean(root, *args):
            if Path(root) == ROOT and args[:1] == ("status",):
                return b""
            return real(root, *args)

        def listing(root, *args):
            if "--others" in args:
                return ["docs/development/zz-untracked-install-test.md"]
            return real_list(root, *args)

        with mock.patch.object(install, "git", clean), mock.patch.object(install, "git_list", listing), \
                contextlib.redirect_stdout(io.StringIO()):
            code, report = run(self.root, "claude", False)
        self.assertEqual((code, report["source_dirty"]), (0, False))
        self.assertFalse((self.root / "docs/development/zz-untracked-install-test.md").exists())
        self.assertFalse(json.loads((self.root / ".sdd/install.json").read_text())["source_dirty"])

    def test_migrated_1_0_target_reports_unchosen_client_files(self):
        self.write("scripts/sdd/__init__.py", "")
        self.write(".sdd/verification.json", json.dumps({"checks": [{"id": "docs"}]}))
        self.write("README.md", README)
        self.write(".cursor/agents/sdd-independent-review.md", "old\n")
        self.commit("migrated 1.0.0 layout with all clients")
        code, report = self.install("claude")
        self.assertEqual(code, 0)
        self.assertIn(("orphan", ".cursor/agents/sdd-independent-review.md"), report["actions"])

    def test_malformed_target_json_is_a_refusal(self):
        self.write("scripts/sdd/__init__.py", "")
        self.write(".sdd/verification.json", "[1, 2]")
        self.commit("malformed")
        self.assertEqual(self.assert_refused()["status"], "refused")
        self.write(".sdd/install.json", json.dumps({"clients": [1]})); self.commit("bad record")
        self.assertEqual(self.assert_refused(None)["status"], "refused")

    def test_rules_and_ci_policy_ownership(self):
        self.assertEqual(self.install()[0], 0)
        rules = json.loads((self.root / ".sdd/risk-rules.json").read_text())["rules"]
        patterns = [p for rule in rules for p in rule["paths"]]
        self.assertNotIn(".agents/tools/**", patterns)
        self.assertNotIn(".agents/adapters/**", patterns)
        self.assertIn(".sdd/product-risk-rules.json", patterns)
        self.assertEqual((self.root / ".sdd/ci.json").read_bytes(), (ROOT / ".sdd/ci.json").read_bytes())
        self.assertEqual((self.root / ".sdd/product-risk-rules.json").read_bytes(),
                         (ROOT / ".sdd/product-risk-rules.json").read_bytes())
        record = json.loads((self.root / ".sdd/install.json").read_text())
        self.assertIn(".sdd/risk-rules.json", record["files"])
        self.assertNotIn(".sdd/product-risk-rules.json", record["files"])

    def test_upgrade_replaces_framework_policy_and_keeps_product_rules(self):
        self.assertEqual(self.install()[0], 0)
        self.commit()
        own = json.dumps({"version": 1, "rules": [
            {"id": "billing", "minimum_level": "L3", "paths": ["billing/**"], "reason": "Money"}]})
        self.write(".sdd/product-risk-rules.json", own)
        self.write(".sdd/risk-rules.json", json.dumps({"version": 1, "rules": []}))
        self.write(".sdd/ci.json", "{}")
        self.commit("local policy edits")
        code, report = self.install(None)
        self.assertEqual(code, 0)
        self.assertEqual((self.root / ".sdd/product-risk-rules.json").read_text(), own)
        self.assertEqual((self.root / ".sdd/ci.json").read_bytes(), (ROOT / ".sdd/ci.json").read_bytes())
        self.assertIn(("replace", ".sdd/risk-rules.json"), report["actions"])

    def test_upgrade_with_product_rules_in_framework_file_is_refused(self):
        self.assertEqual(self.install()[0], 0)
        (self.root / ".sdd/product-risk-rules.json").unlink()
        rules = json.loads((ROOT / ".sdd/product-risk-rules.json").read_text())["rules"]
        framework = json.loads((self.root / ".sdd/risk-rules.json").read_text())
        framework["rules"] += rules
        self.write(".sdd/risk-rules.json", json.dumps(framework))
        self.commit("pre-split layout")
        reason = self.assert_refused(None)["reason"]
        self.assertIn("public-contract", reason)
        self.assertIn(".sdd/product-risk-rules.json", reason)

    def installed_with_framework_rules(self, mutate=None, product=None):
        self.assertEqual(self.install()[0], 0)
        rules = json.loads((self.root / ".sdd/risk-rules.json").read_text())
        if mutate:
            mutate(rules["rules"])
        self.write(".sdd/risk-rules.json", json.dumps(rules))
        if product is not None:
            self.write(".sdd/product-risk-rules.json", json.dumps({"version": 1, "rules": product}))
        self.commit("edited policy")

    def test_upgrade_refuses_patterns_added_to_framework_rules(self):
        def add(rules):
            next(r for r in rules if r["id"] == "delivery-policy")["paths"].append("Jenkinsfile")
        self.installed_with_framework_rules(add)
        reason = self.assert_refused(None)["reason"]
        self.assertIn("delivery-policy patterns Jenkinsfile", reason)

    def test_upgrade_refuses_custom_rule_left_in_framework_file(self):
        custom = {"id": "billing", "minimum_level": "L3", "paths": ["billing/**"], "reason": "Money"}
        self.installed_with_framework_rules(lambda rules: rules.append(custom), product=[])
        self.assertIn("rule billing", self.assert_refused(None)["reason"])

    def test_upgrade_accepts_custom_rule_already_in_product_file(self):
        custom = {"id": "billing", "minimum_level": "L3", "paths": ["billing/**"], "reason": "Money"}
        self.installed_with_framework_rules(lambda rules: rules.append(custom), product=[custom])
        self.assertEqual(self.install(None)[0], 0)

    def test_upgrade_refuses_product_copy_with_fewer_patterns(self):
        custom = {"id": "billing", "minimum_level": "L3", "paths": ["billing/**", "invoices/**"], "reason": "Money"}
        partial = {**custom, "paths": ["billing/**"]}
        self.installed_with_framework_rules(lambda rules: rules.append(custom), product=[partial])
        self.assertIn("billing patterns invoices/**", self.assert_refused(None)["reason"])

    def test_upgrade_ignores_framework_repository_only_patterns(self):
        def add(rules):
            next(r for r in rules if r["id"] == "ci-governance")["paths"].append(".agents/tools/**")
        self.installed_with_framework_rules(add)
        self.assertEqual(self.install(None)[0], 0)

    def test_upgrade_refuses_shipped_id_reused_by_product(self):
        clash = {"id": "delivery-policy", "minimum_level": "L3", "paths": ["deploy/**"], "reason": "Ours"}
        self.installed_with_framework_rules(product=[clash])
        self.assertIn("delivery-policy", self.assert_refused(None)["reason"])

    def test_upgrade_with_malformed_framework_rules_is_refused(self):
        self.assertEqual(self.install()[0], 0)
        self.write(".sdd/risk-rules.json", "{not json")
        self.commit("broken rules")
        self.assertEqual(self.assert_refused(None)["status"], "refused")

    def test_migrated_1_0_target_with_single_rules_file_is_refused(self):
        self.write("scripts/sdd/__init__.py", "")
        self.write(".sdd/verification.json", json.dumps({"checks": [{"id": "docs"}]}))
        self.write("README.md", README)
        old = json.loads((ROOT / ".sdd/risk-rules.json").read_text())
        old["rules"] += json.loads((ROOT / ".sdd/product-risk-rules.json").read_text())["rules"]
        self.write(".sdd/risk-rules.json", json.dumps(old))
        self.commit("1.0.0 single rules file")
        self.assertIn("rule public-contract", self.assert_refused()["reason"])

    def test_product_ci_settings_are_created_once_and_kept(self):
        self.assertEqual(self.install()[0], 0)
        self.assertEqual(json.loads((self.root / ".sdd/product-ci.json").read_text()), {"version": 1})
        self.commit()
        own = json.dumps({"version": 1, "framework_paths": ["tools/release/**"], "scopes": {"L2": "broad"}})
        self.write(".sdd/product-ci.json", own)
        self.commit("product CI settings")
        self.assertEqual(self.install(None)[0], 0)
        self.assertEqual((self.root / ".sdd/product-ci.json").read_text(), own)

    def test_upgrade_refuses_product_ci_below_shipped_scope(self):
        self.assertEqual(self.install()[0], 0)
        self.write(".sdd/product-ci.json", json.dumps({"version": 1, "scopes": {"L1": "focused"}}))
        self.commit("product CI pinned to an older, lower scope")
        self.assertIn("cannot lower", self.assert_refused(None)["reason"])

    def test_upgrade_preflight_rejects_duplicate_json_keys(self):
        self.assertEqual(self.install()[0], 0)
        self.write(".sdd/product-ci.json", '{"version": 1, "version": 1}')
        self.commit("duplicate key")
        self.assertIn("Duplicate JSON key", self.assert_refused(None)["reason"])

    def test_upgrade_reports_dropped_client_files_as_orphans(self):
        self.assertEqual(self.install("claude,cursor")[0], 0)
        self.commit()
        code, report = self.install("claude")
        self.assertEqual(code, 0)
        self.assertIn(("orphan", ".cursor/agents/sdd-independent-review.md"), report["actions"])
        self.assertTrue((self.root / ".cursor/agents/sdd-independent-review.md").exists())
        self.assertEqual(json.loads((self.root / ".sdd/install.json").read_text())["clients"], ["claude"])

    def test_upgrade_without_record_needs_clients(self):
        self.assertEqual(self.install("claude")[0], 0)
        (self.root / ".sdd/install.json").unlink()
        self.commit()
        self.assertIn("--clients", self.assert_refused(None)["reason"])

    def test_write_failure_reports_what_was_written(self):
        real = install.os.replace
        calls = []

        def failing(src, dst):
            calls.append(dst)
            if len(calls) == 3:
                raise OSError("disk full")
            return real(src, dst)

        with mock.patch.object(install.os, "replace", failing):
            code, report = self.install()
        self.assertEqual((code, report["status"]), (2, "failed"))
        self.assertEqual(len(report["written"]), 2)
        self.assertIn("disk full", report["reason"])

    def test_cli_exit_codes(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(["--target", str(self.root), "--clients", "claude", "--dry-run",
                                   "--allow-dirty-source"]), 0)
        self.assertIn("Install: dry-run", out.getvalue())
