"""Static integration contracts. These tests do not execute or certify any agent client."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from sync_adapters import (AdapterError, CLIENTS, COMMENT_MARKER, MARKER, PHASES,
                           inventory, read_interface, render_expected, synchronize)
try:
    import tomllib
except ImportError:  # Python 3.10 remains supported by the automation.
    tomllib = None

RELEASE = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).with_name('sync_adapters.py')


class MultiAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'AGENTS.md').write_text('# Fixture\n')
        for relative in ('.agents/workflows', '.agents/adapters', '.agents/review'):
            shutil.copytree(RELEASE / relative, self.root / relative)

    def write(self, path, text):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')
        return p

    def modify_manifest(self, fn):
        path = self.root / '.agents/adapters/clients.json'
        data = json.loads(path.read_text()); fn(data)
        path.write_text(json.dumps(data))

    def test_all_twenty_files_have_expected_locations(self):
        files = render_expected(self.root)
        self.assertEqual(len(files), 20)
        self.assertEqual(sum(p.endswith('/SKILL.md') for p in files), 10)
        self.assertEqual(sum(p.endswith('/openai.yaml') for p in files), 5)
        self.assertIn('.codex/agents/sdd-independent-review.toml', files)
        self.assertIn('.cursor/agents/sdd-independent-review.md', files)
        self.assertIn('.github/agents/sdd-independent-review.agent.md', files)
        self.assertIn('.github/copilot-instructions.md', files)

    def test_shared_names_are_namespaced_not_generic(self):
        for phase in PHASES:
            text = render_expected(self.root)[f'.agents/skills/sdd-{phase}/SKILL.md']
            self.assertIn(f'\nname: sdd-{phase}\n', text)
            self.assertNotIn(f'\nname: {phase}\n', text)

    def test_all_runtime_implementation_aliases_disable_auto_invocation(self):
        for prefix in ('.agents/skills', '.claude/skills'):
            for phase in PHASES:
                text = render_expected(self.root)[f'{prefix}/sdd-{phase}/SKILL.md']
                self.assertEqual('disable-model-invocation: true' in text, phase == 'implement')

    def test_codex_sidecar_disables_only_implementation(self):
        for phase in PHASES:
            text = render_expected(self.root)[f'.agents/skills/sdd-{phase}/agents/openai.yaml']
            self.assertIn('allow_implicit_invocation: '+('false' if phase == 'implement' else 'true'), text)
            self.assertIn(COMMENT_MARKER, text)

    def test_shared_entrypoints_have_no_claude_argument_expansion(self):
        for phase in PHASES:
            text = render_expected(self.root)[f'.agents/skills/sdd-{phase}/SKILL.md']
            self.assertNotIn('$ARGUMENTS', text)
            self.assertNotIn('!`', text)
            self.assertNotIn('allowed-tools:', text)

    def test_claude_argument_expansion_is_preserved(self):
        text = render_expected(self.root)['.claude/skills/sdd-spec/SKILL.md']
        self.assertIn('Request input: $ARGUMENTS', text)
        self.assertIn('argument-hint:', text)

    def test_sources_are_referenced_not_embedded(self):
        for phase in PHASES:
            for prefix in ('.agents/skills', '.claude/skills'):
                text = render_expected(self.root)[f'{prefix}/sdd-{phase}/SKILL.md']
                self.assertIn(f'workflows/{phase}/SKILL.md', text)
                self.assertNotIn('## Procedure', text)

    def test_no_cursor_or_copilot_skill_copies_generated(self):
        files = render_expected(self.root)
        self.assertFalse(any(p.startswith(('.cursor/skills/', '.github/skills/')) for p in files))

    def test_canonical_sources_remain_byte_identical_after_generation(self):
        before = {p: p.read_bytes() for p in (self.root/'.agents/workflows').rglob('*') if p.is_file()}
        synchronize(self.root)
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_cursor_reviewer_native_readonly_and_foreground(self):
        text = render_expected(self.root)['.cursor/agents/sdd-independent-review.md']
        self.assertIn('readonly: true\n', text)
        self.assertIn('is_background: false\n', text)
        self.assertNotIn('tools:', text)  # Do not invent a Cursor tool allowlist field.
        self.assertIn('confirmation', text)
        self.assertIn('return blocked', text)

    def test_claude_reviewer_stays_no_shell(self):
        text = render_expected(self.root)['.claude/agents/sdd-independent-review.md']
        self.assertIn('tools: Read, Grep, Glob\n', text)
        self.assertIn('native .cursor/agents/', text)

    def test_copilot_reviewer_targets_vscode_and_only_read_search(self):
        text = render_expected(self.root)['.github/agents/sdd-independent-review.agent.md']
        self.assertIn('target: vscode\n', text)
        self.assertIn('tools: ["read", "search"]\n', text)
        self.assertNotIn('handoffs:', text)
        self.assertNotIn('mcp-servers:', text)

    @unittest.skipUnless(tomllib is not None, 'TOML parser is built in on Python 3.11+')
    def test_codex_native_toml_is_valid_and_read_only(self):
        text = render_expected(self.root)['.codex/agents/sdd-independent-review.toml']
        data = tomllib.loads(text)
        self.assertEqual(set(data), {'name', 'description', 'sandbox_mode', 'developer_instructions'})
        self.assertEqual(data['sandbox_mode'], 'read-only')
        self.assertIn('.agents/review/independent-review.md', data['developer_instructions'])
        self.assertIn('return blocked', data['developer_instructions'])

    def test_no_global_configuration_or_permissions_generated(self):
        files = render_expected(self.root)
        self.assertNotIn('.codex/config.toml', files)
        self.assertNotIn('.cursor/settings.json', files)
        self.assertNotIn('.claude/settings.json', files)
        self.assertNotIn('.vscode/settings.json', files)

    def test_copilot_bridge_points_at_root_policy(self):
        text = render_expected(self.root)['.github/copilot-instructions.md']
        self.assertIn('[AGENTS.md](../AGENTS.md)', text)
        self.assertNotIn('| L3 |', text)
        self.assertLess(len(text.splitlines()), 15)

    def test_reserved_cursor_skill_collision_is_rejected(self):
        self.write('.cursor/skills/sdd-spec/SKILL.md', '# User-owned\n')
        with self.assertRaisesRegex(AdapterError, 'collision'):
            synchronize(self.root)

    def test_reserved_name_in_unrelated_folder_is_rejected(self):
        self.write('.github/skills/other/SKILL.md', '---\nname: "sdd-implement"\n---\nOther\n')
        with self.assertRaisesRegex(AdapterError, 'collision'):
            synchronize(self.root)

    def test_old_command_collision_is_rejected(self):
        self.write('.claude/commands/sdd-implement.md', '# Old command\n')
        with self.assertRaisesRegex(AdapterError, 'collision'):
            synchronize(self.root)

    def test_prompt_alias_collision_is_rejected(self):
        self.write('.github/prompts/sdd-implement.prompt.md', '# Another tool set\n')
        with self.assertRaisesRegex(AdapterError, 'collision'):
            synchronize(self.root)

    def test_unrelated_skill_and_settings_are_preserved(self):
        skill = self.write('.cursor/skills/team-helper/SKILL.md', '---\nname: team-helper\n---\nHelp\n')
        config = self.write('.codex/config.toml', 'model = "user-selected"\n')
        synchronize(self.root)
        self.assertIn('team-helper', skill.read_text())
        self.assertEqual(config.read_text(), 'model = "user-selected"\n')

    def test_unowned_copilot_bridge_blocks_every_write(self):
        p = self.write('.github/copilot-instructions.md', 'Company policy\n')
        with self.assertRaisesRegex(AdapterError, 'unowned'):
            synchronize(self.root)
        self.assertEqual(p.read_text(), 'Company policy\n')
        self.assertFalse((self.root/'.agents/skills').exists())

    def test_orphan_marked_adapter_is_not_silently_deleted(self):
        p = self.write('.agents/skills/old-generated/SKILL.md', MARKER+'\nOld\n')
        with self.assertRaisesRegex(AdapterError, 'Orphan'):
            synchronize(self.root)
        self.assertTrue(p.exists())

    def test_missing_codex_metadata_is_drift(self):
        synchronize(self.root)
        p = self.root/'.agents/skills/sdd-implement/agents/openai.yaml'
        p.unlink()
        self.assertIn(p.relative_to(self.root).as_posix(), synchronize(self.root, check=True))
        self.assertFalse(p.exists())

    def test_weakened_codex_gate_is_drift(self):
        synchronize(self.root)
        p = self.root/'.agents/skills/sdd-implement/agents/openai.yaml'
        p.write_text(p.read_text().replace('false', 'true'))
        self.assertIn(p.relative_to(self.root).as_posix(), synchronize(self.root, check=True))
        synchronize(self.root)
        self.assertIn('false', p.read_text())

    def test_weakened_cursor_reviewer_is_drift(self):
        synchronize(self.root)
        p = self.root/'.cursor/agents/sdd-independent-review.md'
        p.write_text(p.read_text().replace('readonly: true', 'readonly: false'))
        self.assertIn(p.relative_to(self.root).as_posix(), synchronize(self.root, check=True))

    def test_symlink_source_is_rejected(self):
        p = self.root/'.agents/workflows/spec/SKILL.md'
        p.unlink()
        p.symlink_to(self.root/'AGENTS.md')
        with self.assertRaisesRegex(AdapterError, 'symlinked'):
            synchronize(self.root)

    def test_symlink_discovery_root_is_rejected(self):
        outside = self.root/'outside'; outside.mkdir()
        (self.root/'.cursor').mkdir()
        (self.root/'.cursor/skills').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(AdapterError, 'symlinked'):
            synchronize(self.root)

    def test_unknown_client_is_rejected(self):
        self.modify_manifest(lambda d: d['clients'].append('unverified-client'))
        with self.assertRaises(AdapterError):
            synchronize(self.root)

    def test_duplicate_json_keys_are_rejected(self):
        p = self.root/'.agents/adapters/clients.json'
        p.write_text(p.read_text().replace('"schema_version": 2', '"schema_version": 2, "schema_version": 2'))
        with self.assertRaisesRegex(AdapterError, 'Duplicate'):
            synchronize(self.root)

    def test_boolean_schema_version_is_rejected(self):
        self.modify_manifest(lambda d: d.update(schema_version=True))
        with self.assertRaises(AdapterError):
            synchronize(self.root)

    def test_unreviewed_command_rename_is_rejected(self):
        self.modify_manifest(lambda d: d['skills'][0].update(command='sdd-something'))
        with self.assertRaises(AdapterError):
            synchronize(self.root)

    def test_extra_canonical_runtime_field_is_rejected(self):
        p = self.root/'.agents/workflows/implement/SKILL.md'
        p.write_text(p.read_text().replace('name: implement\n', 'name: implement\ndisable-model-invocation: true\n'))
        with self.assertRaisesRegex(AdapterError, 'exactly name'):
            synchronize(self.root)

    def test_invalid_ui_metadata_is_rejected(self):
        p = self.root/'.agents/workflows/spec/agents/openai.yaml'
        p.write_text('interface:\n  display_name: unquoted\n  short_description: "Description"\n')
        with self.assertRaisesRegex(AdapterError, 'JSON-quoted'):
            read_interface(p)

    def test_inventory_does_not_claim_runtime_test_or_write(self):
        report = inventory(self.root)
        self.assertEqual(report['clients'], CLIENTS)
        self.assertEqual(report['runtime_validation'], 'not-checked')
        self.assertEqual(report['status'], 'drift')
        self.assertEqual(len(report['files']), 20)
        self.assertFalse((self.root/'.agents/skills').exists())

    def test_inventory_cli_exit_codes_and_read_only_behavior(self):
        cmd = [sys.executable, str(SCRIPT), '--root', str(self.root), '--inventory']
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)['runtime_validation'], 'not-checked')
        synchronize(self.root)
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'consistent')


if __name__ == '__main__':
    unittest.main()
