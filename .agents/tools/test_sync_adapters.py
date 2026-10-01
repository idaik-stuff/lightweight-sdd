"""Framework-maintenance tests. These do not execute an agent or verify a product."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from sync_adapters import AdapterError, MARKER, PHASES, read_skill, render_expected, synchronize

RELEASE = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).with_name('sync_adapters.py')


class AdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'AGENTS.md').write_text('# Test repository\n', encoding='utf-8')
        for relative in ['.agents/workflows', '.agents/adapters', '.agents/review']:
            shutil.copytree(RELEASE / relative, self.root / relative)

    def change_manifest(self, transform) -> None:
        path = self.root / '.agents/adapters/clients.json'
        data = json.loads(path.read_text())
        transform(data)
        path.write_text(json.dumps(data), encoding='utf-8')

    def target(self, phase: str = 'spec') -> Path:
        return self.root / f'.claude/skills/sdd-{phase}/SKILL.md'

    def test_generate_all_client_adapters(self):
        self.assertEqual(len(synchronize(self.root)), 20)
        for relative, expected in render_expected(self.root).items():
            self.assertEqual((self.root / relative).read_text(), expected)

    def test_generation_is_idempotent(self):
        synchronize(self.root)
        self.assertEqual(synchronize(self.root), [])

    def test_check_missing_files_does_not_write(self):
        self.assertEqual(len(synchronize(self.root, check=True)), 20)
        self.assertFalse((self.root / '.claude').exists())

    def test_clean_check_preserves_mtimes(self):
        synchronize(self.root)
        before = {p: p.stat().st_mtime_ns for p in (self.root / '.claude').rglob('*') if p.is_file()}
        self.assertEqual(synchronize(self.root, check=True), [])
        self.assertEqual(before, {p: p.stat().st_mtime_ns for p in before})

    def test_stale_owned_file_is_reported_without_writes(self):
        synchronize(self.root)
        path = self.target()
        path.write_text(path.read_text() + '\nOwned local change\n')
        before = path.read_bytes()
        self.assertEqual(synchronize(self.root, check=True), ['.claude/skills/sdd-spec/SKILL.md'])
        self.assertEqual(path.read_bytes(), before)

    def test_stale_owned_file_is_regenerated(self):
        synchronize(self.root)
        self.target().write_text(MARKER + '\nOld generated content\n')
        self.assertEqual(len(synchronize(self.root)), 1)
        self.assertEqual(synchronize(self.root, check=True), [])

    def test_unowned_file_blocks_all_writes(self):
        path = self.target('verify')
        path.parent.mkdir(parents=True)
        path.write_text('# User-owned skill\n')
        with self.assertRaisesRegex(AdapterError, 'unowned'):
            synchronize(self.root)
        self.assertEqual(path.read_text(), '# User-owned skill\n')
        self.assertFalse(self.target('investigate').exists())

    def test_unrelated_settings_are_preserved(self):
        settings = self.root / '.claude/settings.json'
        settings.parent.mkdir()
        settings.write_text('{"custom":true}')
        synchronize(self.root)
        self.assertEqual(settings.read_text(), '{"custom":true}')

    def test_only_implement_is_manual_only(self):
        outputs = render_expected(self.root)
        for phase in PHASES:
            content = outputs[f'.claude/skills/sdd-{phase}/SKILL.md']
            self.assertEqual('disable-model-invocation: true' in content, phase == 'implement')

    def test_reviewer_has_no_shell_or_write_tools(self):
        text = render_expected(self.root)['.claude/agents/sdd-independent-review.md']
        self.assertIn('tools: Read, Grep, Glob\n', text)
        self.assertNotIn('Bash', text)
        self.assertNotIn('tools: Write', text)

    def test_command_path_traversal_is_rejected(self):
        self.change_manifest(lambda d: d['skills'][0].update(command='../escape'))
        with self.assertRaises(AdapterError):
            synchronize(self.root)

    def test_duplicate_phase_is_rejected(self):
        self.change_manifest(lambda d: d['skills'][1].update(source='investigate'))
        with self.assertRaises(AdapterError):
            synchronize(self.root)

    def test_duplicate_command_is_rejected(self):
        self.change_manifest(lambda d: d['skills'][1].update(command='sdd-investigate'))
        with self.assertRaises(AdapterError):
            synchronize(self.root)

    def test_wrong_schema_is_rejected(self):
        self.change_manifest(lambda d: d.update(schema_version=3))
        with self.assertRaises(AdapterError):
            synchronize(self.root)

    def test_automatic_implementation_change_is_rejected(self):
        self.change_manifest(lambda d: d['skills'][3].update(manual_only=False))
        with self.assertRaises(AdapterError):
            synchronize(self.root)

    def test_reviewer_shell_grant_is_rejected(self):
        self.change_manifest(lambda d: d['reviewer']['tools'].append('Bash'))
        with self.assertRaises(AdapterError):
            synchronize(self.root)

    def test_missing_canonical_skill_is_rejected(self):
        (self.root / '.agents/workflows/spec/SKILL.md').unlink()
        with self.assertRaises(FileNotFoundError):
            synchronize(self.root)

    def test_mismatched_skill_name_is_rejected(self):
        path = self.root / '.agents/workflows/spec/SKILL.md'
        path.write_text(path.read_text().replace('name: spec\n', 'name: other\n'))
        with self.assertRaises(AdapterError):
            synchronize(self.root)

    def test_invalid_frontmatter_is_rejected(self):
        path = self.root / '.agents/workflows/spec/SKILL.md'
        path.write_text('---\nname: spec\ndescription: >\n  folded\n---\nBody\n')
        with self.assertRaisesRegex(AdapterError, 'JSON-quoted'):
            read_skill(path, 'spec')

    def test_symlink_destination_is_rejected(self):
        outside = self.root / 'outside'
        outside.mkdir()
        try:
            (self.root / '.claude').symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f'Symlinks unavailable: {exc}')
        with self.assertRaisesRegex(AdapterError, 'symlinked'):
            synchronize(self.root)
        self.assertEqual(list(outside.iterdir()), [])

    def test_cli_reports_drift_and_success(self):
        command = [sys.executable, str(SCRIPT), '--root', str(self.root)]
        pending = subprocess.run(command + ['--check'], capture_output=True, text=True)
        self.assertEqual(pending.returncode, 1, pending.stderr)
        built = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(built.returncode, 0, built.stderr)
        checked = subprocess.run(command + ['--check'], capture_output=True, text=True)
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_cli_default_root_is_independent_of_cwd(self):
        tool = self.root / '.agents/tools/sync_adapters.py'
        tool.parent.mkdir()
        shutil.copy2(SCRIPT, tool)
        other_cwd = self.root / 'unrelated-working-directory'
        other_cwd.mkdir()
        result = subprocess.run([sys.executable, str(tool)], cwd=other_cwd,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.target().exists())


if __name__ == '__main__':
    unittest.main()
