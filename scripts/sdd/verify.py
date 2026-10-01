"""Run required, configured checks and emit bounded, honest verification evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import sys
import time
import uuid
from typing import Any

from .changes import LEVELS, assess, load_rules
from .common import ConfigError, inside, load_json, require_keys, snapshot

MODES = ("focused", "standard", "broad")
EXIT = {"passed": 0, "failed": 1, "error": 2, "blocked": 3, "not_run": 3, "interrupted": 130}


def configuration(root: Path, execution_root: Path | None = None) -> dict[str, Any]:
    data = load_json(inside(root, ".sdd/verification.json"))
    require_keys(data, {"version", "checks", "profiles"})
    if type(data["version"]) is not int or data["version"] != 1 or not isinstance(data["checks"], list):
        raise ConfigError("Unsupported verification configuration")
    ids: dict[str, dict] = {}
    for item in data["checks"]:
        require_keys(item, {"id", "kind", "argv", "timeout_seconds"}, {"cwd", "requires_env"})
        ident = item["id"]
        if not isinstance(ident, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", ident) or ident in ids:
            raise ConfigError("Check IDs must be unique lowercase names")
        if not isinstance(item["kind"], str) or item["kind"] not in {"framework", "product"}:
            raise ConfigError(f"{ident}: kind must be framework or product")
        if not isinstance(item["argv"], list) or not item["argv"] or not all(
            isinstance(arg, str) and arg and "\x00" not in arg for arg in item["argv"]
        ):
            raise ConfigError(f"{ident}: argv must be a nonempty array of nonempty strings, not a shell command")
        timeout = item["timeout_seconds"]
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or not 0 < timeout <= 86400:
            raise ConfigError(f"{ident}: timeout_seconds must be finite and between 0 and 86400")
        cwd = inside(execution_root or root, item.get("cwd", "."))
        if not cwd.is_dir():
            raise ConfigError(f"{ident}: cwd does not exist")
        env = item.get("requires_env", [])
        if not isinstance(env, list) or not all(isinstance(name, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) for name in env):
            raise ConfigError(f"{ident}: requires_env must be an array of environment-variable names")
        ids[ident] = item
    require_keys(data["profiles"], {"framework", "product"})
    for kind, profiles in data["profiles"].items():
        require_keys(profiles, set(MODES))
        used: set[str] = set()
        for mode in MODES:
            group = profiles[mode]
            if not isinstance(group, list) or not all(isinstance(ident, str) for ident in group):
                raise ConfigError(f"{kind}.{mode}: expected an array of check IDs")
            for ident in group:
                if ident not in ids or ids[ident]["kind"] != kind:
                    raise ConfigError(f"{kind}.{mode}: unknown check or wrong kind: {ident}")
                if ident in used:
                    raise ConfigError(f"{kind}.{mode}: duplicate check; modes already inherit earlier checks")
                used.add(ident)
    load_rules(root)
    return data


def select(data: dict, target: str, mode: str) -> list[dict]:
    if target not in {"framework", "product"} or mode not in MODES:
        raise ConfigError("Unknown verification target or mode")
    by_id = {item["id"]: item for item in data["checks"]}
    ids: list[str] = []
    for kind in (["framework"] if target == "framework" else ["framework", "product"]):
        for current in MODES[:MODES.index(mode) + 1]:
            ids.extend(data["profiles"][kind][current])
    return [by_id[ident] for ident in ids]


def stop_process(process: subprocess.Popen) -> None:
    """Bound cleanup on timeout/interrupt; POSIX children share a new process group."""
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
    except ProcessLookupError:
        pass
    process.wait(timeout=5)


def execute(root: Path, check: dict) -> dict:
    argv = [sys.executable if value == "{python}" else value for value in check["argv"]]
    result = {"id": check["id"], "kind": check["kind"], "argv": argv,
              "cwd": check.get("cwd", "."), "timeout_seconds": check["timeout_seconds"],
              "status": "not_run", "exit_code": None, "duration_seconds": 0.0}
    missing = [name for name in check.get("requires_env", []) if not os.environ.get(name)]
    if missing:
        return {**result, "status": "blocked", "reason": "Missing environment variables: " + ", ".join(missing)}
    # This is not a sandbox. Commands and executables must be reviewed before execution.
    if os.name == "nt" and Path(argv[0]).suffix.lower() in {".cmd", ".bat"}:
        return {**result, "status": "blocked", "reason": "Windows batch commands need an explicitly reviewed platform adapter"}
    start = time.monotonic()
    process = None
    try:
        process = subprocess.Popen(
            argv, cwd=inside(root, check.get("cwd", ".")), shell=False,
            stdin=subprocess.DEVNULL, start_new_session=(os.name == "posix"),
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        )
        process.wait(timeout=check["timeout_seconds"])
        result.update(status="passed" if process.returncode == 0 else "failed", exit_code=process.returncode)
    except subprocess.TimeoutExpired:
        if process is not None:
            stop_process(process)
        result.update(status="blocked", reason="Timed out; no successful result was established")
    except OSError as exc:
        result.update(status="blocked", reason=f"Command unavailable or could not start: {exc}")
    except KeyboardInterrupt:
        if process is not None:
            stop_process(process)
        result.update(status="interrupted", reason="Interrupted by operator")
    result["duration_seconds"] = round(time.monotonic() - start, 3)
    return result


def aggregate(checks: list[dict], reasons: list[str]) -> str:
    statuses = {item["status"] for item in checks}
    if "interrupted" in statuses:
        return "interrupted"
    if "failed" in statuses:
        return "failed"
    if reasons or "blocked" in statuses or not checks:
        return "blocked"
    if "not_run" in statuses:
        return "not_run"
    return "passed"


def result_directory(root: Path) -> Path:
    if not root.is_dir() or not (root / ".sdd").is_dir():
        raise ConfigError("Results require an existing repository with a .sdd directory")
    folder = inside(root, ".sdd/results")
    if folder.is_symlink() or (root / ".sdd").is_symlink():
        raise ConfigError("Refusing a symlinked results directory")
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def save_report(root: Path, report: dict) -> Path:
    folder = result_directory(root)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = folder / f"verify-{timestamp}-{uuid.uuid4().hex[:8]}.json"
    # Exclusive creation never overwrites old evidence or a chosen source path.
    with path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=True)
        stream.write("\n")
    return path


def run(root: Path, mode: str, target: str, base: str | None = None,
        level: str | None = None, change: str | None = None, dry_run: bool = False,
        policy_root: Path | None = None) -> dict:
    report: dict[str, Any] = {
        "schema_version": 1, "started_at": datetime.now(timezone.utc).isoformat(),
        "target": target, "mode": mode, "status": "blocked", "checks": [], "reasons": [],
        "environment": {"python": platform.python_version(), "platform": platform.system()},
        "change_gate": None, "source_before": None, "source_after": None,
        "readiness": "not-assessed", "independent_review": "not-assessed", "deployment": "not-assessed",
        "limitations": ["Only configured automated checks are executed; assess AC and risk coverage separately",
                        "No approval, independent review, deployment, or release decision is established",
                        "Evidence excludes ignored files and external dependencies; source hashing is not an atomic snapshot",
                        "Commands inherit the local environment and are not sandboxed; no raw output or environment values are stored"]}
    try:
        data = configuration(policy_root or root, execution_root=root)
        report["policy_source"] = snapshot(policy_root or root)
        selected = select(data, target, mode)
        # Check output safety before executing any configured process.
        result_directory(root)
        report["source_before"] = snapshot(root)
        if target == "product" and not any(item["kind"] == "product" for item in selected):
            report["reasons"].append("No product checks configured for this scope; framework checks cannot substitute")
        if not selected:
            report["reasons"].append("No checks selected")
        needs_gate = target == "product" or any(value is not None for value in (base, level, change))
        if needs_gate:
            if not base or not level:
                report["reasons"].append("Change verification requires both --base and --level; add --change for L2/L3")
            else:
                gate = assess(root, base, level, change, mode, policy_root=policy_root)
                report["change_gate"] = gate
                if gate["status"] != "passed":
                    report["reasons"].extend(gate["errors"] or [gate["reason"]])
        if report["change_gate"] and report["change_gate"]["status"] == "failed":
            report["status"] = "failed"
        if report["reasons"] or dry_run:
            report["checks"] = [{"id": item["id"], "kind": item["kind"], "argv": item["argv"],
                                  "status": "not_run", "reason": "Preflight blocked or dry run"} for item in selected]
            if not report["reasons"]:
                report["status"] = "not_run"
                report["reasons"].append("Dry run: no checks were executed")
        else:
            for item in selected:
                print(f"\n[{target}/{mode}] {item['id']}", flush=True)
                outcome = execute(root, item)
                report["checks"].append(outcome)
                print(f"{item['id']}: {outcome['status']}", flush=True)
                if outcome["status"] == "interrupted":
                    remaining = selected[len(report["checks"]):]
                    report["checks"].extend({"id": next_item["id"], "kind": next_item["kind"],
                                             "status": "not_run", "reason": "Run interrupted"} for next_item in remaining)
                    break
            report["source_after"] = snapshot(root)
            if policy_root and snapshot(policy_root) != report["policy_source"]:
                report["reasons"].append("Trusted policy changed during verification; rerun with an immutable policy checkout")
            if report["source_after"] != report["source_before"]:
                report["reasons"].append("Source or index changed during verification; rerun against the final snapshot")
            report["status"] = aggregate(report["checks"], report["reasons"])
    except (ConfigError, OSError, UnicodeError, subprocess.SubprocessError) as exc:
        report["reasons"].append(str(exc))
        # Never hide an observed check failure behind a later evidence error.
        report["status"] = "failed" if any(c["status"] == "failed" for c in report["checks"]) else "error"
    except KeyboardInterrupt:
        report["status"] = "interrupted"
        report["reasons"].append("Interrupted during preflight or snapshot; no complete evidence")
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    return report


def main(argv: list[str] | None = None, default_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=MODES)
    parser.add_argument("--target", choices=("framework", "product"), default="product",
                        help="Default: product. Framework-only success does not verify the product")
    parser.add_argument("--root", type=Path, default=default_root or Path.cwd())
    parser.add_argument("--policy-root", type=Path, help="Read risk rules and check registration from a separate trusted checkout")
    parser.add_argument("--base", help="Explicit commit/revision compared with the current working snapshot")
    parser.add_argument("--level", choices=LEVELS)
    parser.add_argument("--change", help="Change directory ID for L2/L3")
    parser.add_argument("--dry-run", action="store_true", help="Validate and show selection, execute nothing; exits 3")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.policy_root and args.policy_root.resolve() != Path(__file__).resolve().parents[2]:
        parser.error("--policy-root must contain the executing runner; invoke the trusted checkout script")
    report = run(root, args.mode, args.target, args.base, args.level, args.change, args.dry_run,
                 args.policy_root.resolve() if args.policy_root else None)
    try:
        path = save_report(root, report)
    except (ConfigError, OSError) as exc:
        report["reasons"].append(f"Cannot save evidence: {exc}")
        if report["status"] == "passed":
            report["status"] = "error"
        path = None
    print(f"\nVerification: {report['status']} | target={args.target} | scope={args.mode}")
    for reason in report["reasons"]:
        print(f"  {reason}")
    for check in report["checks"]:
        if check.get("reason"):
            print(f"  {check['id']}: {check['status']} - {check['reason']}")
    if path:
        print(f"Evidence: {path.relative_to(root).as_posix()}")
    else:
        print(json.dumps(report, indent=2))
    print("This result does not establish approval, independent review, or deployment.")
    return EXIT[report["status"]]
