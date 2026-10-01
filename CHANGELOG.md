# Changelog

All notable changes to the Lightweight SDD framework are recorded here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/). See the
[maintenance guide](docs/manual/maintenance.md#versions) for what each version level means.

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
