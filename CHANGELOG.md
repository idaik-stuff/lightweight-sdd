# Changelog

All notable changes to the Lightweight SDD framework are recorded here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/). See the
[maintenance guide](docs/manual/maintenance.md#versions) for what each version level means.

## [Unreleased]

Targets 2.0.0.

### Changed

- **Breaking:** path floors are split by owner. `.sdd/risk-rules.json` holds only the
  framework's floors and, like `.sdd/ci.json`, is framework-owned and replaced by
  upgrades; the generic product floors move unchanged to the product-owned
  `.sdd/product-risk-rules.json`, which upgrades never replace. The loader reads both and
  rejects duplicate IDs. Before upgrading, move product rules, and any patterns you added
  to framework rules, out of `.sdd/risk-rules.json` into `.sdd/product-risk-rules.json`;
  do it in the same pull request as the upgrade, so no floor is unenforced in between;
  the installer refuses an upgrade that would drop a floor or reuse a shipped rule ID.
  Upgrades also replace `.sdd/ci.json`: local edits to its scopes or framework paths are
  discarded (project governance paths are planned separately). The plan of the first
  change that creates product code maps the real paths.
- **Breaking:** adoption is through the installer only; "Use this template" is no longer a
  supported path. Product commands stay in the product README "Commands" section, and
  `AGENTS.md` points to both registries. `check-ci-setup` requires CODEOWNERS rows for
  `.claude/`, `CLAUDE.md`, `.codex/`, and `.cursor/` only when those are installed.
- The spec and plan templates mark every section as required, optional, or conditional
  for L2 and for L3. Non-applicable sections are deleted instead of filled with `N/A`;
  an L2 spec and plan aim at about one page. The spec header adds `Related changes:` and
  the AC section asks for at least one failure or boundary AC. No new gate rule.
- **Breaking:** L1 Quick is the default level. It covers fixes, refactors, adjustments,
  and small new capabilities whose behavior fits one to three clear AC. L2 Feature now
  requires a named trigger (T1 ambiguity, T2 new user-visible flow, T3 coordinated changes
  across areas, T4 more than one PR or more than about a day, T5 durable design decision), or the
  owner's request. The order is L3, L0, L2 triggers, L1. The agent declares the level in
  one line and raises it on its own; only the owner lowers L2 to L1, and L3 is never
  lowered by decision, only by evidence that the risk is absent. L0 and L3 are
  unchanged; L2 specs written under 1.0.0 stay valid.
- CI runs `standard` verification for L0 as well as L1 and L2 (`.sdd/ci.json`); local
  L0/L1 verification stays `focused`.
- **Breaking:** `scripts/check-change-level` and `scripts/verify` fail when the default
  branch has changes against the base, and when the default branch cannot be determined
  (repository-local `git config sdd.defaultBranch`, else `origin/HEAD`) or the declaration
  names no branch or disagrees with `origin/HEAD`. Move work on the default branch to
  a change branch before upgrading. Detached checkouts, such as `sdd.yml`, are unaffected;
  a custom job that checks out the default branch by name and runs these commands with
  `--base` must check out a detached commit instead.
- `AGENTS.md`, the `implement` and `verify` workflows, the handoff contract, and the PR
  template require one branch and one pull request per change at every level; the agent
  never merges. The L0/L1 change record is the PR description, kept in Git by squash merge.
- `scripts/check-docs` flags placeholders by value, not by word: an acceptance-criteria
  cell that is only `TBD`, `TODO`, `pending`, or `not run` (with optional emphasis, brackets,
  end punctuation, or dash/colon guidance), and a rationale or acceptance field that is empty
  or starts with one. Domain vocabulary such as `Changes pending` and prose outside the
  criteria table no longer fail; a cell that is only a state name such as `pending` still
  counts as a placeholder, and `_TBD_` or `not  run`, which 1.0.0 missed, now fail. The template sentences `Scope acceptance: pending` and
  `Verified version or diff: pending` are ignored when quoted in code. Result cells are
  unchanged.
- The methodology and handoff contract say what evidence rows point to: the PR's CI run,
  the `verify` JSON report with its snapshot, or a manual procedure (guidance, not a check).
- The README Quick start documents the bootstrap order and makes opening the first change
  as a pull request an explicit step.

### Added

- `scripts/verify --target auto` (requires `--base`): picks the target CI would pick, with
  the same routing rule and policy files, and records the choice in the report.
- `.sdd/product-ci.json` (product-owned, never replaced): extra `framework_paths` and
  raised `scopes` for CI; lowering a scope is rejected. CI reads it from the base.
- Guidance for running product checks on a clean CI runner: the first product check
  installs pinned dependencies, and newly registered checks first run on the next PR.
- `scripts/install`: installs or upgrades the framework in a product repository for the
  chosen clients only (`--target`, `--clients`, `--dry-run`, `--allow-dirty-source`). It
  requires a clean change branch and a clean framework checkout, refuses before writing
  on any problem (including symlinks and paths under `.git/`), never overwrites a
  differing file on a fresh install, never replaces product-owned files on upgrade but
  creates missing ones, never deletes (orphans are reported), and records
  `.sdd/install.json`. Products no longer receive the adapter generator, the other
  clients, the manual, or the framework's change history.
- **Breaking for 1.0.0 adopters:** before the first upgrade, move rules added to
  `AGENTS.md` into `docs/project-rules.md`, remove the `adapters` and `adapter-tests`
  checks and `.agents/tools/`, then run the installer with `--clients`. The adoption
  owner is now recorded in `docs/project-rules.md`.
- `docs/development/commands.md` (framework command registry) and `docs/project-rules.md`
  (project rules that upgrades never replace).
- Opt-in `scripts/hooks/pre-push` hook that refuses pushes to the default branch, classified
  as an L3 framework path.
- Optional `sdd-direct-push` workflow that flags commits reaching the default branch without
  a merged pull request.

## [1.0.0] - 2026-10-01

First public release as a GitHub template repository.

### Added

- Risk-based change classification (L0-L3) and minimum workflows in `AGENTS.md`, with
  the methodology, documentation map, and spec, plan, and ADR templates.
- Five agent workflows (investigate, spec, plan, implement, verify) and an
  independent-review contract, generated for Claude Code, Codex, Cursor, and Copilot
  VS Code from one canonical source, with a drift check and maintenance tests.
- Local automation: `scripts/verify`, `scripts/check-docs`, and
  `scripts/check-change-level`, with a JSON check registry, path-based risk floors,
  and local evidence reports.
- Optional GitHub Actions gate (`sdd-policy`, `sdd-verify`, `sdd-gate`) that evaluates
  pull requests with the base branch's policy, plus a PR template, a disabled ruleset
  template, and a CODEOWNERS example with `scripts/check-ci-setup`.
- Product and architecture placeholders for adopting projects.
- Manual: concepts, adoption, working a change, verification and CI, agents,
  practices, a worked example, a continuous-deployment recipe, and a maintenance guide.

### Known limitations

- Live behavior of each agent client is not qualified by this release; run the
  compatibility trials in your environment.
- Remote CI enforcement is not active until each repository configures CODEOWNERS and
  the ruleset and proves that bad merges are blocked.
- Four automation tests are POSIX-only and are skipped on Windows.
