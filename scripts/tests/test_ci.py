import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from support import Fixture, ROOT, command, manifest
from sdd.common import ConfigError
from sdd.ci import START, END, assess_ci, ci_configuration, clean_checkout, event_context, final_gate, metadata
from sdd.ci_setup import PROTECTED, check_setup, owners
from sdd.verify import run


def body(level='L1', change='none'):
    return f'{START}\nChange-Level: {level}\nChange-ID: {change}\n{END}'


class MetadataTests(unittest.TestCase):
    def test_valid_declaration(self):
        self.assertEqual(metadata(body()), {'level': 'L1', 'change': 'none'})

    def test_valid_change(self):
        self.assertEqual(metadata(body('L3', 'CHG-003')), {'level':'L3', 'change':'CHG-003'})

    def test_missing_block(self):
        with self.assertRaises(ConfigError): metadata('Change-Level: L0')

    def test_null_body(self):
        with self.assertRaises(ConfigError): metadata(None)

    def test_duplicate_blocks(self):
        with self.assertRaises(ConfigError): metadata(body()+body())

    def test_duplicate_field(self):
        with self.assertRaises(ConfigError): metadata(body().replace(END,'Change-Level: L0\n'+END))

    def test_unknown_field(self):
        with self.assertRaises(ConfigError): metadata(body().replace(END,'Target: framework\n'+END))

    def test_shell_injection(self):
        with self.assertRaises(ConfigError): metadata(body(change='$(touch stolen)'))

    def test_unsafe_id(self):
        with self.assertRaises(ConfigError): metadata(body(change='..'))

    def test_invalid_level(self):
        with self.assertRaises(ConfigError): metadata(body('L4'))

    def test_reversed_delimiters(self):
        with self.assertRaises(ConfigError): metadata(END+START)

    def test_gate_only_explicit_success(self):
        self.assertTrue(final_gate(['success','success']))
        for value in ('failure','skipped','cancelled','neutral','timed_out','',None):
            with self.subTest(value=value): self.assertFalse(final_gate(['success',value]))
        self.assertFalse(final_gate([]))


class PolicyTests(Fixture):
    def setUp(self):
        super().setUp()
        self.write('.sdd/ci.json', (ROOT/'.sdd/ci.json').read_text())
        self.base = None
        self.external = tempfile.TemporaryDirectory(prefix='sdd-trusted-')
        self.addCleanup(self.external.cleanup)
        self.trusted = Path(self.external.name)/'checkout'

    def start(self):
        self.base = self.init_git()
        self.git('checkout','-qb','candidate')

    def finish(self, level='L1', change='none'):
        self.git('add','.')
        self.git('commit','-qm','Synthetic candidate')
        head = self.git('rev-parse','HEAD')
        self.git('checkout','--detach',self.base)
        self.git('merge','--no-ff','-m','Synthetic test merge',head)
        merge = self.git('rev-parse','HEAD')
        subprocess.run(['git','clone','-q','--no-hardlinks',str(self.root),str(self.trusted)],check=True,stderr=subprocess.PIPE)
        subprocess.run(['git','-C',str(self.trusted),'checkout','-q','--detach',self.base],check=True)
        event={'action':'synchronize','repository':{'full_name':'fixture/repo'},'pull_request':{
            'state':'open','base':{'sha':self.base,'repo':{'full_name':'fixture/repo'}},
            'head':{'sha':head},'body':body(level,change)}}
        return event, merge

    def assess(self, level='L1', change='none'):
        event, merge = self.finish(level,change)
        return assess_ci(self.trusted,self.root,event,merge)

    def test_doc_typo_focused(self):
        self.start(); self.write('README.md','# Changed\n')
        r=self.assess('L0'); self.assertEqual((r['status'],r['scope'],r['target'],r['design_only']),('passed','focused','framework',True))

    def test_unrecognized_path_needs_product(self):
        self.start(); self.write('src/main.py','pass\n')
        r=self.assess(); self.assertEqual(r['target'],'product'); self.assertEqual(r['status'],'failed')

    def test_registered_product_checks_allow_bug(self):
        self.config(manifest([command(),command('product','product')]))
        self.start(); self.write('src/main.py','pass\n')
        r=self.assess(); self.assertEqual(r['status'],'passed'); self.assertIn('product',r['check_ids'])

    def test_candidate_cannot_self_register_product_checks(self):
        self.start(); self.config(manifest([command(),command('product','product')]))
        self.write('src/main.py','pass\n')
        r=self.assess(); self.assertEqual(r['status'],'failed'); self.assertNotIn('product',r['check_ids'])

    def test_candidate_cannot_remove_base_risk(self):
        self.start(); self.rules({'version':1,'rules':[]}); self.write('api/new.txt','contract')
        r=self.assess(); self.assertEqual(r['detected_floor'],'L3'); self.assertEqual(r['status'],'failed')

    def test_candidate_cannot_widen_framework_allowlist(self):
        self.start(); config=json.loads((self.root/'.sdd/ci.json').read_text()); config['framework_paths']=['**']; self.write('.sdd/ci.json',json.dumps(config))
        self.write('business/new.py','pass\n'); r=self.assess(); self.assertEqual(r['target'],'product')

    def test_candidate_removed_check_still_selected(self):
        self.start(); self.config(manifest([])); self.write('README.md','# New\n')
        r=self.assess(); self.assertIn('ok',r['check_ids'])

    def test_draft_spec_only_can_merge_as_design(self):
        self.start(); ident=self.change(); (self.root/f'docs/specs/{ident}/plan.md').unlink()
        self.replace(f'docs/specs/{ident}/spec.md', 'Related plan: [plan](plan.md).', 'Related plan: pending, not yet created.')
        r=self.assess('L2',ident); self.assertTrue(r['design_only']); self.assertEqual(r['status'],'passed',r['errors'])

    def test_draft_spec_blocks_implementation(self):
        self.start(); ident=self.change(); self.write('scripts/tests/new.py','pass\n')
        r=self.assess('L2',ident); self.assertEqual(r['status'],'failed'); self.assertIn('draft', ' '.join(r['errors']))

    def test_approved_spec_and_plan_allow_implementation(self):
        self.start(); ident=self.change(spec_state='approved',plan_state='approved'); self.write('scripts/tests/new.py','pass\n')
        r=self.assess('L2',ident); self.assertEqual(r['status'],'passed',r['errors'])

    def test_implementation_without_change_id_blocked(self):
        self.start(); self.write('scripts/tests/new.py','pass\n')
        r=self.assess('L2'); self.assertEqual(r['status'],'failed')

    def test_broken_docs_block(self):
        self.start(); self.write('README.md','[broken](missing.md)\n')
        r=self.assess('L0'); self.assertEqual(r['status'],'failed')

    def test_declared_level_not_lowered(self):
        self.start(); self.write('README.md','# Design\n')
        r=self.assess('L3'); self.assertEqual(r['scope'],'broad')

    def test_deleted_risky_path_counted(self):
        self.write('api/old.txt','old'); self.start(); (self.root/'api/old.txt').unlink()
        r=self.assess(); self.assertEqual(r['detected_floor'],'L3'); self.assertIn('api/old.txt',r['paths'])

    def test_renamed_risky_path_retains_both_names(self):
        self.write('api/old.txt','old'); self.start(); self.git('mv','api/old.txt','new.txt')
        r=self.assess(); self.assertEqual(r['detected_floor'],'L3'); self.assertIn('new.txt',r['paths']); self.assertIn('api/old.txt',r['paths'])

    def test_symlink_rejected_before_reading(self):
        self.start(); (self.root/'README.md').unlink(); (self.root/'README.md').symlink_to('/etc/passwd')
        event,merge=self.finish('L0')
        with self.assertRaisesRegex(ConfigError,'symlinks'): assess_ci(self.trusted,self.root,event,merge)

    def test_dirty_candidate_blocked(self):
        self.start(); self.write('README.md','# Changed\n'); event,merge=self.finish('L0'); self.write('dirty.txt','x')
        with self.assertRaisesRegex(ConfigError,'clean'): assess_ci(self.trusted,self.root,event,merge)

    def test_wrong_merge_sha_blocked(self):
        self.start(); self.write('README.md','# Changed\n'); event,merge=self.finish('L0')
        with self.assertRaisesRegex(ConfigError,'HEAD'): assess_ci(self.trusted,self.root,event,event['pull_request']['head']['sha'])

    def test_wrong_event_parent_blocked(self):
        self.start(); self.write('README.md','# Changed\n'); event,merge=self.finish('L0'); event['pull_request']['head']['sha']='a'*40
        with self.assertRaisesRegex(ConfigError,'parents'): assess_ci(self.trusted,self.root,event,merge)

    def test_same_trust_and_candidate_rejected(self):
        with self.assertRaisesRegex(ConfigError,'separate'): assess_ci(self.root,self.root,{},'a'*40)

    def test_nested_trust_rejected(self):
        with self.assertRaisesRegex(ConfigError,'separate'): assess_ci(self.root,self.root/'nested',{},'a'*40)

    def test_missing_trusted_ci_policy_errors(self):
        (self.root/'.sdd/ci.json').unlink()
        with self.assertRaises(ConfigError): ci_configuration(self.root)

    def test_l3_scope_cannot_be_lowered(self):
        data=json.loads((self.root/'.sdd/ci.json').read_text()); data['scopes']['L3']='focused'; self.write('.sdd/ci.json',json.dumps(data))
        with self.assertRaises(ConfigError): ci_configuration(self.root)

    def test_bad_scope_type_is_error(self):
        data=json.loads((self.root/'.sdd/ci.json').read_text()); data['scopes']['L3']=[]; self.write('.sdd/ci.json',json.dumps(data))
        with self.assertRaises(ConfigError): ci_configuration(self.root)

    def test_merge_queue_event_unsupported(self):
        with self.assertRaises(ConfigError): event_context({'merge_group':{}},'a'*40)

    def test_closed_event_rejected(self):
        self.start(); self.write('README.md','# Changed\n'); event,merge=self.finish('L0'); event['pull_request']['state']='closed'
        with self.assertRaises(ConfigError): assess_ci(self.trusted,self.root,event,merge)

    def test_base_has_to_match_trusted_checkout(self):
        self.start(); self.write('README.md','# Changed\n'); event,merge=self.finish('L0'); event['pull_request']['base']['sha']='b'*40
        with self.assertRaisesRegex(ConfigError,'HEAD'): assess_ci(self.trusted,self.root,event,merge)

    def test_runner_uses_base_registration_not_candidate(self):
        self.config(manifest([command('must-fail',code='raise SystemExit(7)')]))
        self.start(); self.config(manifest([command('fake-pass')])); event,merge=self.finish()
        report=run(self.root,'focused','framework',policy_root=self.trusted)
        self.assertEqual(report['status'],'failed'); self.assertEqual(report['checks'][0]['id'],'must-fail')

    def test_runner_uses_base_risk_floor(self):
        self.start(); self.rules({'version':1,'rules':[]}); self.write('api/new.txt','x'); event,merge=self.finish()
        report=run(self.root,'focused','framework',base=self.base,level='L1',policy_root=self.trusted)
        self.assertEqual(report['status'],'failed'); self.assertEqual(report['change_gate']['detected_floor'],'L3')


class SetupTests(Fixture):
    def setUp(self):
        super().setUp(); self.write('.sdd/ci.json',(ROOT/'.sdd/ci.json').read_text())

    def valid(self):
        return '\n'.join(pattern+' @fixture-owner' for pattern in PROTECTED)+'\n'

    def test_missing_owners_is_blocked(self):
        self.assertEqual(check_setup(self.root)['status'],'blocked')

    def test_placeholder_owners_rejected(self):
        self.assertTrue(owners(self.valid().replace('@fixture-owner','@REPLACE-WITH-OWNER')))

    def test_complete_local_file_not_remote_certification(self):
        self.write('.github/CODEOWNERS',self.valid()); r=check_setup(self.root)
        self.assertEqual(r['status'],'local-files-ready'); self.assertEqual(r['remote_enforcement'],'not-checked')

    def test_later_override_rejected(self):
        self.assertTrue(owners(self.valid()+'* @someone-else\n'))

    def test_empty_owner_rejected(self):
        self.assertTrue(owners(self.valid().replace('/scripts/ @fixture-owner','/scripts/')))

    def test_product_ownership_above_block_allowed(self):
        self.assertFalse(owners('/src/ @fixture-org/product\n'+self.valid()))

    def test_ruleset_is_deliberately_disabled(self):
        data=json.loads((ROOT/'.github/sdd-ruleset.template.json').read_text())
        self.assertEqual(data['enforcement'],'disabled'); self.assertEqual(data['bypass_actors'],[])
        rules={item['type']:item.get('parameters',{}) for item in data['rules']}
        self.assertEqual(rules['required_status_checks']['required_status_checks'],[{'context':'sdd-gate'}])
        self.assertTrue(rules['pull_request']['require_code_owner_review'])
        self.assertTrue(rules['pull_request']['dismiss_stale_reviews_on_push'])
