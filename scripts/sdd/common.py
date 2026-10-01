"""Shared configuration, path, and Git helpers. No commands run at import time."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any


class ConfigError(ValueError):
    """Invalid configuration, input, or unavailable repository context."""


def load_json(path: Path) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ConfigError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique,
                          parse_constant=lambda value: (_ for _ in ()).throw(
                              ConfigError(f"Invalid JSON number: {value}")))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"Expected a JSON object in {path}")
    return data


def require_keys(data: dict[str, Any], required: set[str], optional: set[str] = frozenset()) -> None:
    if not isinstance(data, dict):
        raise ConfigError("Expected an object")
    missing, unknown = required - data.keys(), data.keys() - required - optional
    if missing or unknown:
        raise ConfigError(f"Invalid fields; missing={sorted(missing)}, unknown={sorted(unknown)}")


def relative_path(value: str) -> str:
    """Accept an unambiguous repository-relative POSIX path, including spaces."""
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ConfigError("Expected a nonempty repository-relative POSIX path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or ":" in value:
        raise ConfigError(f"Unsafe relative path: {value!r}")
    return path.as_posix()


def inside(root: Path, value: str) -> Path:
    candidate = root / relative_path(value)
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ConfigError(f"Path escapes repository: {value!r}") from exc
    return candidate


def git(root: Path, *args: str) -> bytes:
    """Read Git without a shell, external diff drivers, or interactive prompting."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0")
    # Do not let an inherited Git directory/index redirect reads to another repository.
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
        env.pop(key, None)
    try:
        result = subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false",
             "-C", str(root), *args],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=30, check=False, env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ConfigError(f"Git unavailable: {exc}") from exc
    if result.returncode:
        message = result.stderr.decode("utf-8", "replace").strip()
        raise ConfigError(f"Git command failed: {message}")
    return result.stdout


def git_root(root: Path) -> Path:
    actual = Path(os.fsdecode(git(root, "rev-parse", "--show-toplevel")).strip()).resolve()
    if actual != root.resolve():
        raise ConfigError("Run against the repository root, not a nested directory")
    return actual


def commit(root: Path, ref: str) -> str:
    if not ref or ref.startswith("-") or "\x00" in ref:
        raise ConfigError("Invalid base revision")
    return git(root, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()


def nul_paths(data: bytes) -> list[str]:
    return [os.fsdecode(item) for item in data.split(b"\x00") if item]


def repo_paths(root: Path) -> tuple[list[str], dict[str, Any]]:
    """Enumerate source for evidence, including staged/unstaged/untracked work."""
    if (root / ".git").exists():
        git_root(root)
        if git(root, "ls-files", "--unmerged", "-z"):
            raise ConfigError("Unresolved merge conflicts; source snapshot is blocked")
        index = git(root, "ls-files", "--stage", "-z")
        if any(record.startswith(b"160000 ") for record in index.split(b"\x00")):
            raise ConfigError("Submodule repositories need explicit verification; not supported by this runner")
        flags = git(root, "ls-files", "-v", "-z")
        if any(record and (record[:1].islower() or record.startswith(b"S "))
               for record in flags.split(b"\x00")):
            raise ConfigError("assume-unchanged / skip-worktree indexes are not supported")
        tracked = nul_paths(git(root, "ls-files", "--cached", "-z"))
        if any(p.startswith(".sdd/results/") for p in tracked):
            raise ConfigError("Verification reports must not be tracked under .sdd/results/")
        other = nul_paths(git(root, "ls-files", "--others", "--exclude-standard", "-z"))
        try:
            head = commit(root, "HEAD")
        except ConfigError:
            # A genuinely unborn branch is allowed for framework checks only.
            if git(root, "rev-list", "--all", "--max-count=1").strip():
                raise
            head = None
        meta = {"source": "git-worktree", "head": head,
                "index_sha256": hashlib.sha256(index).hexdigest()}
        return sorted(set(tracked + other) - {p for p in other if p.startswith(".sdd/results/")}), meta
    # Archive checkouts have no Git baseline. Only the delivered framework is inventoried.
    names: list[str] = []
    roots = [root / p for p in (".agents", ".claude", ".github", ".sdd", "docs", "scripts")]
    names.extend(p.name for p in root.iterdir() if p.is_file())
    for folder in roots:
        if not folder.exists():
            continue
        for current, directories, files in os.walk(folder, followlinks=False):
            directories[:] = sorted(d for d in directories
                                     if d not in {"__pycache__", ".git", ".venv", "node_modules"}
                                     and (Path(current) / d) != root / ".sdd/results")
            names.extend((Path(current) / name).relative_to(root).as_posix()
                         for name in files if not name.endswith((".pyc", ".pyo")))
    return sorted(set(names)), {"source": "archive-framework-only", "head": None,
                               "limitation": "No Git baseline; product verification is unavailable"}


def snapshot(root: Path) -> dict[str, Any]:
    names, meta = repo_paths(root)
    digest = hashlib.sha256()
    count = 0
    for name in names:
        path = root / relative_path(name)
        # Hash a symlink's target string, never the contents outside the repository.
        if path.is_symlink():
            value, mode = os.fsencode(os.readlink(path)), b"symlink"
            content_hash = hashlib.sha256(value).hexdigest()
        elif not path.exists():
            content_hash, mode = "deleted", b"missing"
        elif path.is_file():
            file_hash = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    file_hash.update(chunk)
            content_hash = file_hash.hexdigest()
            mode = b"executable" if path.stat().st_mode & 0o111 else b"file"
        else:
            raise ConfigError(f"Unsupported source entry: {name!r}")
        digest.update(os.fsencode(name) + b"\x00" + mode + b"\x00" + content_hash.encode() + b"\x00")
        count += 1
    digest.update(json.dumps(meta, sort_keys=True).encode())
    return {**meta, "sha256": digest.hexdigest(), "files": count}
