# Lightweight SDD

Framework version: `1.0.0` | License: [MIT](LICENSE)

A lightweight spec-driven development (SDD) framework for teams working with AI coding
agents. It classifies every change by risk (L0–L3), asks for a spec and plan only when
the risk warrants them, verifies with real commands, and requires an independent
review for the riskiest changes. It ships agent workflows for Claude Code, Codex,
Cursor, and Copilot VS Code, deterministic local checks, and an optional GitHub
Actions gate.

This repository is a template: create your project from it and replace the product
placeholders in `docs/product/` and `docs/architecture/` with your own.

New to the framework? Start with the [manual](docs/manual/README.md): concepts,
adoption, working a change, verification and CI, agents, practices, and a complete
worked example.

## Quick start

1. Create a repository from this template (**Use this template** on GitHub), or merge
   the framework deliberately into an existing repository. Preserve existing
   organization instructions, permissions, documents, and configurations.
2. Check that the framework is healthy:
   `python3 scripts/verify standard --target framework`.
3. Complete [the brief](docs/product/brief.md) and [the MVP scope](docs/product/mvp.md)
   first. Add only necessary cross-cutting requirements to [the PRD](docs/product/prd.md).
   Describe in [architecture](docs/architecture/overview.md) what actually exists.
   Proposed architecture belongs in the first plan and, when justified, an ADR.
4. When the stack exists, register its real checks in `.sdd/verification.json`
   (see [connecting the product](docs/development/automation.md#connecting-the-product)).
5. Optionally activate the CI gate following the
   [activation guide](docs/development/ci-enforcement.md#activation-sequence).

[AGENTS.md](AGENTS.md) contains permanent rules. [The methodology](docs/development/methodology.md)
defines gates; [the documentation index](docs/README.md) identifies each canonical source.

## Commands

Run from the repository root. Framework automation requires Python 3.10 or later and
uses only the standard library; Git is required for change checks and product verification.

This README is the human command registry. `.sdd/verification.json` is the machine
source for automated check arguments and profile membership. The template registers
no product checks: add your stack's commands to the table below and to that file.

| Operation | Command | Scope / prerequisites |
| --- | --- | --- |
| Check all framework Markdown | `python3 scripts/check-docs` | Links, anchors, and structural conventions; not semantic approval. |
| Focused framework verification | `python3 scripts/verify focused --target framework` | Documentation and generated adapters. |
| Standard framework verification | `python3 scripts/verify standard --target framework` | Focused checks plus adapter and automation tests. |
| Broad framework verification | `python3 scripts/verify broad --target framework` | Inherits standard; no extra broad framework-only checks are configured. |
| Change-level check | `python3 scripts/check-change-level --base BASE --level LEVEL` | Replace placeholders; add `--change ID` for L2/L3. |
| Product verification | `python3 scripts/verify MODE --base BASE --level LEVEL` | Add `--change ID` for L2/L3. Runs registered framework + product checks; blocked until product checks exist. |
| Check local CI ownership setup | `python3 scripts/check-ci-setup` | Exits 3 until real CODEOWNERS are configured; does not audit GitHub. |

All selected checks are required. `standard` inherits `focused`; `broad` inherits both.
Manual, contract, migration, security, or recovery evidence remains change-specific
until a real deterministic command is added.

Reports are written locally to ignored `.sdd/results/`. Keep reviewed evidence
summaries in the plan or change record; do not commit raw reports or logs by default.
Approval, independent review, and deployment are separate decisions.

### Framework maintenance commands

| Operation | Command | Scope |
| --- | --- | --- |
| Check generated adapters | `python3 .agents/tools/sync_adapters.py --check` | Detect missing or stale generated entrypoints; no writes. |
| Regenerate adapters | `python3 .agents/tools/sync_adapters.py` | Create or update the 20 owned discovery, metadata, reviewer, and bridge files. |
| Inspect adapter inventory | `python3 .agents/tools/sync_adapters.py --inventory` | Read-only JSON file consistency; never live-client certification. |
| Test adapter generator | `python3 -m unittest discover -s .agents/tools -p 'test_*.py' -v` | Isolated maintenance tests. |
| Test automation | `python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v` | Isolated CLI, configuration, Git, documentation, and runner tests. |

The command entrypoints also have executable permissions for POSIX checkouts. The
`python3 scripts/...` form avoids dependence on executable-bit preservation. Substitute
`python` only when it refers to the supported Python 3 interpreter.

## Use with agents

`AGENTS.md` is the shared policy and `CLAUDE.md` is a one-line import. Five canonical
workflow bundles live in `.agents/workflows/`; templates live in `docs/templates/`.

Generated `.agents/skills/sdd-*/` entrypoints serve Codex, Cursor, and Copilot VS Code.
The `.claude/skills/sdd-*/` entrypoints provide Claude's command interface. There are
five procedures, not ten independently maintained workflows. Some clients also scan
Claude's directory: both aliases resolve to the same source and manual policy. Resolve
user/global collisions and verify the repository entrypoint in the actual client before use.

Use `/sdd-investigate`, `/sdd-spec`, `/sdd-plan`, `/sdd-implement`, `/sdd-verify` in
Claude Code, Cursor, or Copilot VS Code local agent mode. Use the same names with `$`
in Codex CLI/IDE. Select `sdd-implement` explicitly and authorize its actual scope.
The [workflow guide](docs/development/workflows.md) shows worked invocations; the
[compatibility guide](docs/development/agent-compatibility.md) specifies discovery,
reviewer controls, supported surfaces, and the required live smoke tests.

Each client gets an adapter to the same independent-review contract. A read-only
sandbox is not a tool allowlist; Cursor/Codex reviews additionally require confirmation
that write-capable external tools are unavailable, or the gate stays blocked.

## First product session

```text
Read AGENTS.md and docs/product/brief.md.
We are defining the product, not implementing it or choosing the stack.
I will provide my vision. Separate facts, hypotheses, and pending decisions.
First, ask about gaps that prevent us from defining the problem, user, and value.
Update only docs/product/brief.md and keep it in draft until I validate it.
Do not fill the PRD, MVP, or architecture with assumptions.
```

## CI activation

The [workflow](.github/workflows/sdd.yml) reads classification and check registration
from a separate checkout of the PR base, verifies the exact test merge, and produces
one final `sdd-gate`. The [PR template](.github/pull_request_template.md) needs a level
and change ID; unknown changed paths require product checks rather than a
framework-only exemption.

Copy `.github/CODEOWNERS.example` to `.github/CODEOWNERS`, assign real owners, and
configure the supplied disabled ruleset template in GitHub. Run a controlled PR and
the negative activation scenarios before calling enforcement active. The
[activation guide](docs/development/ci-enforcement.md#activation-sequence) covers
the ordered steps, the bootstrap boundary, and what to do when your GitHub plan
cannot enforce rules.

The workflow itself must be protected by independent ownership or a separately
administered organization-required workflow. Local code cannot protect itself against
privileged administrators or forged same-name workflows.

For local CI reproduction, use two separate Git checkouts at the event base and test merge:

```bash
python3 -I /path/to/trusted/scripts/check-ci \
  --candidate-root /path/to/candidate \
  --event /path/to/pull-request-event.json \
  --expected-sha FULL_TEST_MERGE_SHA \
  --report /path/to/ci-policy-result.json
```

The expected SHA must be the full event test-merge SHA. This command inspects candidate
data; it never falls back to executing the candidate's CI policy.
`scripts/verify --policy-root /path/to/trusted` uses an external registry only when
invoked through that trusted checkout's runner.

## What is intentionally left out

No application stack, product check, deployment, user secret, or external connector
is included. Remote CI/ruleset enforcement is not activated by the template. There is
no automatic all-phases command, mandatory third feature artifact, or extra approval
system.
