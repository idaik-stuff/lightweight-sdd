"""Isolated fixtures: no product, network, credentials, or user Git configuration."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
ROOT = Path(__file__).resolve().parents[2]


def command(ident="ok", kind="framework", code="pass", **kwargs):
    return {"id": ident, "kind": kind, "argv": ["{python}", "-c", code],
            "timeout_seconds": 5, **kwargs}


def manifest(checks=None):
    checks = checks if checks is not None else [command()]
    return {"version": 1, "checks": checks,
            "profiles": {"framework": {"focused": [c["id"] for c in checks if c["kind"] == "framework"], "standard": [], "broad": []},
                         "product": {"focused": [c["id"] for c in checks if c["kind"] == "product"], "standard": [], "broad": []}}}


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sdd-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write(".gitignore", ".sdd/results/\n__pycache__/\n*.pyc\n")
        self.write("README.md", "# Fixture\n")
        self.config(manifest())
        self.rules({"version": 1, "rules": [{"id": "api", "minimum_level": "L3", "paths": ["api/**"], "reason": "External contract"}]})

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def config(self, data):
        self.write(".sdd/verification.json", json.dumps(data))

    def rules(self, data):
        self.write(".sdd/risk-rules.json", json.dumps(data))

    def git(self, *args, check=True):
        env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                   GIT_TERMINAL_PROMPT="0")
        for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
            env.pop(key, None)
        result = subprocess.run(["git", "-C", str(self.root), *args], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)
        return result.stdout.decode("utf-8", "surrogateescape").strip()

    def init_git(self):
        self.git("init", "-q")
        self.git("config", "user.name", "SDD fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "core.hooksPath", str(self.root / "disabled-hooks"))
        self.git("add", ".")
        self.git("commit", "-qm", "Fixture baseline")
        return self.git("rev-parse", "HEAD")

    def change(self, level="L2", spec_state="draft", plan_state="draft"):
        identifier = "CHG-001-fixture"
        spec = f'''# Spec: {identifier}

Status: `{spec_state}` | Level: `{level}` | Level rationale: `Intentional behavior change`.
Owner: `Fixture owner` | Scope accepted by / date: `Fixture approver / 2026-01-01`.

## Acceptance criteria

| ID | Scenario | Action | Observable outcome |
| --- | --- | --- | --- |
| AC-01 | A fixture | Run | Deterministic result |

## Acceptance and next steps

Scope acceptance: recorded in this synthetic test fixture, not an actual approval.
Related plan: [plan](plan.md).
'''
        scope = "broad" if level == "L3" else "standard"
        plan = f'''# Plan: {identifier}

Status: `{plan_state}` | Technical owner: `Fixture` | Accepted by / date: `Fixture / 2026-01-01`.
Spec: [spec](spec.md) | Verification scope: `{scope}`.

## Verification plan and traceability

| AC / risk | Check | Command | Expected result |
| --- | --- | --- | --- |
| AC-01 | Fixture check | Synthetic procedure | Deterministic result |

## Completion evidence

Verified version or diff: synthetic fixture only. Relevant environment: isolated test.

| AC / check | Result | Evidence |
| --- | --- | --- |
| AC-01 | Passed | Synthetic fixture only |
'''
        self.write(f"docs/specs/{identifier}/spec.md", spec)
        self.write(f"docs/specs/{identifier}/plan.md", plan)
        return identifier

    def replace(self, name, old, new):
        path = self.root / name
        text = path.read_text()
        self.assertIn(old, text)
        path.write_text(text.replace(old, new), encoding="utf-8")
