"""CI policy loading and routing shared by CI assessment and local verification."""
from __future__ import annotations

from pathlib import Path
import tempfile

from .changes import LEVELS, SCOPES, matches
from .common import ConfigError, commit, git, inside, load_json, require_keys

FRAMEWORK_CI = ".sdd/ci.json"
PRODUCT_CI = ".sdd/product-ci.json"
# Synthetic paths that no real product layout uses; a product pattern matching them matches everything.
PROBES = ("zz-sdd-probe", "zz-sdd-probe/zz-sdd-probe.txt", "zz-sdd-probe/zz/zz.py",
          "zz-sdd-probe/zz/zz.ts", "zz-sdd-probe/zz/zz.js", "zz-sdd-probe/zz/zz.go")


def patterns(values, source: str, group: str, nonempty: bool) -> list[str]:
    if not isinstance(values, list) or (nonempty and not values):
        raise ConfigError(f"{source}: {group} must be a {'nonempty ' if nonempty else ''}list")
    for value in values:
        if not isinstance(value, str) or not value or value.startswith('/') or '\\' in value \
                or '..' in value.split('/') or '\x00' in value:
            raise ConfigError(f"{source}: invalid CI path pattern")
    return values


def ci_configuration(root: Path) -> dict:
    """The framework-owned .sdd/ci.json, validated."""
    data = load_json(inside(root, FRAMEWORK_CI))
    require_keys(data, {'version', 'framework_paths', 'design_paths', 'scopes'})
    if type(data['version']) is not int or data['version'] != 1:
        raise ConfigError('Unsupported CI policy version')
    for group in ('framework_paths', 'design_paths'):
        patterns(data[group], FRAMEWORK_CI, group, nonempty=True)
    require_keys(data['scopes'], set(LEVELS))
    for level, mode in data['scopes'].items():
        minimum = 'broad' if level == 'L3' else 'standard' if level == 'L2' else 'focused'
        if not isinstance(mode, str) or mode not in SCOPES or SCOPES[mode] < SCOPES[minimum]:
            raise ConfigError(f'{level} cannot use a scope below {minimum}')
    return data


def merge(data: dict, extra) -> dict:
    """Apply product CI settings to the framework policy: add framework paths, raise scopes only."""
    try:
        require_keys(extra, {'version'}, {'framework_paths', 'scopes'})
    except ConfigError as exc:
        raise ConfigError(f'{PRODUCT_CI}: {exc}') from exc
    if type(extra['version']) is not int or extra['version'] != 1:
        raise ConfigError(f'{PRODUCT_CI}: unsupported version')
    merged = {**data, 'framework_paths': list(data['framework_paths']), 'scopes': dict(data['scopes'])}
    if 'framework_paths' in extra:
        added = patterns(extra['framework_paths'], PRODUCT_CI, 'framework_paths', nonempty=False)
        for pattern in added:
            if any(matches(probe, pattern) for probe in PROBES):
                raise ConfigError(f'{PRODUCT_CI}: framework_paths pattern {pattern!r} matches arbitrary '
                                  'product paths (note that * also matches /), so they would run no product checks')
        merged['framework_paths'] += added
    scopes = extra.get('scopes', {})
    if not isinstance(scopes, dict) or set(scopes) - set(LEVELS):
        raise ConfigError(f'{PRODUCT_CI}: scopes must map levels L0-L3 to scopes')
    for level, mode in scopes.items():
        if not isinstance(mode, str) or mode not in SCOPES:
            raise ConfigError(f'{PRODUCT_CI}: invalid scope for {level}')
        if SCOPES[mode] < SCOPES[data['scopes'][level]]:
            raise ConfigError(f'{PRODUCT_CI}: {level} cannot lower the scope below {data["scopes"][level]}')
        merged['scopes'][level] = mode
    return merged


def ci_policy(root: Path) -> dict:
    """The framework policy, extended by the product's own settings when present."""
    data = ci_configuration(root)
    product = inside(root, PRODUCT_CI)
    # A dangling link fails closed instead of silently dropping the product settings.
    if not product.exists() and not product.is_symlink():
        return data
    return merge(data, load_json(product))


def ci_policy_at(root: Path, revision: str) -> dict:
    """The CI policy as committed at a revision (what CI would read from that base)."""
    resolved = commit(root, revision)
    with tempfile.TemporaryDirectory(prefix="sdd-policy-") as folder:
        snapshot = Path(folder)
        (snapshot / ".sdd").mkdir()
        for path in (FRAMEWORK_CI, PRODUCT_CI):
            entry = git(root, "ls-tree", resolved, "--", path).decode().strip()
            if not entry:
                continue
            if not entry.startswith(("100644 blob ", "100755 blob ")):
                raise ConfigError(f"{path} at {resolved[:12]} is not a regular file")
            (snapshot / path).write_bytes(git(root, "show", f"{resolved}:{path}"))
        return ci_policy(snapshot)


def route(policy: dict, paths: list[str]) -> tuple[str, bool]:
    """(target, design_only): framework only when every changed path is a framework path."""
    target = 'framework' if all(any(matches(p, g) for g in policy['framework_paths']) for p in paths) else 'product'
    design = all(p.endswith('.md') and any(matches(p, g) for g in policy['design_paths']) for p in paths)
    return target, design
