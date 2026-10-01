"""Conservative risk floors over an explicitly based Git working snapshot."""
from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path
import re

from .common import ConfigError, commit, git, git_root, inside, load_json, nul_paths, repo_paths, require_keys
from .docs import change_id, field, read_markdown, validate_change

LEVELS = {f"L{i}": i for i in range(4)}
SCOPES = {"focused": 0, "standard": 1, "broad": 2}


def matches(path: str, pattern: str) -> bool:
    """fnmatchcase over POSIX paths; leading **/ also matches at the root."""
    return fnmatch.fnmatchcase(path, pattern) or (pattern.startswith("**/") and fnmatch.fnmatchcase(path, pattern[3:]))


def load_rules(root: Path) -> list[dict]:
    data = load_json(inside(root, ".sdd/risk-rules.json"))
    require_keys(data, {"version", "rules"})
    if type(data["version"]) is not int or data["version"] != 1 or not isinstance(data["rules"], list):
        raise ConfigError("Unsupported risk rules format")
    ids: set[str] = set()
    for rule in data["rules"]:
        require_keys(rule, {"id", "minimum_level", "paths", "reason"})
        if not isinstance(rule["id"], str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", rule["id"]) or rule["id"] in ids:
            raise ConfigError("Risk rule IDs must be unique lowercase names")
        ids.add(rule["id"])
        if not isinstance(rule["minimum_level"], str) or rule["minimum_level"] not in LEVELS or not isinstance(rule["reason"], str) or not rule["reason"].strip():
            raise ConfigError("Invalid risk floor or reason")
        if not isinstance(rule["paths"], list) or not rule["paths"]:
            raise ConfigError("Risk rules need at least one path pattern")
        for pattern in rule["paths"]:
            if not isinstance(pattern, str) or not pattern or pattern.startswith("/") or ".." in pattern.split("/") or "\\" in pattern or "\x00" in pattern:
                raise ConfigError("Invalid risk path pattern")
    return data["rules"]


def changed_paths(root: Path, base: str) -> tuple[list[str], str]:
    git_root(root)
    # Validate conflicts, submodules, index flags, and report-directory tracking too.
    repo_paths(root)
    resolved = commit(root, base)
    options = ["--name-only", "-z", "--no-renames", "--no-ext-diff", "--no-textconv"]
    work = nul_paths(git(root, "diff", *options, resolved, "--"))
    staged = nul_paths(git(root, "diff", "--cached", *options, resolved, "--"))
    other = nul_paths(git(root, "ls-files", "--others", "--exclude-standard", "-z"))
    # Disabling rename detection retains both the old and new paths for risk matching.
    paths = sorted(set(work + staged + [p for p in other if not p.startswith(".sdd/results/")]))
    return paths, resolved


def assess(root: Path, base: str, declared: str, change: str | None = None, scope: str | None = None, policy_root: Path | None = None) -> dict:
    if declared not in LEVELS:
        raise ConfigError("Declared level must be L0, L1, L2, or L3")
    if scope is not None and scope not in SCOPES:
        raise ConfigError("Invalid verification scope")
    rules = load_rules(policy_root or root)
    paths, resolved = changed_paths(root, base)
    matches_found: list[dict] = []
    floor = 0
    for rule in rules:
        hits = [p for p in paths if any(matches(p, pattern) for pattern in rule["paths"])]
        if hits:
            floor = max(floor, LEVELS[rule["minimum_level"]])
            matches_found.append({"rule": rule["id"], "minimum_level": rule["minimum_level"],
                                  "reason": rule["reason"], "paths": hits})
    required = max(LEVELS[declared], floor)
    errors: list[str] = []
    if LEVELS[declared] < floor:
        errors.append(f"Declared {declared} is below detected minimum L{floor}; reclassify before continuing")
    required_scope = "broad" if required == 3 else "standard" if required == 2 else "focused"
    if scope is not None and SCOPES[scope] < SCOPES[required_scope]:
        errors.append(f"Level L{required} requires at least {required_scope} verification")
    if required >= 2 and not change:
        errors.append("L2/L3 requires --change with its paired spec.md and plan.md")
    if change:
        change_id(change)
        errors.extend(validate_change(root, change, require_pair=True))
        spec = inside(root, f"docs/specs/{change}/spec.md")
        if spec.is_file() and field(read_markdown(spec), "Level") != declared:
            errors.append("The spec's Level differs from the declared level")
    status = "failed" if errors else "passed" if paths else "blocked"
    return {"status": status, "base_commit": resolved, "declared_level": declared,
            "detected_floor": f"L{floor}", "required_level": f"L{required}",
            "minimum_scope": required_scope, "change": change, "paths": paths,
            "matches": matches_found, "errors": errors,
            "reason": "No changes relative to the explicit base" if not paths else None,
            "readiness": "not-assessed", "policy_source": "external trusted policy" if policy_root else "working-tree .sdd/risk-rules.json",
            "limitations": ["Path heuristics only; no match does not prove low risk",
                            "Rules and scripts are locally editable, not a trusted enforcement boundary",
                            "Artifact structure does not prove authorization, semantic coverage, or independent review"]}


def main(argv: list[str] | None = None, default_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=default_root or Path.cwd())
    parser.add_argument("--base", required=True, help="Explicit commit/revision; compare it with the current working snapshot")
    parser.add_argument("--level", required=True, choices=LEVELS)
    parser.add_argument("--change", help="Change directory ID, required for L2/L3")
    parser.add_argument("--scope", choices=SCOPES)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = assess(args.root.resolve(), args.base, args.level, args.change, args.scope)
        code = {"passed": 0, "failed": 1, "blocked": 3}[report["status"]]
    except (ConfigError, OSError) as exc:
        report, code = {"status": "error", "errors": [str(exc)]}, 2
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Change checks: {report['status']} (not a readiness or approval decision)")
        if "required_level" in report:
            print(f"Declared {report['declared_level']}; detected floor {report['detected_floor']}; "
                  f"required {report['required_level']}; {len(report['paths'])} changed paths")
        for match in report.get("matches", []):
            print(f"  {match['rule']}: {match['minimum_level']} - {match['reason']}")
        for error in report["errors"]:
            print(f"  {error}")
        if report.get("reason"):
            print(f"  {report['reason']}")
    return code
