# Spec: CHG-005-installer | Installer with client selection

Status: `approved` | Level: `L3` | Level rationale: changes how the framework reaches every product (the adoption contract), which files each product owns, the command registry `AGENTS.md` points to, and the CI ownership check; a wrong install or upgrade could overwrite product work or ship a product without its gates.
Owner: Idaika Iglesias | Scope accepted by / date: Idaika Iglesias, 2026-10-19 (in conversation).
Related changes: fifth of the SDD Lite 2.0 rollout; builds on [CHG-001](../CHG-001-branch-and-pr-workflow/spec.md) (branch and PR rule, bootstrap order), [CHG-003](../CHG-003-levels/spec.md), and [CHG-004](../CHG-004-templates/spec.md). CHG-006 (risk-rule split and path mapping) and CHG-007 (CI runtimes and `--target auto`) follow.

## Problem and goal

Products adopt the framework with GitHub "Use this template" or by copying files by hand. Either way a product receives all four client adapters, the adapter generator and its tests, the onboarding manual, and the framework's own change history, although it uses one or two clients and never regenerates adapters. Upgrading means merging files by hand with no rule for what the product owns.

Goal: one installer that puts exactly the framework a product needs into its repository, for the clients it chose, as a normal change on a branch, and that can later upgrade the framework-owned files without touching anything the product owns.

## Context and current behavior

Observed at `aefa291` (main after CHG-004):

- No installer exists. `README.md` Quick start and `docs/manual/02-adoption.md` describe path A ("Use this template") and path B (merge by hand); `docs/development/ci-enforcement.md` describes the CI bootstrap boundary for path B.
- `.agents/tools/sync_adapters.py` generates 20 wrapper files for exactly four clients (`claude`, `codex`, `cursor`, `copilot-vscode`) from `.agents/adapters/clients.json`, and refuses any other client set.
- `.sdd/verification.json` registers the framework checks `docs`, `adapters`, `adapter-tests`, `automation-tests`; `adapters` and `adapter-tests` need `.agents/tools/`.
- `scripts/sdd/ci_setup.py` `PROTECTED` requires CODEOWNERS rows for `/.cursor/` and `/.codex/` among others, whether or not those clients exist in the repository.
- `AGENTS.md` names the "Commands" section of `README.md` as the canonical command source; the `verify` workflow and `docs/development/automation.md` refer to it. That section mixes framework commands, product-check guidance, and generator maintenance commands.

Closed design decisions (ideation, 2026-10-19, point 2, and the CHG-005 design discussion of the same day):

1. Installer form: `scripts/install`, Python standard library, run from a framework checkout as `python3 scripts/install --target DIR --clients A,B [--dry-run]`. The target is a Git repository root on a non-default branch with a clean worktree. A fresh install (no `.sdd/` in the target) copies the framework files and empty product documents and never overwrites a differing file: it lists collisions and stops. An upgrade (target has `.sdd/`) replaces only framework-owned files and never touches product documents, specs, or configuration. It records `.sdd/install.json` with the framework version and the chosen clients.
2. Shipped files:
   - Framework-owned (copied, replaced on upgrade): `AGENTS.md` (ending with a pointer to the product-owned `docs/project-rules.md`), `.agents/workflows`, `.agents/review`, `.agents/references`, `.agents/evals`, `.agents/README.md`, the wrappers of the chosen clients only, `.github/workflows/sdd.yml`, `.github/workflows/sdd-direct-push.yml`, `.github/pull_request_template.md`, `.github/CODEOWNERS.example`, `.github/sdd-ruleset.template.json`, `scripts/` (including `hooks/` and the automation tests), `docs/development/`, `docs/templates/`, `docs/README.md`, `docs/specs/README.md`.
   - Product-owned (created only on a fresh install): `docs/product/*`, `docs/architecture/overview.md`, `docs/adr/README.md`, `docs/project-rules.md`, `.sdd/verification.json` without `adapters`/`adapter-tests`, `.sdd/ci.json`, `.sdd/risk-rules.json`.
   - Not shipped: `.agents/tools`, `.agents/adapters/clients.json`, wrappers of clients not chosen, `docs/manual/`, `docs/specs/CHG-*`, `CHANGELOG.md`, `LICENSE`.
   - `.gitignore` and `.gitattributes`: created when missing; when present, the required lines are checked and missing ones are reported as collisions.
   - The CODEOWNERS ownership check adapts to the installed clients.
3. Commands: framework commands move to the framework-owned `docs/development/commands.md`. Product commands live in the product's `README.md` "Commands" section; on a fresh install without a README the installer creates a minimal one with that section; an existing README without it is a collision. `AGENTS.md` and the workflows point to both. The framework repository's README keeps a summary and the generator maintenance commands.
4. The installer is the only adoption path, for new and existing repositories. A new repository starts with a README-only initial commit on the default branch, then a `chg-000-install-sdd` branch, the install, and a PR merged under the existing bootstrap exception; then the hook is enabled. Disabling the GitHub "template repository" flag is the owner's action. README and manual 02 describe this single path; the manual stays in the framework repository. Releasing 2.0.0 happens after CHG-007.

## Scope and non-goals

Includes:

- `scripts/install` and its implementation and tests, covering fresh install, upgrade, client selection, collisions, `--dry-run`, and refusals.
- Wrapper generation for a subset of clients, reusing the generator's logic, without shipping the generator.
- The shipped `.sdd/verification.json` for products (no adapter checks) and the client-aware CODEOWNERS check.
- `docs/development/commands.md`; the pointers in `AGENTS.md`, the `verify` workflow, `docs/development/automation.md`, and other documents that name the README command registry; `docs/project-rules.md` pointer in `AGENTS.md`.
- `README.md` Quick start, `docs/manual/02-adoption.md`, `docs/development/agent-compatibility.md` "Installation and maintenance", and `ci-enforcement.md` bootstrap wording, rewritten for the installer path.
- CHANGELOG entry.

Does not include:

- Splitting `.sdd/risk-rules.json` into framework and product parts, removing rules for paths not shipped, and the product path-mapping procedure (CHG-006). This change ships the risk rules as they are.
- CI runtimes and `--target auto` (CHG-007).
- A hash manifest of installed files (future work).
- Changing GitHub settings (the template flag) or publishing a release.
- Installing into a repository that is not a Git repository, or installing from a network source.

## Expected behavior

- Installing into a new repository on a change branch with `--clients claude` produces a repository with the framework-owned files, Claude's wrappers only, empty product documents, a minimal README with a Commands section, and `.sdd/install.json`; nothing from the not-shipped list.
- In that installed repository, the documented framework verification passes without the generator.
- Any refusal (default branch, dirty worktree, collisions, unknown client, not a repository root) happens before the first write and leaves the target unchanged.
- An upgrade leaves every product-owned file byte-for-byte unchanged, replaces framework-owned files, and keeps the recorded clients unless `--clients` changes them.
- `--dry-run` reports the same actions and refusals as a real run and writes nothing.

## Acceptance criteria

Include at least one failure or boundary AC, or state in one line why there is none.

| ID | Scenario / precondition | Action | Observable outcome |
| --- | --- | --- | --- |
| AC-01 | Target: Git root with only a README commit, on branch `chg-000-install-sdd`, clean | `scripts/install --target T --clients claude` | Exit 0; framework-owned files, Claude wrappers, product-owned stubs, and `.sdd/install.json` (version, `["claude"]`) exist; no not-shipped file and no other client's wrapper exists |
| AC-02 | Same target | `--clients codex,cursor` | Only Codex and Cursor wrappers are present; no `.claude/` or Copilot files |
| AC-03 | Freshly installed target (AC-01) | Run `python3 scripts/verify standard --target framework` and `python3 scripts/check-docs` inside it | Both pass; no `adapters` or `adapter-tests` check is registered |
| AC-04 | Target on its default branch, or with uncommitted changes | Run the installer | Refuses with a clear message; target unchanged |
| AC-05 | Target already has an `AGENTS.md` (or other shipped path) with different content, or a README without a Commands section | Fresh install | Lists every collision, exits non-zero, writes nothing |
| AC-06 | `.gitignore` exists without `.sdd/results/`, or `.gitattributes` without LF normalization | Fresh install | Reported as collisions; files not edited |
| AC-07 | Unknown client name, or `--target` not a repository root | Run the installer | Refuses before writing |
| AC-08 | Any of the cases above | Run with `--dry-run` | Same report and exit status; target unchanged |
| AC-09 | Installed target whose product files were edited (`docs/product`, `docs/project-rules.md`, README, `.sdd/verification.json` with a product check) and one framework file modified | Upgrade from a newer framework checkout without `--clients` | Product files unchanged; framework file replaced; recorded clients reused; `.sdd/install.json` version updated |
| AC-10 | Installed target with one client | Run `scripts/check-ci-setup` with a CODEOWNERS covering only the installed paths | Not blocked for missing rows of clients that are not installed; still blocked for missing rows of installed paths |
| AC-11 | Framework repository after this change | Read `AGENTS.md`, the `verify` workflow, `docs/development/commands.md`, README | Framework commands live in `commands.md`; `AGENTS.md` and workflows point to it and to the product README Commands section; README keeps a summary and the generator commands; `AGENTS.md` points to `docs/project-rules.md` |
| AC-12 | Updated README Quick start, manual 02, agent-compatibility, ci-enforcement | Read them | The installer is the only adoption path; no instruction to use "Use this template" remains; the new-repository bootstrap sequence is described |
| AC-13 | Repository at the end of this change | `scripts/check-docs`, `scripts/verify broad --target framework` | Pass |

AC-04 to AC-08 are the refusal boundaries; AC-09 is the property that the product's work is never overwritten.

## Constraints and compatibility

- Property at risk: product-owned files are never modified by an install or upgrade (AC-05, AC-09), and refusals are all-or-nothing (AC-04 to AC-08).
- The framework repository keeps its four clients, the generator, and its checks; nothing about its own verification gets weaker.
- Existing adopters on 1.0.0 have no `.sdd/install.json`; treating such a repository as an upgrade requires the clients to be given explicitly.
- Standard library only, Python 3.10+, works on Windows and Linux; no network access.

## Uncertainties

None open. The design points were closed with the owner on 2026-10-19.

## Acceptance and next steps

Scope acceptance: accepted by Idaika Iglesias on 2026-10-19 (in conversation), with AC-01 to AC-13. Next: plan with strategy.

Related plan: [plan.md](plan.md). States and completion rules: [docs/specs/README.md](../README.md).

Upon completion, record evidence and delivery status in the plan. If another change replaces this behavior, reference that change without rewriting history.
