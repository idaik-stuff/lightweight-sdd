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
# Client rows apply only when that client's files are installed in the repository.
CLIENT_ROWS = {'/.claude/': '.claude', '/CLAUDE.md': 'CLAUDE.md', '/.cursor/': '.cursor', '/.codex/': '.codex'}
OWNER = re.compile(r'@[A-Za-z0-9][A-Za-z0-9-]*(?:/[A-Za-z0-9][A-Za-z0-9_-]*)?')


def protected(root: Path) -> tuple[str, ...]:
    return tuple(p for p in PROTECTED if p not in CLIENT_ROWS or (root / CLIENT_ROWS[p]).exists())


def owners(text: str, patterns: tuple[str, ...] = PROTECTED) -> list[str]:
    """The file must end with a protected block: every required pattern, in example order.

    Rows for clients that are not installed may stay in the block; nothing may follow it.
    """
    errors = []
    rows = [line.split() for line in text.splitlines() if line.strip() and not line.lstrip().startswith('#')]
    for row in rows:
        if len(row) < 2 or any(not OWNER.fullmatch(value) or re.search('replace|example|tbd', value, re.I) for value in row[1:]):
            errors.append('Every CODEOWNERS row needs real @user or @organization/team owners, not placeholders')
    block: list[str] = []
    for row in reversed(rows):
        if row[0] not in PROTECTED:
            break
        block.insert(0, row[0])
    if len(set(block)) != len(block) or block != [p for p in PROTECTED if p in block]:
        errors.append('Keep the protected block last and in the example order to prevent later overrides')
    missing = [p for p in patterns if p not in block]
    if missing:
        errors.append('CODEOWNERS must end with every protected pattern from the example; missing ' + ', '.join(missing))
    return sorted(set(errors))


def check_setup(root: Path) -> dict:
    ci_configuration(root)
    path = inside(root, '.github/CODEOWNERS')
    errors = owners(path.read_text(encoding='utf-8'), protected(root)) if path.is_file() else ['Missing .github/CODEOWNERS; customize the example first']
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
