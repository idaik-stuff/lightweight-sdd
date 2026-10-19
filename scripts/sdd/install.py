"""Install or upgrade the framework in a product repository, for the chosen clients only."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile

from .changes import LEVELS, branch_guard, matches
from .common import ConfigError, git, git_root, load_json, relative_path
from .policy import PRODUCT_CI, merge

SOURCE = Path(__file__).resolve().parents[2]
CLIENTS = ("claude", "codex", "cursor", "copilot-vscode")

# Framework-owned: copied on install, replaced on upgrade.
FRAMEWORK = (
    "AGENTS.md", ".agents/README.md", ".agents/workflows/**", ".agents/review/**",
    ".agents/references/**", ".agents/evals/**",
    ".github/workflows/sdd.yml", ".github/workflows/sdd-direct-push.yml",
    ".github/pull_request_template.md", ".github/sdd-ruleset.template.json",
    "scripts/**", "docs/development/**", "docs/templates/**", "docs/README.md", "docs/specs/README.md",
    ".sdd/ci.json",
)
# Generated framework-owned files: the framework rules without framework-repository-only paths.
FRAMEWORK_RULES = ".sdd/risk-rules.json"
PRODUCT_RULES = ".sdd/product-risk-rules.json"
FRAMEWORK_ONLY = (".agents/tools/**", ".agents/adapters/**")
# The installer needs a framework checkout, so it and its tests are never shipped.
EXCLUDED = ("scripts/install", "scripts/sdd/install.py", "scripts/tests/test_install.py")
CLIENT_FILES = {
    "claude": ("CLAUDE.md", ".claude/skills/**", ".claude/agents/**"),
    "codex": (".agents/skills/**", ".codex/agents/**"),
    "cursor": (".agents/skills/**", ".cursor/agents/**"),
    "copilot-vscode": (".agents/skills/**", ".github/agents/**", ".github/copilot-instructions.md"),
}
# Product-owned: created when missing (install or upgrade), never replaced.
PRODUCT = ("docs/product/brief.md", "docs/product/mvp.md", "docs/product/prd.md",
           "docs/architecture/overview.md", "docs/adr/README.md", "docs/project-rules.md",
           PRODUCT_RULES, PRODUCT_CI)
GENERATOR_CHECKS = {"adapters", "adapter-tests"}
REQUIRED_LINES = {".gitignore": (".sdd/results/",), ".gitattributes": ("* text=auto eol=lf",)}
CODEOWNERS_EXAMPLE = ".github/CODEOWNERS.example"
RECORD = ".sdd/install.json"
CLIENT_ROWS = {"/.claude/": "claude", "/CLAUDE.md": "claude", "/.cursor/": "cursor", "/.codex/": "codex"}
README_STUB = """# Project name

Describe the project here.

## Commands

Framework commands: [docs/development/commands.md](docs/development/commands.md).

| Operation | Command | Scope / prerequisites |
| --- | --- | --- |
| TBD | TBD | Register real product checks in `.sdd/verification.json` too. |
"""
MIGRATION = ("This looks like a framework 1.0.0 repository. Migrate it first, in a change branch: "
             "move any rules you added to AGENTS.md into docs/project-rules.md; move the product rules "
             "(public-contract, security-boundary, persistent-data, production-delivery, and any of your own) "
             "from .sdd/risk-rules.json into .sdd/product-risk-rules.json, with any patterns you added to the "
             "framework rules (in the same pull request as the upgrade, so no floor is unenforced in between); "
             "note that .sdd/ci.json will be replaced; remove the 'adapters' and "
             "'adapter-tests' checks from .sdd/verification.json; delete .agents/tools/ and "
             ".agents/adapters/; commit; then run the installer with --clients")


class WriteError(Exception):
    def __init__(self, message: str, written: list[str]):
        super().__init__(message)
        self.written = written


def text(data: str) -> bytes:
    return data.encode("utf-8")


def git_list(root: Path, *args: str) -> list[str]:
    return sorted(os.fsdecode(p) for p in git(root, *args, "-z").split(b"\x00") if p)


def executable_paths(root: Path) -> set[str]:
    """Paths recorded as executable in the source index, independent of core.fileMode."""
    entries = git(root, "ls-files", "-s", "-z").split(b"\x00")
    return {os.fsdecode(e.split(b"\t", 1)[1]) for e in entries if e.startswith(b"100755 ")}


def selected(paths: list[str], patterns: tuple[str, ...]) -> list[str]:
    return [p for p in paths if any(matches(p, pattern) for pattern in patterns)]


def parse_clients(value: str | None) -> list[str] | None:
    if value is None:
        return None
    names = [name.strip() for name in value.split(",") if name.strip()]
    unknown = [name for name in names if name not in CLIENTS]
    if not names or unknown or len(set(names)) != len(names):
        raise ConfigError(f"Choose one or more distinct clients from {', '.join(CLIENTS)}; got {value!r}")
    return [name for name in CLIENTS if name in names]


def unsafe(target: Path, path: str) -> str | None:
    """Why a destination cannot be written safely, or None.

    Every existing component must be a real directory (no symlinks, no files in the way),
    the leaf must be absent or a regular file, and nothing may land inside .git/.
    """
    parts = PurePosixPath(relative_path(path)).parts
    if ".git" in parts:
        return "inside .git/"
    current = target
    for index, part in enumerate(parts):
        current = current / part
        if current.is_symlink():
            return f"symlink at {PurePosixPath(*parts[:index + 1])}"
        if not current.exists():
            return None
        if index < len(parts) - 1 and not current.is_dir():
            return f"{PurePosixPath(*parts[:index + 1])} is not a directory"
    return None if current.is_file() else "not a regular file"


def source_checks(source: Path, allow_dirty: bool) -> bool:
    """The source must be a framework checkout without adapter drift; returns dirtiness."""
    tool = source / ".agents/tools/sync_adapters.py"
    if not tool.is_file():
        raise ConfigError("Run the installer from a framework checkout (missing .agents/tools)")
    spec = importlib.util.spec_from_file_location("sdd_sync_adapters", tool)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    stale = module.synchronize(source, check=True)
    if stale:
        raise ConfigError("Source adapters are stale; run sync_adapters.py first: " + ", ".join(stale))
    dirty = bool(git(source, "status", "--porcelain=v1", "--untracked-files=all").strip())
    if dirty and not allow_dirty:
        raise ConfigError("The framework checkout has uncommitted or untracked files; commit them, "
                          "or pass --allow-dirty-source to ship them deliberately")
    return dirty


def target_checks(source: Path, target: Path) -> None:
    if not target.is_dir():
        raise ConfigError(f"Target is not a directory: {target}")
    git_root(target)
    if target.resolve() == source.resolve():
        raise ConfigError("Target is the framework checkout itself")
    branch, _, errors = branch_guard(target)
    if branch is None:
        errors = ["Target is on a detached HEAD; check out a change branch first"]
    if errors:
        raise ConfigError("; ".join(errors))
    if git(target, "status", "--porcelain=v1", "--untracked-files=all").strip():
        raise ConfigError("Target worktree has uncommitted or untracked changes; commit or stash them first")


def read_json(target: Path, path: str) -> dict:
    reason = unsafe(target, path)
    if reason:
        raise ConfigError(f"Cannot read {path}: {reason}")
    return load_json(target / path)


def mode(target: Path, clients: list[str] | None) -> tuple[str, list[str], list[str] | None]:
    """Return (mode, clients, previously installed files or None)."""
    if (target / RECORD).exists() or (target / RECORD).is_symlink():
        record = read_json(target, RECORD)
        chosen = clients or parse_clients(",".join(record["clients"]))
        return "upgrade", chosen, record.get("files")
    if not (target / ".sdd").exists() and not (target / ".sdd").is_symlink():
        if clients is None:
            raise ConfigError("Name the clients with --clients")
        return "install", clients, None
    if unsafe(target, ".sdd/verification.json") or not (target / ".sdd/verification.json").is_file() \
            or not (target / "scripts/sdd").is_dir():
        raise ConfigError("Target has a .sdd/ that is not a framework installation; rename it first")
    checks = {c.get("id") for c in read_json(target, ".sdd/verification.json").get("checks", [])}
    if (target / ".agents/tools").exists() or checks & GENERATOR_CHECKS:
        raise ConfigError(MIGRATION)
    if clients is None:
        raise ConfigError("No .sdd/install.json to reuse; name the clients with --clients")
    return "upgrade", clients, None


def product_verification(source: Path) -> bytes:
    data = json.loads((source / ".sdd/verification.json").read_text(encoding="utf-8"))
    data["checks"] = [c for c in data["checks"] if c["id"] not in GENERATOR_CHECKS]
    for profiles in data["profiles"].values():
        for name, ids in profiles.items():
            profiles[name] = [i for i in ids if i not in GENERATOR_CHECKS]
    return text(json.dumps(data, indent=2) + "\n")


RULES_MIGRATION = ("Upgrading would drop floors kept in .sdd/risk-rules.json, which this version "
                   "replaces: {}. In the same change branch and pull request as this upgrade, move these rules or "
                   "patterns into .sdd/product-risk-rules.json (same format, unique IDs); if they came from an "
                   "older framework version, delete them. Commit, then run the installer again")
RULES_COLLISION = ("This framework version ships rule IDs that .sdd/product-risk-rules.json also uses: {}. "
                   "Rename those product rules, commit, then run the installer again")


def framework_rules(source: Path) -> bytes:
    data = json.loads((source / FRAMEWORK_RULES).read_text(encoding="utf-8"))
    rules = []
    for rule in data["rules"]:
        paths = [p for p in rule["paths"] if p not in FRAMEWORK_ONLY]
        if paths:
            rules.append({**rule, "paths": paths})
    return text(json.dumps({**data, "rules": rules}, indent=2) + "\n")


def present(target: Path, path: str) -> bool:
    return (target / path).exists() or (target / path).is_symlink()


def rules_guard(target: Path, shipped_rules: bytes) -> None:
    """Refuse an upgrade that would lose a floor or create a duplicate rule ID.

    Every rule or pattern in the target's framework file must still be shipped, or be kept
    by the product file; framework-repository-only patterns are ignored.
    """
    shipped = {r["id"]: r for r in json.loads(shipped_rules)["rules"]}
    product = read_json(target, PRODUCT_RULES)["rules"] if present(target, PRODUCT_RULES) else []
    product_ids = {r["id"] for r in product}
    collisions = sorted(product_ids & set(shipped))
    if collisions:
        raise ConfigError(RULES_COLLISION.format(", ".join(collisions)))
    if not present(target, FRAMEWORK_RULES):
        return
    problems = []
    kept = {r["id"]: r for r in product}
    for rule in read_json(target, FRAMEWORK_RULES)["rules"]:
        ident = rule["id"]
        # A rule is kept by the shipped framework rule, or else by the product rule with its ID.
        keeper = shipped.get(ident) or kept.get(ident)
        if keeper is None:
            problems.append(f"rule {ident}")
            continue
        extra = sorted(set(rule["paths"]) - set(keeper["paths"]) - set(FRAMEWORK_ONLY))
        if extra:
            problems.append(f"{ident} patterns {', '.join(extra)}")
        if LEVELS[rule["minimum_level"]] > LEVELS[keeper["minimum_level"]]:
            problems.append(f"{ident} floor {rule['minimum_level']}")
    if problems:
        raise ConfigError(RULES_MIGRATION.format("; ".join(problems)))


def codeowners_example(source: Path, clients: list[str]) -> bytes:
    lines = (source / CODEOWNERS_EXAMPLE).read_text(encoding="utf-8").splitlines()
    keep = [line for line in lines if not line.split() or line.split()[0] not in CLIENT_ROWS
            or CLIENT_ROWS[line.split()[0]] in clients]
    return text("\n".join(keep) + "\n")


def describe(source: Path, dirty: bool) -> dict:
    version = git(source, "describe", "--tags", "--always").decode().strip()
    commit = git(source, "rev-parse", "HEAD").decode().strip()
    return {"framework_version": version, "framework_commit": commit, "source_dirty": dirty}


def plan(source: Path, target: Path, clients: list[str] | None, dirty: bool) -> dict:
    kind, clients, previous = mode(target, clients)
    upgrade = kind == "upgrade"
    files = set(git_list(source, "ls-files"))
    if dirty:
        files |= set(git_list(source, "ls-files", "--others", "--exclude-standard"))
    files = sorted(files)
    shipped = {p: (source / p).read_bytes() for p in selected(files, FRAMEWORK) if p not in EXCLUDED}
    for client in clients:
        shipped.update({p: (source / p).read_bytes() for p in selected(files, CLIENT_FILES[client])})
    shipped[CODEOWNERS_EXAMPLE] = codeowners_example(source, clients)
    shipped[FRAMEWORK_RULES] = framework_rules(source)
    if upgrade:
        rules_guard(target, shipped[FRAMEWORK_RULES])
        if present(target, PRODUCT_CI):
            # The product's CI settings must stay valid against the CI policy this version ships.
            merge(json.loads(shipped[".sdd/ci.json"]), read_json(target, PRODUCT_CI))
    modes = executable_paths(source)
    product = {p: (source / p).read_bytes() for p in PRODUCT}
    product[".sdd/verification.json"] = product_verification(source)
    product["README.md"] = text(README_STUB)
    actions: list[tuple[str, str]] = []
    writes: dict[str, bytes] = {}

    def blocked(path: str) -> bool:
        reason = unsafe(target, path)
        if reason:
            actions.append(("collision", f"{path} ({reason})"))
        return bool(reason)

    for path, content in sorted(shipped.items()):
        if blocked(path):
            continue
        destination = target / path
        if not destination.exists():
            actions.append(("create", path)); writes[path] = content
        elif destination.read_bytes() == content:
            actions.append(("same", path))
        elif upgrade:
            actions.append(("replace", path)); writes[path] = content
        else:
            actions.append(("collision", path))
    for path, content in sorted(product.items()):
        if blocked(path):
            continue
        if (target / path).exists():
            actions.append(("keep", path))
        else:
            actions.append(("create", path)); writes[path] = content
    if "README.md" not in writes and not unsafe(target, "README.md") and \
            not re.search(r"^## Commands\s*$", (target / "README.md").read_text(encoding="utf-8"), re.M):
        actions.append(("collision", "README.md (add a '## Commands' section for product commands, "
                                      "or start the repository without a README)"))
    for name, required in REQUIRED_LINES.items():
        if blocked(name):
            continue
        if not (target / name).exists():
            actions.append(("create", name)); writes[name] = (source / name).read_bytes()
            continue
        lines = {line.strip() for line in (target / name).read_text(encoding="utf-8").splitlines()}
        for line in required:
            if line not in lines:
                actions.append(("collision", f"{name} (missing line {line!r})"))
    if upgrade and previous is None:
        # A migrated 1.0.0 layout has no file list: entrypoints of clients not chosen are orphans.
        others = tuple(p for c in CLIENTS if c not in clients for p in CLIENT_FILES[c])
        previous = selected(git_list(target, "ls-files"), others)
    for path in sorted(set(previous or ()) - set(shipped)):
        if (target / path).exists():
            actions.append(("orphan", path))
    if not blocked(RECORD):
        meta = {"schema_version": 1, **describe(source, dirty), "clients": clients, "files": sorted(shipped)}
        writes[RECORD] = text(json.dumps(meta, indent=2) + "\n")
        actions.append(("record", RECORD))
    return {"mode": kind, "clients": clients, "actions": actions, "writes": writes,
            "executable": sorted(p for p in writes if p in modes), "source_dirty": dirty}


def write(target: Path, writes: dict[str, bytes], executable: list[str]) -> list[str]:
    written: list[str] = []
    for path, content in writes.items():
        destination = target / path
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            handle = tempfile.NamedTemporaryFile(dir=destination.parent, delete=False)
            try:
                with handle:
                    handle.write(content)
                # Temporary files are owner-only; give normal checkout permissions.
                os.chmod(handle.name, 0o755 if path in executable else 0o644)
                os.replace(handle.name, destination)
            finally:
                if Path(handle.name).exists():
                    Path(handle.name).unlink()
        except OSError as exc:
            raise WriteError(f"Writing {path} failed: {exc}", written) from exc
        written.append(path)
    return written


def run(target: Path, clients: str | None, dry_run: bool, source: Path = SOURCE,
        allow_dirty_source: bool = False) -> tuple[int, dict]:
    try:
        dirty = source_checks(source, allow_dirty_source)
        target_checks(source, target)
        result = plan(source, target, parse_clients(clients), dirty)
    except (ConfigError, OSError, UnicodeError, ValueError, KeyError, TypeError, AttributeError) as exc:
        # Malformed JSON shapes in the target are refusals, not tracebacks; nothing is written yet.
        return 2, {"status": "refused", "reason": str(exc), "actions": []}
    report = {key: result[key] for key in ("mode", "clients", "actions", "executable", "source_dirty")}
    if any(kind == "collision" for kind, _ in result["actions"]):
        return 1, {"status": "collisions", **report}
    if dry_run:
        return 0, {"status": "dry-run", **report}
    try:
        write(target, result["writes"], result["executable"])
    except WriteError as exc:
        return 2, {"status": "failed", "reason": str(exc), "written": exc.written, **report}
    return 0, {"status": "done", **report}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True, help="Root of the product repository")
    parser.add_argument("--clients", help=f"Comma-separated clients from: {', '.join(CLIENTS)}")
    parser.add_argument("--dry-run", action="store_true", help="Report the actions and refusals; write nothing")
    parser.add_argument("--allow-dirty-source", action="store_true",
                        help="Ship uncommitted and untracked framework files deliberately")
    args = parser.parse_args(argv)
    code, report = run(args.target.resolve(), args.clients, args.dry_run,
                       allow_dirty_source=args.allow_dirty_source)
    print(f"Install: {report['status']}" + (f" ({report['mode']}, clients: {', '.join(report['clients'])})" if "mode" in report else ""))
    if report.get("source_dirty"):
        print("  WARNING: shipping from a framework checkout with uncommitted or untracked files")
    if report.get("reason"):
        print(f"  {report['reason']}")
    for kind, path in report["actions"]:
        if kind != "same":
            print(f"  {kind}: {path}")
    if report["status"] == "collisions":
        print("Nothing was written. Resolve the collisions above, then run again.")
    elif report["status"] == "failed":
        print("Partially written before the failure: " + (", ".join(report["written"]) or "nothing"))
    elif report["status"] == "done" and report["executable"]:
        print("If core.fileMode is false (Windows), record the executable bit before committing:")
        print("  git add --chmod=+x -- " + " ".join(report["executable"]))
    return code


if __name__ == "__main__":
    sys.exit(main())
