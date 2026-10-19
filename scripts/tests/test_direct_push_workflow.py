"""Contract checks for the optional direct-push workflow, plus its shell with a stubbed gh."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
from support import ROOT

UPSTREAM_ONLY = "github.repository != 'idaik-stuff/lightweight-sdd'"


class DirectPushWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / '.github/workflows/sdd-direct-push.yml').read_text()

    def test_runs_on_push_to_default_branch_only(self):
        self.assertIn('on:\n  push:\n', self.text)
        self.assertNotRegex(self.text, r'(?m)^\s*(pull_request_target|workflow_run|workflow_dispatch):')
        self.assertIn("github.ref == format('refs/heads/{0}', github.event.repository.default_branch)", self.text)

    def test_only_prs_merged_into_default_branch_count(self):
        self.assertIn('select(.merged_at != null and .base.ref == env.DEFAULT_BRANCH)', self.text)
        self.assertIn('DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}', self.text)
        self.assertIn('FORCED: ${{ github.event.forced }}', self.text)

    def test_upstream_template_is_skipped(self):
        conditions = re.findall(r'(?m)^    if: (.*)$', self.text)
        self.assertEqual(len(conditions), 1)
        self.assertIn(UPSTREAM_ONLY, conditions[0])

    def test_readonly_credentials(self):
        self.assertIn('permissions:\n  contents: read\n  pull-requests: read\n', self.text)
        self.assertNotIn('secrets.', self.text)
        self.assertNotIn(': write', self.text)

    def test_no_unpinned_actions_or_error_suppression(self):
        for action in re.findall(r'uses: ([^\s#]+)', self.text):
            self.assertRegex(action, r'^actions/[a-z-]+@[0-9a-f]{40}$')
        self.assertNotIn('continue-on-error', self.text)
        self.assertNotIn('|| true', self.text)

    @unittest.skipIf(os.name == 'nt', 'The shipped workflow runs on Ubuntu; Windows bash launchers are not equivalent')
    @unittest.skipUnless(shutil.which('bash'), 'The shipped workflow runs on Linux with bash')
    def test_actual_shell_with_stubbed_github_api(self):
        block = self.text.split('        run: |\n')[1]
        script = '\n'.join(line[10:] for line in block.splitlines())
        with tempfile.TemporaryDirectory(prefix='sdd-gh-') as folder:
            stub = Path(folder) / 'gh'
            # Commits named "merged*" have a merged PR; "fail*" makes the API call fail.
            stub.write_text('#!/bin/bash\ncase "$2" in\n  */fail*) exit 1 ;;\n'
                            '  */merged*) echo 1 ;;\n  *) echo 0 ;;\nesac\n')
            stub.chmod(0o755)
            cases = [('0' * 40, 'false', 'direct', 0, 'Branch creation'),
                     ('a' * 40, 'false', 'merged1 merged2', 0, 'Every pushed commit'),
                     ('a' * 40, 'false', 'merged1 direct1', 1, 'direct1'),
                     ('a' * 40, 'false', 'fail1', 1, ''),
                     ('a' * 40, 'true', 'merged1', 1, 'Force push'),
                     ('a' * 40, 'false', '', 1, '0 commits'),
                     ('a' * 40, 'false', ' '.join(f'merged{i}' for i in range(2048)), 1, '2048 commits')]
            for before, forced, commits, expected, text in cases:
                with self.subTest(forced=forced, commits=commits[:40]):
                    env = dict(os.environ, PATH=folder + os.pathsep + os.environ['PATH'], REPO='owner/repo',
                               DEFAULT_BRANCH='main', BEFORE=before, FORCED=forced, COMMITS=commits)
                    result = subprocess.run(['bash', '--noprofile', '--norc', '-e', '-o', 'pipefail', '-c', script],
                                            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                    self.assertIn(text, result.stdout)
                    if commits == 'merged1 direct1':
                        self.assertNotIn('merged1', result.stdout)
