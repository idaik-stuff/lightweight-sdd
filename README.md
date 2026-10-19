# Lightweight SDD

Framework version: `2.0.0` | License: [MIT](LICENSE)

A lightweight spec-driven development (SDD) framework for teams working with AI coding
agents. It classifies every change by risk (L0–L3), asks for a spec and plan only when
the risk warrants them, verifies with real commands, and requires an independent
review for the riskiest changes. It ships agent workflows for Claude Code, Codex,
Cursor, and Copilot VS Code, deterministic local checks, and an optional GitHub
Actions gate.

Products adopt it with the installer below rather than by copying this repository: this
repository also holds the adapter generator, the manual, and its own change history,
which products do not need.

New to the framework? Start with the [manual](docs/manual/README.md): concepts,
adoption, working a change, verification and CI, agents, practices, and a complete
worked example.

## Quick start

Install the framework into your product repository with the installer; it ships only
what a product needs, for the agent clients you choose. Requirements: Git and Python 3.10+.

1. Prepare the product repository.
   - **New repository:** create it without a README (for example with only GitHub's
     `.gitignore` or license), or with a README that already has a `## Commands`
     section. That initial commit is the only one on the default branch.
   - **Existing repository:** nothing to prepare; the installer stops and lists any file
     it would have to overwrite, and you resolve each collision by hand.
2. Clone it, create a change branch (for example `chg-000-install-sdd`), and keep the
   worktree clean.
3. From a checkout of this repository, preview and then run the installer:
   `python3 scripts/install --target PATH --clients claude --dry-run`, then without
   `--dry-run`. Clients: `claude`, `codex`, `cursor`, `copilot-vscode` (comma-separated).
   On Windows, run the `git add --chmod=+x` command the installer prints.
4. In the product, check the framework: `python3 scripts/verify standard --target framework`.
   Commit, push, and open the install as a pull request. Its CI gate cannot pass, because
   the base has no framework yet; merge it under the
   [bootstrap exception](docs/development/ci-enforcement.md#3-establish-the-initial-trusted-version).
5. Once per clone, enable the guard that refuses pushes to the default branch:
   `git config core.hooksPath scripts/hooks`. The hook and the checks read the default
   branch from this repository's `git config sdd.defaultBranch <name>`, else from
   `origin/HEAD` (set it with `git remote set-head origin --auto`). They fail instead of
   passing when neither exists, or when the declared branch does not exist or disagrees
   with `origin/HEAD`. Every change, at every level, goes on its own branch and through
   a pull request; in GitHub, allow squash merging only, with the default message
   "Pull request title and description", and delete head branches automatically.
6. Activate the CI gate following the
   [activation guide](docs/development/ci-enforcement.md#activation-sequence), and open
   your next change as a pull request to see `sdd-gate` run.
7. Complete the brief and MVP scope in `docs/product/` first, describe in
   `docs/architecture/` what actually exists, and register the stack's real checks in
   `.sdd/verification.json` and the README "Commands" section when the stack exists.

To upgrade later, run the installer again from a newer framework checkout on a change
branch; it replaces only framework-owned files and keeps the recorded clients. Review
that pull request as L3.

[AGENTS.md](AGENTS.md) contains permanent rules. [The methodology](docs/development/methodology.md)
defines gates; [the documentation index](docs/README.md) identifies each canonical source.

## Commands

Framework commands are listed in [docs/development/commands.md](docs/development/commands.md):
documentation checks, framework and product verification, the change-level check, the
CI ownership check, the automation tests, and the pre-push hook.

Product commands belong in this section of a product's own README, next to the checks
registered in `.sdd/verification.json`. This framework repository has no product, so it
registers none.

### Framework maintenance commands

These exist only in this repository; the installer does not ship them.

| Operation | Command | Scope |
| --- | --- | --- |
| Check generated adapters | `python3 .agents/tools/sync_adapters.py --check` | Detect missing or stale generated entrypoints; no writes. |
| Regenerate adapters | `python3 .agents/tools/sync_adapters.py` | Create or update the 20 owned discovery, metadata, reviewer, and bridge files. |
| Inspect adapter inventory | `python3 .agents/tools/sync_adapters.py --inventory` | Read-only JSON file consistency; never live-client certification. |
| Test adapter generator | `python3 -m unittest discover -s .agents/tools -p 'test_*.py' -v` | Isolated maintenance tests. |
| Install or upgrade the framework in a product | `python3 scripts/install --target DIR --clients CLIENTS [--dry-run]` | Run from this checkout; the target must be on a clean change branch. See [adoption](docs/manual/02-adoption.md). |

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
is included. Remote CI/ruleset enforcement is not activated by the installer. There is
no automatic all-phases command, mandatory third feature artifact, or extra approval
system.
