"""Check the repository's deliberately small Markdown and change-record contract."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

from .common import ConfigError, inside, relative_path

SPEC_STATES = {"draft", "approved", "implemented", "superseded", "cancelled"}
PLAN_STATES = {"draft", "approved", "in-progress", "completed", "cancelled"}
PENDING = re.compile(r"\b(TBD|TODO|pending|not run)\b", re.I)
FIELD = lambda name: re.compile(r"(?:^|\|)\s*" + re.escape(name) + r":\s*`?([^`|\n]+)", re.M)


def prose(text: str) -> str:
    """Remove fenced code and inline code, retaining lines for error locations."""
    out: list[str] = []
    fence: tuple[str, int] | None = None
    for line in text.splitlines():
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = (token[0], len(token))
                out.append("")
                continue
            if token[0] == fence[0] and len(token) >= fence[1]:
                fence = None
                out.append("")
                continue
        out.append("" if fence else re.sub(r"(`+).*?\1", "", line))
    return "\n".join(out)


def anchors(text: str) -> set[str]:
    """GitHub-style ATX headings for the simple subset used by this framework."""
    result: set[str] = set()
    # Keep inline-code heading words; only remove fences.
    fence: tuple[str, int] | None = None
    for line in text.splitlines():
        mark = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if mark:
            token = mark.group(1)
            if fence is None:
                fence = (token[0], len(token))
            elif token[0] == fence[0] and len(token) >= fence[1]:
                fence = None
            continue
        if fence:
            continue
        heading = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if heading:
            value = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", heading.group(1))
            slug = re.sub(r"[^\w\- ]", "", value.lower()).replace(" ", "-")
            candidate, suffix = slug, 0
            while candidate in result:
                suffix += 1
                candidate = f"{slug}-{suffix}"
            result.add(candidate)
        for ident in re.findall(r'<(?:a|span|h[1-6])\b[^>]*\b(?:id|name)=["\']([^"\']+)', line, re.I):
            result.add(ident)
    return result


def destinations(text: str) -> list[tuple[int, str]]:
    """Inline links/images and reference definitions, not a general Markdown parser."""
    result: list[tuple[int, str]] = []
    for number, line in enumerate(prose(text).splitlines(), 1):
        # Destinations may be angle-bracketed or unquoted without whitespace/parentheses.
        for match in re.finditer(r"!?\[[^]\n]*\]\(\s*(?:<([^>]+)>|([^\s()]+))(?:\s+[\"'][^\n]*?[\"'])?\s*\)", line):
            result.append((number, match.group(1) or match.group(2)))
        definition = re.match(r"^\s{0,3}\[[^]]+\]:\s*(?:<([^>]+)>|(\S+))", line)
        if definition:
            result.append((number, definition.group(1) or definition.group(2)))
    return result


def read_markdown(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ConfigError(f"Cannot read Markdown {path}: {exc}") from exc


def section(text: str, heading: str) -> str:
    match = re.search(r"^## " + re.escape(heading) + r"\s*$", text, re.M)
    if not match:
        return ""
    end = re.search(r"^## ", text[match.end():], re.M)
    return text[match.end():match.end() + end.start()] if end else text[match.end():]


def field(text: str, name: str) -> str | None:
    match = FIELD(name).search(text)
    return match.group(1).strip().rstrip(".") if match else None


def change_id(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value) or value in {".", ".."}:
        raise ConfigError("Change ID must be a single safe directory name")
    return value


def validate_change(root: Path, identifier: str, require_pair: bool = False) -> list[str]:
    """Check structural facts only; never infer approval or semantic coverage."""
    change_id(identifier)
    errors: list[str] = []
    texts: dict[str, str] = {}
    for filename, states in (("spec.md", SPEC_STATES), ("plan.md", PLAN_STATES)):
        path = inside(root, f"docs/specs/{identifier}/{filename}")
        if not path.is_file():
            if filename == "spec.md":
                errors.append(f"{identifier}: missing {filename}")
            continue
        text = read_markdown(path)
        texts[filename] = text
        state = field(text, "Status")
        if state not in states:
            errors.append(f"{identifier}/{filename}: invalid or missing Status")
    spec, plan = texts.get("spec.md"), texts.get("plan.md")
    if spec is None:
        return errors
    if plan is None and (require_pair or field(spec, "Status") == "implemented"):
        errors.append(f"{identifier}: missing plan.md")
    level = field(spec, "Level")
    state, plan_state = field(spec, "Status"), field(plan, "Status") if plan else None
    if level not in {"L2", "L3"}:
        errors.append(f"{identifier}/spec.md: recorded changes need Level L2 or L3")
    rationale = field(spec, "Level rationale")
    if not rationale or PENDING.search(rationale):
        errors.append(f"{identifier}/spec.md: provide a concrete Level rationale")
    ac_section = section(spec, "Acceptance criteria")
    ids = re.findall(r"^\s*\|\s*(AC-\d+)\s*\|", ac_section, re.M)
    if not ids:
        errors.append(f"{identifier}/spec.md: Acceptance criteria needs at least one AC-NN table row")
    if len(set(ids)) != len(ids):
        errors.append(f"{identifier}/spec.md: duplicate acceptance-criterion IDs")
    if state in {"approved", "implemented"}:
        acceptance = field(spec, "Scope accepted by / date")
        if not acceptance or PENDING.search(acceptance):
            errors.append(f"{identifier}/spec.md: accepted state has no recorded scope acceptance")
        if PENDING.search(ac_section):
            errors.append(f"{identifier}/spec.md: accepted criteria contain pending placeholders")
        if re.search(r"Scope acceptance:\s*pending", spec, re.I):
            errors.append(f"{identifier}/spec.md: acceptance statement is still pending")
    if plan is None:
        return errors
    verified_plan = section(plan, "Verification plan and traceability")
    if not verified_plan:
        errors.append(f"{identifier}/plan.md: missing Verification plan and traceability section")
    if plan_state in {"approved", "in-progress", "completed"}:
        acceptance = field(plan, "Accepted by / date")
        if not acceptance or PENDING.search(acceptance):
            errors.append(f"{identifier}/plan.md: accepted state has no recorded technical acceptance")
        for ident in ids:
            if not re.search(r"\b" + re.escape(ident) + r"\b", verified_plan):
                errors.append(f"{identifier}/plan.md: no verification mapping for {ident}")
        if not field(plan, "Verification scope") in {"focused", "standard", "broad"}:
            errors.append(f"{identifier}/plan.md: invalid Verification scope")
        if level == "L3" and field(plan, "Verification scope") != "broad":
            errors.append(f"{identifier}/plan.md: L3 requires broad scope")
        if level == "L2" and field(plan, "Verification scope") == "focused":
            errors.append(f"{identifier}/plan.md: L2 requires at least standard scope")
    if state == "implemented" and plan_state != "completed":
        errors.append(f"{identifier}: implemented spec requires completed plan")
    if plan_state == "completed":
        evidence = section(plan, "Completion evidence")
        if not evidence or re.search(r"Verified version or diff:\s*pending", evidence, re.I):
            errors.append(f"{identifier}/plan.md: completed state needs a version/diff in Completion evidence")
        for ident in ids:
            if not re.search(r"\b" + re.escape(ident) + r"\b", evidence):
                errors.append(f"{identifier}/plan.md: no completion evidence row/reference for {ident}")
        if re.search(r"^\s*\|[^\n]*\|\s*(?:not run|blocked|failed|pending)\s*\|", evidence, re.I | re.M):
            errors.append(f"{identifier}/plan.md: completion table contains an unresolved result")
    return errors


def check_docs(root: Path, requested: list[str] | None = None, change: str | None = None) -> dict:
    files: list[Path] = []
    if requested:
        for name in requested:
            path = inside(root, name)
            if path.suffix.lower() != ".md" or not path.is_file():
                raise ConfigError(f"Expected an existing Markdown file: {name}")
            files.append(path)
    else:
        files.extend(sorted(root.glob("*.md")))
        for name in ("docs", ".agents", ".claude", ".github", ".cursor", ".codex"):
            files.extend(sorted((root / name).rglob("*.md")))
    files = sorted(set(files))
    if not files:
        raise ConfigError("No Markdown documents selected")
    errors: list[str] = []
    links = 0
    cache: dict[Path, str] = {}
    for path in files:
        relative = path.relative_to(root).as_posix()
        inside(root, relative)
        text = read_markdown(path)
        cache[path.resolve()] = text
        for line, destination in destinations(text):
            try:
                parsed = urlsplit(destination)
            except ValueError:
                errors.append(f"{relative}:{line}: invalid link destination {destination!r}")
                continue
            if parsed.scheme or parsed.netloc:
                continue
            links += 1
            url_path = unquote(parsed.path)
            target = (root / url_path.lstrip("/")) if url_path.startswith("/") else path.parent / url_path
            if not url_path:
                target = path
            try:
                resolved = target.resolve()
                resolved.relative_to(root.resolve())
            except ValueError:
                errors.append(f"{relative}:{line}: link escapes repository: {destination}")
                continue
            if not target.exists():
                errors.append(f"{relative}:{line}: missing link target: {destination}")
            elif parsed.fragment and target.suffix.lower() == ".md":
                if resolved not in cache:
                    cache[resolved] = read_markdown(target)
                if unquote(parsed.fragment) not in anchors(cache[resolved]):
                    errors.append(f"{relative}:{line}: missing heading/anchor: {destination}")
    identifiers: set[str] = set()
    if change:
        identifiers.add(change_id(change))
    elif not requested:
        folder = root / "docs/specs"
        if folder.exists():
            identifiers.update(p.name for p in folder.iterdir() if p.is_dir() and not p.name.startswith("."))
    else:
        for path in files:
            parts = path.relative_to(root).parts
            if len(parts) == 4 and parts[:2] == ("docs", "specs") and path.name in {"spec.md", "plan.md"}:
                identifiers.add(parts[2])
    for identifier in sorted(identifiers):
        errors.extend(validate_change(root, identifier))
    return {"status": "failed" if errors else "passed", "files_checked": len(files),
            "local_links_checked": links, "change_records_checked": len(identifiers),
            "errors": errors, "scope": "structural-only",
            "limitations": ["Simple Markdown subset; external URLs and bare code-formatted paths are not checked",
                            "Recorded approvals, semantic correctness, AC satisfaction, and review are not authenticated"]}


def main(argv: list[str] | None = None, default_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Optional repository-relative Markdown paths")
    parser.add_argument("--root", type=Path, default=default_root or Path.cwd())
    parser.add_argument("--change", help="Also check the paired spec/plan for this change")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable structural report")
    args = parser.parse_args(argv)
    try:
        report = check_docs(args.root.resolve(), args.paths, args.change)
    except (ConfigError, OSError) as exc:
        report = {"status": "error", "errors": [str(exc)]}
        code = 2
    else:
        code = 1 if report["errors"] else 0
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Documentation: {report['status']} (structural checks only)")
        if "files_checked" in report:
            print(f"{report['files_checked']} Markdown files; {report['local_links_checked']} local links; "
                  f"{report['change_records_checked']} change records")
        for error in report["errors"]:
            print(f"  {error}")
    return code
