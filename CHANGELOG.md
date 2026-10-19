# Changelog

All notable changes to the Lightweight SDD framework are recorded here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/). See the
[maintenance guide](docs/manual/maintenance.md#versions) for what each version level means.

## [Unreleased]

Targets 2.0.0.

### Changed

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
