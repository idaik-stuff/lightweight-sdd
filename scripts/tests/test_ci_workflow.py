"""Contract checks for the shipped adapter, not a replacement for actionlint."""
import itertools
import os
from pathlib import Path
import re
import shutil
import subprocess
import unittest
from support import ROOT


# The only allowed job condition: skip the upstream template repository itself.
UPSTREAM_ONLY = "github.repository != 'idaik-stuff/lightweight-sdd'"


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / '.github/workflows/sdd.yml').read_text()

    def test_every_action_is_commit_pinned(self):
        uses = re.findall(r'uses: ([^\s#]+)', self.text)
        self.assertTrue(uses)
        for action in uses:
            self.assertRegex(action, r'^actions/[a-z-]+@[0-9a-f]{40}$')

    def test_no_privileged_event(self):
        self.assertIn('  pull_request:\n', self.text)
        self.assertNotRegex(self.text, r'(?m)^\s*(pull_request_target|workflow_run|workflow_dispatch):')

    def test_no_path_or_branch_filters(self):
        self.assertNotRegex(self.text,r'(?m)^\s*(paths|paths-ignore|branches|branches-ignore):')

    def test_readonly_credentials(self):
        self.assertIn('permissions:\n  contents: read', self.text)
        self.assertNotIn('secrets.', self.text)
        self.assertNotIn(': write', self.text)
        self.assertEqual(self.text.count('persist-credentials: false'),4)

    def test_no_error_suppression(self):
        self.assertNotIn('continue-on-error', self.text)
        self.assertNotIn('|| true', self.text)

    def test_final_gate_is_unconditional(self):
        gate=self.text.split('  gate:\n')[1]
        self.assertIn('needs: [policy, verify]',gate)
        self.assertIn('if: ${{ always() && ' + UPSTREAM_ONLY + ' }}',gate)
        self.assertIn('permissions: {}',gate)

    def test_only_the_upstream_template_is_skipped(self):
        conditions=re.findall(r'(?m)^    if: (.*)$',self.text)
        self.assertEqual(conditions,['${{ ' + UPSTREAM_ONLY + ' }}',
                                     '${{ always() && ' + UPSTREAM_ONLY + ' }}'])
        policy=self.text.split('  policy:\n')[1].split('\n  verify:\n')[0]
        self.assertIn('if: ${{ ' + UPSTREAM_ONLY + ' }}',policy)
        self.assertIn('needs: policy',self.text.split('  verify:\n')[1])

    def test_runner_and_registry_are_from_trusted_checkout(self):
        self.assertIn('python -I sdd-trusted/scripts/verify', self.text)
        self.assertIn('--policy-root sdd-trusted', self.text)
        self.assertNotIn('python sdd-candidate/scripts/verify', self.text)

    def test_ownership_prerequisites_checked(self):
        self.assertIn('scripts/check-ci-setup --root sdd-trusted',self.text)
        self.assertIn('scripts/check-ci-setup --root sdd-candidate',self.text)

    def test_hidden_reports_explicit_and_bounded(self):
        self.assertIn('path: sdd-candidate/.sdd/results/verify-*.json',self.text)
        self.assertIn('include-hidden-files: true',self.text)
        self.assertEqual(self.text.count('retention-days: 14'),2)
        self.assertEqual(self.text.count('if-no-files-found: error'),2)

    @unittest.skipIf(os.name == 'nt', 'The shipped CI adapter runs on Ubuntu; Windows bash launchers are not equivalent')
    @unittest.skipUnless(shutil.which('bash'), 'The shipped CI adapter runs on Linux with bash')
    def test_actual_gate_shell_rejects_non_success_combinations(self):
        gate=self.text.split('  gate:\n')[1]
        block=gate.split('        run: |\n')[1]
        script='\n'.join(line[10:] for line in block.splitlines())
        for first,second in itertools.product(('success','failure','skipped','cancelled','neutral'), repeat=2):
            with self.subTest(first=first,second=second):
                result=subprocess.run(['bash','--noprofile','--norc','-e','-o','pipefail','-c',script],
                    env=dict(os.environ,POLICY_RESULT=first,VERIFY_RESULT=second),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                self.assertEqual(result.returncode==0,first==second=='success')
