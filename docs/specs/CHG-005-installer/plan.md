# Plan: CHG-005-installer | Installer with client selection

Status: `approved` | Technical owner: Idaika Iglesias | Accepted by / date: Idaika Iglesias, 2026-10-19 (in conversation), including the three refinements (installer files not shipped, upgrade never deletes, CODEOWNERS rows from installed clients).
Spec: [spec.md](spec.md) | Verification scope: `broad`.

## System inspection

Inspected at base `aefa291` (main after CHG-004; the CHG-003/004 closeouts are merged separately):

- `.agents/tools/sync_adapters.py` `render_expected()` produces 20 files: `.claude/skills/*` and `.claude/agents/sdd-independent-review.md` (Claude); `.agents/skills/*/SKILL.md` and `.agents/skills/*/agents/openai.yaml` (shared discovery used by Codex, Cursor, and Copilot); `.codex/agents/sdd-independent-review.toml` (Codex); `.cursor/agents/sdd-independent-review.md` (Cursor); `.github/agents/sdd-independent-review.agent.md` and `.github/copilot-instructions.md` (Copilot). `CLAUDE.md` is a static file. `load_config()` requires exactly the four clients, and `synchronize(check=True)` reports drift.
- Generated files are committed and kept current by the `adapters` check, so the installer can copy them instead of regenerating.
- `scripts/sdd/ci_setup.py` `PROTECTED` is a fixed tuple including `/.cursor/`, `/.codex/`, `/.claude/`, `/CLAUDE.md`; `owners()` requires every row; `test_agent_governance.py` asserts this tuple and the shipped `CODEOWNERS.example`.
- Shipped documents link to non-shipped files in two places: `docs/README.md` (manual) and `docs/development/ci-enforcement.md` (manual recipe). `check-docs` treats external URLs as unchecked, so upstream URLs are safe in a product.
- `scripts/verify`, `scripts/check-docs`, and the other entrypoints are thin Python launchers over `scripts/sdd/*.py`; the same pattern fits `scripts/install`.
- `docs/product/*.md`, `docs/architecture/overview.md`, and `docs/adr/README.md` in this repository are already neutral starter documents (`TBD` content), usable as product stubs.
- `scripts/tests/support.py` `Fixture` creates isolated Git repositories with a disabled hooks path, suitable for target repositories in installer tests.

## Technical approach

1. `scripts/sdd/install.py` with a `scripts/install` launcher. The ownership manifest is code in that module:
   - `FRAMEWORK`: path patterns copied and replaced on upgrade (spec decision 2), plus `docs/development/commands.md`.
   - `CLIENTS`: per client, the generated paths above (`.agents/skills/**` for Codex, Cursor, and Copilot; `CLAUDE.md` with Claude).
   - `PRODUCT`: stubs created only on a fresh install: copies of the starter `docs/product/*`, `docs/architecture/overview.md`, `docs/adr/README.md`; generated `docs/project-rules.md`, minimal `README.md` with a Commands section, `.sdd/verification.json` (the framework file without `adapters` and `adapter-tests`), `.sdd/ci.json`, `.sdd/risk-rules.json` (copied as they are until CHG-006), `.github/CODEOWNERS.example` filtered to installed paths.
   - Excluded even under `scripts/`: `scripts/install`, `scripts/sdd/install.py`, `scripts/tests/test_install.py`. They need a framework checkout to work, so shipping them would give the product a command and a test that cannot pass there. This refines decision 2 ("`scripts/` complete") and needs owner acceptance.
2. Run order, all checks before any write:
   1. Source checks: run from a framework checkout whose generated adapters have no drift (`sync_adapters.synchronize(check=True)` imported from the source checkout).
   2. Target checks: `--target` is a Git repository root; current branch is not the default branch (reusing `changes.branch_guard()`); worktree clean (`git status --porcelain`); clients valid.
   3. Mode: fresh install when `.sdd/` is absent, upgrade otherwise. On upgrade without `--clients`, read clients from `.sdd/install.json`; a 1.0.0 repository without it requires `--clients`.
   4. Action list: for each framework and client file, `create`, `replace` (upgrade only, framework-owned), `same`, or `collision` (fresh install, existing differing content); product stubs `create` only when missing (fresh install) or `keep`; `.gitignore`/`.gitattributes` `create` or `collision` when required lines are missing; README without a Commands section is a collision.
   5. Any refusal or collision: print the report, exit non-zero, write nothing. `--dry-run`: print the report and exit with the same status, write nothing.
   6. Writes: each file through a temporary file and `os.replace`, LF line endings, executable bit preserved for entrypoints and the hook.
   7. `.sdd/install.json`: `schema_version`, `framework_version` (`git describe --tags --always` of the source), `framework_commit`, `clients`.
3. Upgrade never deletes. Framework files that a newer version no longer ships, and wrappers of clients dropped through `--clients`, are listed as orphans for a reviewed manual removal, like the generator's "no delete mode".
4. `scripts/sdd/ci_setup.py`: compute the protected rows from the repository: `/.claude/` and `/CLAUDE.md` only when `.claude/` exists, `/.codex/` only when `.codex/` exists, `/.cursor/` only when `.cursor/` exists; all other rows unchanged. In this repository all exist, so its result does not change.
5. Commands: create `docs/development/commands.md` from the framework rows of the README "Commands" section (operations, scopes, reports, interpreter note). README keeps a short pointer, the product-check guidance, and the generator maintenance table. `AGENTS.md` "Commands" names both sources and ends with the `docs/project-rules.md` pointer; the `verify` workflow, `docs/development/automation.md`, and manual 03 point to `commands.md`.
6. Shipped links to non-shipped files (`docs/README.md`, `ci-enforcement.md`) become upstream GitHub URLs.
7. Adoption docs: README Quick start, `docs/manual/02-adoption.md` (single installer path, new-repository bootstrap sequence, collisions), `agent-compatibility.md` "Installation and maintenance" (framework repository vs product), `ci-enforcement.md` bootstrap wording.
8. Tests:
   - `scripts/tests/test_install.py` (framework only): temporary source copy is not needed; the tests use this checkout as source and `Fixture` repositories as targets. Cases for AC-01, AC-02, AC-04 to AC-09, and an end-to-end case that runs the target's `scripts/check-docs` and `scripts/verify focused --target framework` (AC-03).
   - `test_agent_governance.py`: CODEOWNERS tests updated for computed rows (AC-10), and client-specific assertions skipped when that client's files are not in the repository, so the suite also passes inside an installed product.
9. CHANGELOG entry.

Rejected alternatives:

- Regenerating wrappers in the target with the generator: it would ship or import generator code into the product and requires all four clients; copying verified generated files is smaller.
- A separate manifest file for ownership: one more framework file to keep consistent; the manifest as code is tested directly.
- Rewriting links during install: hidden transformation of shipped files; upstream URLs are explicit.

## Affected components and contracts

| Area / path | Proposed change | Impact / consumer |
| --- | --- | --- |
| `scripts/install`, `scripts/sdd/install.py` (new) | Installer and ownership manifest | Adopters; framework repository only |
| `scripts/sdd/ci_setup.py` | Protected rows computed from installed clients | `check-ci-setup` and `sdd.yml` in products and here |
| `docs/development/commands.md` (new), `README.md`, `AGENTS.md`, `verify` workflow, `automation.md`, manual 03 | Command registry split | Every client and reader |
| `docs/README.md`, `ci-enforcement.md`, `agent-compatibility.md`, manual 02 | Upstream links; installer path | Readers in products and here |
| `scripts/tests/test_install.py` (new), `test_agent_governance.py` | Installer tests; client-aware governance tests | Framework tests; product tests |
| `CHANGELOG.md` | Entry | Adopters |

## Risk-proportionate strategy

| Area | Decision, check, or reason it is not affected |
| --- | --- |
| Compatibility and consumers | 1.0.0 adopters keep working; upgrading them requires explicit `--clients`. This repository keeps four clients, the generator, and all checks; `ci_setup` output unchanged here. |
| Data, integrity, and migration | Product files are the data at risk: fresh install never overwrites differing files, upgrade never touches product-owned paths, nothing is deleted (AC-05, AC-09). |
| Permissions, security, and privacy | No network, no credentials, no shell; Git is read through the existing safe helper; writes stay inside `--target` (path checks reuse `common.inside`); symlinks in target paths are refused. |
| Failures, load, and availability | All refusals happen before the first write; each file is replaced atomically; a crash mid-write leaves completed files and no partial file; the report lists what was written so a rerun is idempotent (`same`). |
| Change observability | Every run prints the action list; `.sdd/install.json` records version, commit, and clients; the install is reviewed as a PR in the product. |
| Rollout and feasible recovery | Ships with 2.0.0 through this PR. In a product, recovery is reverting the install PR. Here, revert the squash commit. |

## Implementation steps

1. Commands split and pointers (AC-11); upstream links.
2. `ci_setup` computed rows and governance tests (AC-10).
3. Installer module and launcher with fresh install, client selection, refusals, dry run (AC-01, AC-02, AC-04 to AC-08).
4. Upgrade mode and orphan report (AC-09); end-to-end test (AC-03).
5. Adoption docs (AC-12) and CHANGELOG.
6. Broad verification (AC-13), manual installed-target run, independent review.

## Verification plan and traceability

Environment: Windows 11 with Python 3; Linux via WSL Ubuntu (native ext4 copy) for the full suites and an installed-target run.

| AC / risk | Test, check, or manual procedure | Command / location / environment | Expected result |
| --- | --- | --- | --- |
| AC-01, AC-02 | Fresh install into a fixture repository with one and with two clients | `scripts/tests/test_install.py` | Expected file set; no excluded or other-client files; `install.json` content |
| AC-03 | End-to-end: target's `check-docs` and `verify focused --target framework`; manual: target's `verify standard --target framework` on Windows and Linux | `test_install.py`; manual run recorded here | Pass; no adapter checks registered |
| AC-04, AC-07 | Default branch, dirty worktree, unknown client, non-root target | `test_install.py` | Refusal, target unchanged (snapshot compared) |
| AC-05, AC-06 | Differing `AGENTS.md`, README without Commands, incomplete `.gitignore`/`.gitattributes` | `test_install.py` | All collisions listed, nothing written |
| AC-08 | Each refusal and a clean case with `--dry-run` | `test_install.py` | Same report and exit, nothing written |
| AC-09 | Install, edit product files and one framework file, commit, upgrade without `--clients` | `test_install.py` | Product files byte-identical; framework file replaced; clients reused; orphan report when a client is dropped |
| AC-10 | CODEOWNERS with only installed rows, with and without a missing installed row | `test_agent_governance.py` / `test_install.py` | Not blocked / blocked |
| AC-11, AC-12 | Inspection | Diff review and independent review | As specified |
| AC-13 | Full framework verification | `python3 scripts/check-docs`; `python3 scripts/verify broad --target framework --base main --level L3 --change CHG-005-installer` | Passed |
| Level floor | Change-level check | `python3 scripts/check-change-level --base main --level L3 --change CHG-005-installer --scope broad` | Passed |
| L3 review | Independent review in a fresh session | `sdd-independent-review` agent with `.agents/review/independent-review.md` | Findings recorded and resolved |

## Affected documentation

`AGENTS.md`, `README.md`, `docs/development/commands.md` (new), `automation.md`, `agent-compatibility.md`, `ci-enforcement.md`, `docs/README.md`, `.agents/workflows/verify/SKILL.md`, `docs/manual/02-adoption.md`, `03-working-a-change.md`, `CHANGELOG.md`.

## Deviations and decisions during execution

None recorded yet.

## Completion evidence

Verified version or diff: pending. Relevant environment: pending.

| AC / check | Result | Evidence summary / reference |
| --- | --- | --- |
| AC-01 to AC-13 | Not run | Pending implementation. |

Independent review: pending; required for L3.

Outstanding items / exceptions: `sdd-gate` is skipped in this repository by design; the installer is exercised only against local fixture repositories, not a real adopter.

Delivery: not merged; not released.
