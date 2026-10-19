"""Run the shipped pre-push hook through real Git pushes to a local bare remote."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from support import Fixture, ROOT

HOOKS = ROOT / "scripts/hooks"


class PrePushHookTests(Fixture):
    def setUp(self):
        super().setUp()
        remote = tempfile.TemporaryDirectory(prefix="sdd-remote-")
        self.addCleanup(remote.cleanup)
        self.remote = Path(remote.name)
        subprocess.run(["git", "init", "-q", "--bare", str(self.remote)], check=True)
        self.init_git()
        self.git("config", "core.hooksPath", HOOKS.as_posix())
        self.git("remote", "add", "origin", self.remote.as_posix())

    def push(self, *refs, remote="origin", verify=True):
        options = [] if verify else ["--no-verify"]
        result = subprocess.run(["git", "-C", str(self.root), "push", "-q", *options, remote, *refs],
                                env=self.git_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode, result.stderr

    def remote_has(self, branch):
        result = subprocess.run(["git", "-C", str(self.remote), "rev-parse", "-q", "--verify", f"refs/heads/{branch}"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0

    def test_push_to_default_branch_refused(self):
        code, error = self.push(f"HEAD:refs/heads/{self.default_branch}")
        self.assertNotEqual(code, 0)
        self.assertIn(f"default branch '{self.default_branch}'", error)
        self.assertFalse(self.remote_has(self.default_branch))

    def test_push_of_change_branch_accepted(self):
        code, error = self.push("chg-fixture")
        self.assertEqual(code, 0, error)
        self.assertTrue(self.remote_has("chg-fixture"))

    def test_remote_head_declares_default_branch(self):
        self.git("config", "--unset", "sdd.defaultBranch")
        self.git("update-ref", "refs/remotes/origin/trunk", "HEAD")
        self.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")
        code, error = self.push("HEAD:refs/heads/trunk")
        self.assertNotEqual(code, 0)
        self.assertIn("default branch 'trunk'", error)
        code, error = self.push("chg-fixture")
        self.assertEqual(code, 0, error)

    def test_deleting_default_branch_refused(self):
        code, error = self.push(f"{self.default_branch}:{self.default_branch}", verify=False)
        self.assertEqual(code, 0, error)
        code, error = self.push("--delete", self.default_branch)
        self.assertNotEqual(code, 0)
        self.assertIn("refusing to update the default branch", error)
        self.assertTrue(self.remote_has(self.default_branch))

    def test_mixed_push_with_default_branch_refused_entirely(self):
        code, error = self.push("chg-fixture", f"HEAD:refs/heads/{self.default_branch}")
        self.assertNotEqual(code, 0)
        self.assertIn("refusing to update the default branch", error)
        self.assertFalse(self.remote_has("chg-fixture"))
        self.assertFalse(self.remote_has(self.default_branch))

    def test_push_to_url_uses_declaration(self):
        url = self.remote.as_posix()
        code, error = self.push(f"HEAD:refs/heads/{self.default_branch}", remote=url)
        self.assertNotEqual(code, 0)
        self.assertIn("refusing to update the default branch", error)
        self.git("config", "--unset", "sdd.defaultBranch")
        code, error = self.push("chg-fixture", remote=url)
        self.assertNotEqual(code, 0)
        self.assertIn("for a push to a URL", error)
        self.assertNotIn("set-head", error)

    def test_declaration_errors_refused(self):
        self.git("config", "sdd.defaultBranch", "mian")
        code, error = self.push("chg-fixture")
        self.assertNotEqual(code, 0)
        self.assertIn("'mian' names no local or origin branch", error)
        self.git("config", "sdd.defaultBranch", self.default_branch)
        self.git("update-ref", "refs/remotes/origin/trunk", "HEAD")
        self.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")
        code, error = self.push("chg-fixture")
        self.assertNotEqual(code, 0)
        self.assertIn("disagrees with origin/HEAD 'trunk'", error)
        self.assertFalse(self.remote_has("chg-fixture"))

    def test_secondary_remote_head_does_not_contradict_declaration(self):
        # Like scripts/sdd/changes.py, the declaration is only compared with origin/HEAD.
        mirror = tempfile.TemporaryDirectory(prefix="sdd-mirror-")
        self.addCleanup(mirror.cleanup)
        subprocess.run(["git", "init", "-q", "--bare", mirror.name], check=True)
        self.git("remote", "add", "mirror", Path(mirror.name).as_posix())
        self.git("update-ref", "refs/remotes/mirror/trunk", "HEAD")
        self.git("symbolic-ref", "refs/remotes/mirror/HEAD", "refs/remotes/mirror/trunk")
        code, error = self.push("chg-fixture", remote="mirror")
        self.assertEqual(code, 0, error)
        code, error = self.push(f"HEAD:refs/heads/{self.default_branch}", remote="mirror")
        self.assertNotEqual(code, 0)
        self.assertIn("refusing to update the default branch", error)

    @unittest.skipIf(os.name == "nt", "Runs the hook directly with a POSIX git stub")
    @unittest.skipUnless(shutil.which("sh"), "Needs a POSIX shell")
    def test_unreadable_declaration_refused(self):
        stubs = tempfile.TemporaryDirectory(prefix="sdd-git-stub-")
        self.addCleanup(stubs.cleanup)
        stub = Path(stubs.name) / "git"
        stub.write_text('#!/bin/sh\nif [ "$1 $2 $3 $4" = "config --local --get sdd.defaultBranch" ]; then\n'
                        '    echo "fatal: bad config line 1" >&2; exit 128\nfi\n'
                        f'exec "{shutil.which("git")}" "$@"\n')
        stub.chmod(0o755)
        env = dict(self.git_env(), PATH=stubs.name + os.pathsep + os.environ["PATH"])
        result = subprocess.run(["sh", str(HOOKS / "pre-push"), "origin", self.remote.as_posix()], cwd=self.root,
                                env=env, input="", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("cannot read sdd.defaultBranch (git config exited 128)", result.stderr)

    def test_shipped_hook_is_executable_in_git(self):
        # Git on Linux and macOS silently ignores a hook without the executable bit.
        entry = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-s", "scripts/hooks/pre-push"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if entry.returncode or not entry.stdout:
            self.skipTest("Not a Git checkout with the hook in its index")
        self.assertTrue(entry.stdout.startswith("100755 "), entry.stdout)

    def test_undeterminable_default_branch_refused(self):
        self.git("config", "--unset", "sdd.defaultBranch")
        code, error = self.push("chg-fixture")
        self.assertNotEqual(code, 0)
        self.assertIn("cannot determine the default branch", error)
        self.assertFalse(self.remote_has("chg-fixture"))
