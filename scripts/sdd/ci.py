"""Assess a PR using base-branch policy, without importing candidate Python code."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from .changes import LEVELS, SCOPES, load_rules, matches
from .common import ConfigError, commit, git, git_root, inside, load_json, nul_paths, relative_path, require_keys
from .docs import change_id, check_docs, field, read_markdown, validate_change
from .verify import configuration, select

START, END = '<!-- sdd:metadata -->', '<!-- /sdd:metadata -->'
SHA = re.compile(r'[0-9a-f]{40}')


def metadata(body: str | None) -> dict[str, str]:
    if not isinstance(body, str) or len(body) > 100000 or body.count(START) != 1 or body.count(END) != 1:
        raise ConfigError('PR body needs exactly one sdd:metadata block')
    start, end = body.index(START) + len(START), body.index(END)
    if end < start:
        raise ConfigError('Reversed metadata delimiters')
    values: dict[str, str] = {}
    for line in body[start:end].strip().splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r'(Change-Level|Change-ID): ([A-Za-z0-9._-]+)', line)
        if not match or match[1] in values:
            raise ConfigError('Metadata requires exactly one Change-Level and Change-ID; no extra fields')
        values[match[1]] = match[2]
    if set(values) != {'Change-Level', 'Change-ID'} or values['Change-Level'] not in LEVELS:
        raise ConfigError('Declare Change-Level: L0/L1/L2/L3 and Change-ID: ID or none')
    if values['Change-ID'] != 'none':
        change_id(values['Change-ID'])
    return {'level': values['Change-Level'], 'change': values['Change-ID']}


def ci_configuration(root: Path) -> dict:
    data = load_json(inside(root, '.sdd/ci.json'))
    require_keys(data, {'version', 'framework_paths', 'design_paths', 'scopes'})
    if type(data['version']) is not int or data['version'] != 1:
        raise ConfigError('Unsupported CI policy version')
    for group in ('framework_paths', 'design_paths'):
        values = data[group]
        if not isinstance(values, list) or not values:
            raise ConfigError(f'{group} must be a nonempty list')
        for value in values:
            if not isinstance(value, str) or not value or value.startswith('/') or '\\' in value or '..' in value.split('/') or '\x00' in value:
                raise ConfigError('Invalid CI path pattern')
    require_keys(data['scopes'], set(LEVELS))
    for level, mode in data['scopes'].items():
        minimum = 'broad' if level == 'L3' else 'standard' if level == 'L2' else 'focused'
        if not isinstance(mode, str) or mode not in SCOPES or SCOPES[mode] < SCOPES[minimum]:
            raise ConfigError(f'{level} cannot use a scope below {minimum}')
    return data


def clean_checkout(root: Path, expected: str) -> None:
    git_root(root)
    if commit(root, 'HEAD') != expected:
        raise ConfigError('Checkout HEAD does not match the event commit')
    if git(root, 'status', '--porcelain=v1', '--untracked-files=all').strip():
        raise ConfigError('CI requires clean, committed checkouts')
    # Reject symlinks and submodules before Markdown readers access candidate paths.
    for record in git(root, 'ls-tree', '-r', '-z', expected).split(b'\x00'):
        if record and not record.startswith((b'100644 blob ', b'100755 blob ')):
            raise ConfigError('CI adapter does not support symlinks or submodules')


def event_context(event: dict, expected_sha: str) -> tuple[str, str, str | None]:
    try:
        pr = event['pull_request']
        base, head = pr['base']['sha'], pr['head']['sha']
        body = pr.get('body')
        repo = event['repository']['full_name']
        if pr['base']['repo']['full_name'] != repo or pr['state'] != 'open':
            raise ConfigError('Expected an open PR into this repository')
        if event['action'] not in {'opened', 'synchronize', 'reopened', 'edited', 'ready_for_review'}:
            raise ConfigError('Unsupported event action; merge queues and pushes need another adapter')
    except (KeyError, TypeError) as exc:
        raise ConfigError('Expected a GitHub pull_request event') from exc
    if not all(isinstance(value, str) and SHA.fullmatch(value) for value in (base, head, expected_sha)):
        raise ConfigError('Expected full SHA-1 commit identifiers')
    return base, head, body


def assess_ci(trusted: Path, candidate: Path, event: dict, expected_sha: str) -> dict:
    trusted, candidate = trusted.resolve(), candidate.resolve()
    if trusted == candidate or trusted in candidate.parents or candidate in trusted.parents:
        raise ConfigError('Trusted policy and candidate require separate, non-nested checkouts')
    base, head, body = event_context(event, expected_sha)
    clean_checkout(trusted, base)
    clean_checkout(candidate, expected_sha)
    parents = git(candidate, 'rev-list', '--parents', '-n', '1', expected_sha).decode().split()
    if parents != [expected_sha, base, head]:
        raise ConfigError('Expected the PR test merge with exactly the event base and head as parents')
    policy = ci_configuration(trusted)
    rules = load_rules(trusted)
    declared = metadata(body)
    paths = sorted(set(nul_paths(git(candidate, 'diff', '--name-only', '-z', '--no-renames',
                                    '--no-ext-diff', '--no-textconv', base, expected_sha, '--'))))
    for path in paths:
        relative_path(path)
    if not paths:
        raise ConfigError('No changes in the tested PR merge')
    hits = []
    floor = 0
    for rule in rules:
        changed = [p for p in paths if any(matches(p, glob) for glob in rule['paths'])]
        if changed:
            floor = max(floor, LEVELS[rule['minimum_level']])
            hits.append({'id': rule['id'], 'paths': changed, 'minimum_level': rule['minimum_level']})
    required = max(floor, LEVELS[declared['level']])
    mode = policy['scopes'][f'L{required}']
    target = 'framework' if all(any(matches(p, g) for g in policy['framework_paths']) for p in paths) else 'product'
    design = all(p.endswith('.md') and any(matches(p, g) for g in policy['design_paths']) for p in paths)
    errors: list[str] = []
    if LEVELS[declared['level']] < floor:
        errors.append(f'Declared {declared["level"]} is below the base-policy floor L{floor}')
    # Only code from the trusted interpreter is used for both document reads and validation.
    errors.extend(check_docs(candidate)['errors'])
    identifier = declared['change']
    if required >= 2 and not design and identifier == 'none':
        errors.append('L2/L3 implementation requires Change-ID and its spec/plan pair')
    if identifier != 'none':
        errors.extend(validate_change(candidate, identifier, require_pair=not design))
        spec = inside(candidate, f'docs/specs/{identifier}/spec.md')
        plan = inside(candidate, f'docs/specs/{identifier}/plan.md')
        if spec.is_file() and field(read_markdown(spec), 'Level') != declared['level']:
            errors.append('Spec Level disagrees with the declaration')
        if not design:
            if spec.is_file() and field(read_markdown(spec), 'Status') not in {'approved', 'implemented'}:
                errors.append('Implementation needs an approved or implemented spec; not a draft/cancelled record')
            if plan.is_file() and field(read_markdown(plan), 'Status') not in {'approved', 'in-progress', 'completed'}:
                errors.append('Implementation needs an approved, in-progress, or completed plan')
    # Candidate registration is parsed for validity, never used to select this run's commands.
    configuration(candidate)
    ci_configuration(candidate)
    checks = select(configuration(trusted, execution_root=candidate), target, mode)
    if not checks or (target == 'product' and not any(c['kind'] == 'product' for c in checks)):
        errors.append('Required checks are absent in the base policy; register real product checks in a separate reviewed change')
    return {'schema_version': 1, 'status': 'failed' if errors else 'passed',
            **declared, 'scope': mode, 'target': target, 'design_only': design,
            'base': base, 'head': head, 'merge': expected_sha,
            'metadata_sha256': hashlib.sha256(body.encode()).hexdigest(),
            'paths': paths, 'detected_floor': f'L{floor}', 'matches': hits,
            'check_ids': [c['id'] for c in checks], 'errors': errors,
            'policy_source': 'PR base commit', 'review': 'server-side requirement; not authenticated by this check',
            'limitations': ['The workflow itself needs protected ownership or an organization-required workflow',
                           'Path rules cannot establish full semantic risk or adequate tests',
                           'Document acceptance text is not authenticated human approval',
                           'This adapter supports pull_request test merges, not merge queues']}


def final_gate(results: list[str]) -> bool:
    return bool(results) and all(result == 'success' for result in results)


def main(argv: list[str] | None = None, default_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate-root', type=Path, required=True)
    parser.add_argument('--event', type=Path, required=True)
    parser.add_argument('--expected-sha', required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--github-output', type=Path)
    args = parser.parse_args(argv)
    trusted = (default_root or Path(__file__).resolve().parents[2]).resolve()
    try:
        report = assess_ci(trusted, args.candidate_root, load_json(args.event), args.expected_sha)
        code = 0 if report['status'] == 'passed' else 1
    except (ConfigError, OSError, UnicodeError) as exc:
        report, code = {'status': 'error', 'errors': [str(exc)]}, 2
    # Output locations are supplied by the trusted workflow, never by PR metadata.
    try:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        if code == 0 and args.github_output:
            with args.github_output.open('a', encoding='utf-8') as out:
                for key in ('level', 'change', 'scope', 'target', 'base', 'head', 'merge'):
                    out.write(f'{key}={report[key]}\n')
                out.write('design_only=' + str(report['design_only']).lower() + '\n')
    except OSError as exc:
        print(f'Cannot record CI evidence: {exc}')
        return 2
    print(json.dumps(report, indent=2))
    return code
