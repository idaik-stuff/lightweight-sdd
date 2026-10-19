# Plan: CHG-005-installer | Installer with client selection

Status: `in-progress` | Technical owner: Idaika Iglesias | Accepted by / date: Idaika Iglesias, 2026-10-19 (in conversation), including the three refinements (installer files not shipped, upgrade never deletes, CODEOWNERS rows from installed clients).
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

Steps 1 to 3 describe the design accepted before review; the Deviations section records the round-1 refinements that supersede them (upgrade detection, migration refusal, stubs created on upgrade, path validation, `install.json` file list).

1. `scripts/sdd/install.py` with a `scripts/install` launcher. The ownership manifest is code in that module:
   - `FRAMEWORK`: path patterns copied and replaced on upgrade (spec decision 2), plus `docs/development/commands.md`.
   - `CLIENTS`: per client, the generated paths above (`.agents/skills/**` for Codex, Cursor, and Copilot; `CLAUDE.md` with Claude).
   - `PRODUCT`: stubs created only on a fresh install: copies of the starter `docs/product/*`, `docs/architecture/overview.md`, `docs/adr/README.md`, `docs/project-rules.md`; a minimal `README.md` with a Commands section, `.sdd/verification.json` (the framework file without `adapters` and `adapter-tests`), `.sdd/ci.json`, `.sdd/risk-rules.json` (copied as they are until CHG-006). `.github/CODEOWNERS.example`, filtered to installed paths, is framework-owned.
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
   - `test_agent_governance.py`: CODEOWNERS tests updated for computed rows (AC-10), and client-specific assertions skipped when that client's files are not in the repository, so the suite also passes inside an installed product. (As implemented, the governance test checks the shipped example against `protected(ROOT)`; no client-specific assertion needed skipping.)
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
| AC-14, AC-15 | 1.0.0 and migrated layouts, unrelated `.sdd/`, file at a parent path, symlinks, target equals source, dirty source | `test_install.py` | Refusal or collision, target unchanged; migrated layout upgraded |
| AC-13 | Full framework verification | `python3 scripts/check-docs`; `python3 scripts/verify broad --target framework --base main --level L3 --change CHG-005-installer` | Passed |
| Level floor | Change-level check | `python3 scripts/check-change-level --base main --level L3 --change CHG-005-installer --scope broad` | Passed |
| L3 review | Independent review in a fresh session | `sdd-independent-review` agent with `.agents/review/independent-review.md` | Findings recorded and resolved |

## Affected documentation

`AGENTS.md`, `README.md`, `docs/development/commands.md` (new), `automation.md`, `agent-compatibility.md`, `ci-enforcement.md`, `docs/README.md`, `.agents/workflows/verify/SKILL.md`, `docs/manual/02-adoption.md`, `03-working-a-change.md`, `CHANGELOG.md`.

## Deviations and decisions during execution

- The README collision rule (decision 3) made every new-repository install collide, because GitHub's initial README has no `## Commands` section. Owner decision (2026-10-19, in conversation): keep the rule; a new repository starts without a README (for example only GitHub's `.gitignore` or `LICENSE`), or with a README that has the section. Spec AC-01 and decision 4 updated; the collision message explains the fix.
- `.agents/README.md` linked to `adapters/clients.json`, which is not shipped; found by the first end-to-end install (`check-docs` failed in the product). The row is now plain text marked "framework repository only", and the Distribution section describes the installer.
- `docs/project-rules.md` also exists in this repository (AGENTS.md links to it); the installer copies it as the product stub.
- The installer reads new, not yet committed source files too and records `source_dirty` in `.sdd/install.json`, so installs from a development checkout are visible as such.
- Executable bits come from the source index (`100755`); on Windows the installer prints the `git add --chmod=+x` command for the product's first commit instead of staging anything.
- `.sdd/verification.json`: the `automation-tests` timeout rose from 120 to 300 seconds, because the suite with the installer tests takes about 120 seconds on Windows and the first broad run after round 2 was blocked by the timeout. Products receive the same value.
- Independent review round 3, focused on `mode()`/`plan()`, the new tests, and the timeout (2026-10-19): no blocking findings. N1 (migrated 1.0.0 orphan list includes product files in unchosen clients' directories) documented in the manual's migration note; N2 (a test wrote into the framework checkout) fixed by mocking the untracked listing; N3 (broad `TypeError`/`AttributeError` catch can mask installer bugs) accepted as residual risk, since nothing is written before planning ends.
- Independent review round 2 (2026-10-19): no blocking findings. Non-blocking R1 (stale manual text: adoption owner sentence, maintenance and agents chapters, ownership table), R2 (migrated 1.0.0 upgrades did not report unchosen clients' entrypoints), R3 (malformed JSON shapes raised tracebacks), R4 (CHANGELOG entry), R5 (this Technical approach predates round 1), R6 (clean-source path and upgraded record untested) were fixed: manual 02/05/maintenance and CHANGELOG reworded, orphans for unchosen clients in migrated layouts, `TypeError`/`AttributeError` refused, a note above step 1, and three tests added.
- Independent review round 1 (owner accepted all corrections, 2026-10-19, in conversation):
  - F1 (blocking): partial writes were possible (file at a parent path, dangling or directory symlinks, `.sdd` as a file, uncaught write errors). Every destination, including README, `.gitignore`, `.gitattributes`, and `install.json`, is now checked by `unsafe()` before writing; failures during writing return `failed` with the files written.
  - F2 (blocking): upgrading a 1.0.0 adopter would break `check-docs` (no `docs/project-rules.md`) and replace its `AGENTS.md` rules. Missing product stubs are now created on upgrade; unmigrated 1.0.0 layouts are refused with migration steps (spec decisions 1 and 2 refined, AC-14).
  - F3 (blocking): `workflows.md`, `manual/maintenance.md`, `manual/README.md`, manual 02 step 9, `automation.md`, README, and workflow comments still described template or copy adoption; rewritten. The earlier AC-11/AC-12 evidence was inaccurate.
  - F4: any symlink component and any path under `.git/` is refused.
  - F5: upgrade mode needs `.sdd/install.json` or a migrated 1.0.0 layout; other `.sdd/` and the framework checkout itself are refused.
  - F6: a dirty source is refused unless `--allow-dirty-source`, which prints a warning; only tracked files ship from a clean source.
  - F7: the adoption owner moved from the methodology header to `docs/project-rules.md`.
  - F8: `install.json` records the shipped file list; orphans are previous files no longer shipped, so product files under `scripts/` are not reported.
  - F9: written files get 0644, executables 0755.
  - F10: this plan's ownership and governance-test wording aligned with the code.
  - F11: tests added for the no-README stub, `install.json` version/commit/files, dry run with collisions, write failure, and the AC-14/AC-15 cases.

## Completion evidence

Verified version or diff: working snapshot on branch `chg-005-installer` after review round 1 (HEAD `c8316b3` plus uncommitted changes; snapshot in the Broad gate row; first run `4d47442bcc6fe307`), base `main` (`aefa291`; the CHG-003/004 closeout merged to `origin/main` later touches only those records).
Relevant environment: Windows 11, Git for Windows, Python 3.14.7; Linux via WSL Ubuntu, Python 3.14.4, on a native ext4 copy committed as a Git repository (so the installer tests run there too).

| AC / check | Result | Evidence summary / reference |
| --- | --- | --- |
| AC-01 | Passed | `test_install.py` `test_fresh_install_for_one_client` (target without README): framework, Claude, and product files including the README stub; no tools, adapters config, other clients, manual, framework specs, installer, or CHANGELOG; `LICENSE` untouched; `install.json` clients, commit, version, and file list; product `verification.json` without generator checks; filtered `CODEOWNERS.example`. `test_written_files_have_checkout_permissions` (POSIX: 0644/0755). |
| AC-02 | Passed | `test_client_selection` (`codex,cursor`). |
| AC-03 | Passed | `test_installed_product_passes_its_own_checks` (`check-docs`, `verify focused --target framework`). Manual, after review round 1: products installed without README and committed ran `verify standard --target framework` with 220 automation tests passing on Windows (`claude`, after the printed `git add --chmod=+x`) and on Linux (`codex,cursor`, files 644/755 without extra steps). |
| AC-04, AC-07 | Passed | `test_refuses_default_branch`, `test_refuses_dirty_worktree`, `test_refuses_unknown_client_and_nested_target`; target snapshots unchanged. |
| AC-05, AC-06 | Passed | `test_collisions_are_listed_and_nothing_is_written` (`AGENTS.md`, README without Commands, `.gitignore`, `.gitattributes`). |
| AC-08 | Passed | `test_dry_run_reports_and_writes_nothing` and the dry run inside the collision test, whose actions equal the real run's. |
| AC-09 | Passed | `test_upgrade_keeps_product_files_and_recorded_clients` (product files byte-identical, deleted `docs/adr/README.md` recreated, framework file replaced, recorded clients reused, `scripts/build.sh` not an orphan), `test_upgrade_reports_dropped_client_files_as_orphans`, `test_upgrade_without_record_needs_clients`. |
| AC-10 | Passed | `test_ci.py` `test_client_rows_required_only_when_installed`, `test_protected_rows_follow_installed_clients`; governance test uses `protected(ROOT)`. |
| AC-11, AC-12 | Passed (review) | Command registry split as specified; after review round 1, `workflows.md`, `manual/maintenance.md`, `manual/README.md`, manual 02, `automation.md`, `agent-compatibility.md`, `ci-enforcement.md`, README, and workflow comments describe only the installer; the only remaining mention of "Use this template" is manual 02's warning not to use it (and CHANGELOG history). |
| AC-14, AC-15 | Passed | `test_framework_1_0_target_needs_migration`, `test_unrelated_sdd_directory_is_refused`, `test_migrated_1_0_target_upgrades_and_gains_missing_stubs`, `test_file_where_a_directory_is_needed_is_a_collision`, `test_symlinks_are_collisions` (ran on Windows and Linux), `test_refuses_the_framework_checkout_itself`, `test_refuses_dirty_source_without_flag`, `test_clean_source_ships_tracked_files_only`, `test_migrated_1_0_target_reports_unchosen_client_files`, `test_malformed_target_json_is_a_refusal`, `test_write_failure_reports_what_was_written`. Manual: the Windows install without `--allow-dirty-source` was refused; with it, the warning was printed. |
| AC-13 | Passed | `check-docs` passed; `sync_adapters --check` 0 stale; broad gate below. |
| Full suites | Passed | Windows: 244 automation tests (7 skips: platform-specific) and 57 adapter tests. Linux native ext4 Git repository: 244 (no skips) and 57. |
| Level floor | Passed | `python3 scripts/check-change-level --base main --level L3 --change CHG-005-installer --scope broad`: floor L3. |
| Broad gate | Passed | `python3 scripts/verify broad --target framework --base main --level L3 --change CHG-005-installer`: docs, adapters, adapter-tests, automation-tests (121 s, 244 tests) passed on snapshot `d43352e0552eb42a` after review round 3; report `.sdd/results/verify-20261019T160339812185Z-e325a64b.json` (local, untracked). An earlier pass on `3aa63cb80c3a3600` preceded the round-3 test fix. The run before the timeout change (`verify-20261019T155425171654Z-09dfbbd2.json`) was blocked by the 120 s timeout; earlier runs `4d47442bcc6fe307` and `f65689090aed0135` passed. Only this line changed afterwards. |

Independent review: automated reviewer (`sdd-independent-review`, Claude sub-agent), fresh context without the implementation conversation (a different reviewer from CHG-001 to CHG-004), read-only tools; it ran no code, and every count, hash, and result it cites is requester-supplied. Round 2 resumed the same reviewer context. Not a human review or approval.

| Round | Target | Result | Resolution |
| --- | --- | --- | --- |
| 1 | Full patch vs `main`, snapshot `4d47442bcc6fe307` | Blocking: F1 (partial writes possible), F2 (1.0.0 upgrade breaks `check-docs` and replaces `AGENTS.md` rules), F3 (documents still describing template or copy adoption). Non-blocking: F4 (symlinked directories, `.git/`), F5 (upgrade detection, target equal to source), F6 (dirty source shipped), F7 (adoption owner in a framework file), F8 (product files reported as orphans), F9 (0600 permissions), F10 (plan wording), F11 (test gaps) | All fixed with owner acceptance; spec decisions 1 and 2 refined, AC-09 extended, AC-14 and AC-15 added; see Deviations |
| 2 | Full patch vs `main`, snapshot `f65689090aed0135` | No blocking findings. Non-blocking: R1 (stale manual text), R2 (migrated 1.0.0 upgrades did not report unchosen clients), R3 (malformed JSON tracebacks), R4 (CHANGELOG), R5 (plan approach text), R6 (clean-source and record tests) | All fixed; see Deviations. Focused re-review done as round 3 |
| 3 | `install.py`, `test_install.py`, `verification.json` vs `main`, snapshot `3aa63cb80c3a3600` | No blocking findings. Non-blocking: N1, N2, N3 (observation) | N1 documented, N2 fixed, N3 accepted as residual risk |

Review limitations: an isolated session of the same model is not human independence; round 2 was not a fresh context. Not exercised: CI (`sdd-gate` skipped in this repository), a real adopter install, and an upgrade of a real 1.0.0 adopter. Windows junctions are not detected as symlinks (Git cannot commit them).

Outstanding items / exceptions: `sdd-gate` is skipped in this repository by design; the installer is exercised only against local fixture repositories, not a real adopter.

Delivery: not merged; not released.
