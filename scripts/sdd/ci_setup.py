"""Check local activation files; never claim to have inspected GitHub settings."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
from .common import ConfigError, inside, load_json
from .ci import ci_configuration

PROTECTED = ('/.github/', '/.sdd/', '/.agents/', '/.claude/', '/.cursor/', '/.codex/', '/scripts/',
             '/AGENTS.md', '/CLAUDE.md', '/README.md', '/docs/development/', '/docs/templates/')
OWNER = re.compile(r'@[A-Za-z0-9][A-Za-z0-9-]*(?:/[A-Za-z0-9][A-Za-z0-9_-]*)?')


def owners(text: str) -> list[str]:
    errors = []
    rows = [line.split() for line in text.splitlines() if line.strip() and not line.lstrip().startswith('#')]
    if len(rows) < len(PROTECTED):
        errors.append('CODEOWNERS must end with every protected pattern from the example')
    for row in rows:
        if len(row) < 2 or any(not OWNER.fullmatch(value) or re.search('replace|example|tbd', value, re.I) for value in row[1:]):
            errors.append('Every CODEOWNERS row needs real @user or @organization/team owners, not placeholders')
    if [row[0] for row in rows[-len(PROTECTED):]] != list(PROTECTED):
        errors.append('Keep the protected block last and in the example order to prevent later overrides')
    return errors


def check_setup(root: Path) -> dict:
    ci_configuration(root)
    path = inside(root, '.github/CODEOWNERS')
    errors = owners(path.read_text(encoding='utf-8')) if path.is_file() else ['Missing .github/CODEOWNERS; customize the example first']
    return {'status': 'blocked' if errors else 'local-files-ready', 'errors': errors,
            'remote_enforcement': 'not-checked',
            'remaining': ['Verify owner existence, team visibility, and write permission in GitHub',
                          'Activate required sdd-gate, current approvals, code-owner reviews, and no routine bypass',
                          'Inspect Actions permissions, fork policies, and actual failed-PR merge blocking']}


def main(argv: list[str] | None = None, default_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=default_root or Path.cwd())
    args = parser.parse_args(argv)
    try:
        report = check_setup(args.root.resolve())
        code = 3 if report['status'] == 'blocked' else 0
    except (ConfigError, OSError, UnicodeError) as exc:
        report, code = {'status': 'error', 'errors': [str(exc)]}, 2
    print(json.dumps(report, indent=2))
    return code
