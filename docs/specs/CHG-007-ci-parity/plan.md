# Plan: CHG-007-ci-parity | Product checks in CI, local CI parity, and product CI settings

Status: `completed` | Technical owner: Idaika Iglesias | Accepted by / date: Idaika Iglesias, 2026-10-19 (in conversation).
Spec: [spec.md](spec.md) | Verification scope: `broad`.

## System inspection

Inspected at base `baa5770` (main after CHG-006):

- `scripts/sdd/ci.py` holds `ci_configuration(root)` (validates `.sdd/ci.json`: `framework_paths`, `design_paths`, `scopes` with minimums) and computes, in `assess_ci()`, `target`, `design_only`, and `scope` from the trusted base's policy. `ci.py` imports `verify` (`configuration`, `select`), and `ci_setup.py` imports `ci_configuration` from `ci`.
- `scripts/sdd/verify.py` `run()` takes `target` in `{framework, product}`; `main()` restricts `--target` to those two, default `product`. `verify` must not import `ci`, which already imports `verify`.
- `scripts/sdd/changes.py` `changed_paths(root, base)` returns the committed, staged, unstaged, and untracked paths against a base, the same set `assess()` uses.
- `.sdd/ci.json` `framework_paths` and the `ci-governance` rule list each `.sdd/*.json` policy file explicitly.
- `scripts/sdd/install.py` `PRODUCT` lists product stubs created when missing.
- `.github/workflows/sdd.yml` is not changed by this plan.

## Technical approach

1. New module `scripts/sdd/policy.py` (no import of `ci` or `verify`):
   - `ci_configuration(root)`: moved from `ci.py` with the same validation (its messages now name `.sdd/ci.json`), which re-exports it so existing callers and tests keep working.
   - `ci_policy(root)`: `ci_configuration(root)` merged with `.sdd/product-ci.json` when present (exists or is a symlink, so a dangling link fails closed). The product file requires `version: 1` and allows only `framework_paths` (list of patterns, validated like the framework ones, appended) and `scopes` (subset of levels; each value a valid scope not lower than `.sdd/ci.json`'s for that level, replacing it). Errors name the file.
   - `route(policy, paths)`: returns `(target, design_only)` with today's rule from `assess_ci()`.
2. `ci.py`: `assess_ci()` uses `ci_policy(trusted)` and `route()`; the candidate's files are still validated (`ci_policy(candidate)`), never used for routing. Behavior without a product file is unchanged.
3. `verify.py`: `--target auto`. `run()` resolves it before selection: refuse without `--base`; otherwise `route(ci_policy(policy_root or root), changed_paths(root, base))`. The report gets `target_selection` (`auto` or `explicit`) and the resolved `target`; the summary line prints the resolved target.
4. Data and protection: `.sdd/product-ci.json` (`{"version": 1}`) in this repository as the stub; added to `framework_paths` in `.sdd/ci.json` and to the `ci-governance` rule.
5. Installer: `.sdd/product-ci.json` joins `PRODUCT`.
6. Documentation: `automation.md` "Connecting the product" (clean runner, first check installs dependencies from a lockfile, check runner image versions, bootstrap order), `ci-enforcement.md` (product CI settings, base-read, raise-only), `commands.md` and the `verify` workflow (`--target auto`), manual 02 step 6 and manual 04 where they register checks; CHANGELOG.

Rejected alternatives:

- Computing auto routing inside `verify.py` with its own copy of the rule: two copies of the routing rule would drift; a shared module keeps CI and local identical.
- Letting `.sdd/product-ci.json` replace `.sdd/ci.json` values freely: a product could lower a scope; decision 3 allows only raising.

## Affected components and contracts

| Area / path | Proposed change | Impact / consumer |
| --- | --- | --- |
| `scripts/sdd/policy.py` (new), `ci.py`, `verify.py` | Shared policy loading and routing; `--target auto` | CI assessment, local verification |
| `.sdd/product-ci.json` (new), `.sdd/ci.json`, `.sdd/risk-rules.json` | Stub; protection and routing | Products and this repository |
| `scripts/sdd/install.py` | Product stub | Products |
| `scripts/tests/test_ci.py`, `test_verify.py`, `test_install.py`, `test_agent_governance.py` | Tests below | Framework tests |
| `automation.md`, `ci-enforcement.md`, `commands.md`, `verify` workflow, manual 02/04, CHANGELOG | Wording | Readers, agents |

## Risk-proportionate strategy

| Area | Decision, check, or reason it is not affected |
| --- | --- |
| Compatibility and consumers | No product file: identical CI and local results (AC-08 tests compare). Existing imports of `ci_configuration` keep working. Default `--target` unchanged. |
| Data, integrity, and migration | Product CI settings are product data: created once, never replaced (AC-09). |
| Permissions, security, and privacy | The product file can only add framework paths or raise scopes; CI reads it from the base; it has an L3 floor; `sdd.yml` and its permissions are unchanged. |
| Failures, load, and availability | Invalid, lowering, unknown-key, or dangling-link product files fail closed with the file named (AC-06). `auto` without a base refuses (AC-03). |
| Change observability | The verify report records `target_selection` and the resolved target; CI's policy report already records target and scope. |
| Rollout and feasible recovery | Ships with 2.0.0 through this PR; revert the squash commit to recover. |

## Implementation steps

1. `policy.py`, `ci.py` refactor, product CI file, protection, with tests (AC-04 to AC-08).
2. `verify --target auto` with tests (AC-01 to AC-03).
3. Installer stub (AC-09); documentation and workflow (AC-10); CHANGELOG.
4. Broad verification (AC-11) and independent review.

## Verification plan and traceability

Environment: Windows 11 with Python 3; Linux via WSL Ubuntu (native ext4 Git repository) for the full suites.

| AC / risk | Test, check, or manual procedure | Command / location / environment | Expected result |
| --- | --- | --- | --- |
| AC-01, AC-02 | Auto routing for framework-only and mixed diffs, compared with `route()` used by CI | `scripts/tests/test_verify.py` | Framework / product; recorded in report |
| AC-03 | Auto without base | `test_verify.py` | Refused, nothing executed |
| AC-04 | Product framework path in CI and auto | `test_ci.py`, `test_verify.py` | Framework target |
| AC-05, AC-06 | Raised scope; lowered scope, unknown key, invalid pattern, dangling link | `test_ci.py` | Broad; errors naming the file |
| AC-07 | Candidate edits product CI settings | `test_ci.py` | Base settings apply; L3 floor (`test_agent_governance.py`) |
| AC-08 | No product file | Existing `test_ci.py` and `test_verify.py` cases unchanged | Pass unchanged |
| AC-09 | Install and upgrade | `test_install.py` | Created; kept byte-identical |
| AC-10 | Inspection | Diff review, independent review | Present |
| AC-11 | Full framework verification | `python3 scripts/check-docs`; `python3 scripts/verify broad --target framework --base main --level L3 --change CHG-007-ci-parity` | Passed |
| Level floor | Change-level check | `python3 scripts/check-change-level --base main --level L3 --change CHG-007-ci-parity --scope broad` | Passed |
| L3 review | Independent review in a fresh session | `sdd-independent-review` agent | Findings recorded and resolved |

## Affected documentation

`docs/development/automation.md`, `ci-enforcement.md`, `commands.md`, `.agents/workflows/verify/SKILL.md`, `docs/manual/02-adoption.md`, `04-verification-ci.md`, `CHANGELOG.md`.

## Deviations and decisions during execution

- `ci.py` keeps `ci_configuration` as a re-export from `policy.py` so `ci_setup.py` and the tests need no change.
- Independent review round 2 (2026-10-19): no blocking findings. Fixed: N1-r2 (`*` crosses `/` in `fnmatch`, so `*.py` matched all Python files): deeper probes with common source extensions reject such patterns, and `ci-enforcement.md` explains the matching; N7: auto also validates the working tree's policy files, as CI validates the candidate's (test `test_auto_validates_working_tree_product_ci`); N8: the installer reads target JSON with the strict `load_json` (duplicate keys rejected; test `test_upgrade_preflight_rejects_duplicate_json_keys`); N9: warning wording, test imports, and the docs now say auto reads the routing and scope files from the base while the registry and risk rules come from the working tree unless `--policy-root` is given. Not re-reviewed after these fixes.
- Independent review round 1 (owner accepted all corrections, 2026-10-19, in conversation):
  - B1 (blocking): `--target auto` read the policy files from the working tree, while CI reads them from the base, so a branch that added `src/**` to product `framework_paths` was routed to `framework` locally and to `product` in CI. Auto now uses `--policy-root` when given, else `ci_policy_at()`, which reads `.sdd/ci.json` and `.sdd/product-ci.json` as committed at `--base` (regular files only). Test `test_auto_ignores_working_tree_policy_edits`.
  - B2 (blocking): unknown keys, a missing `version`, or a non-object product file raised errors that did not name `.sdd/product-ci.json`; `merge()` now prefixes the file and the tests require it.
  - N1: a product `framework_paths` pattern that matches every path (`**`, `*`, `**/*`, `*/**`) is rejected, and `ci-enforcement.md` says those paths run no product checks.
  - N2: the clean-runner guidance now says the dependency install check goes first in the product `focused` profile, and that the registration PR is L3 with spec and plan.
  - N3: the installer refuses an upgrade when the product CI settings would be invalid against the shipped `.sdd/ci.json` (for example a scope below a raised framework scope).
  - N4: tests compare `--target auto` with `assess_ci` on the same test merge, and cover a candidate removing the base product file, an invalid candidate file, auto with `--dry-run`, and the installer refusal.
  - N5: this plan's "moved unchanged" wording corrected.
  - N6: the auto report records `ci_scope` for the declared level and warns when the local mode is lower; a failed auto run no longer prints `target=auto (auto)`.

## Completion evidence

Verified version or diff: working snapshot on branch `chg-007-ci-parity` (HEAD `a92f833` plus uncommitted changes; snapshot in the Broad gate row), base `main` (`635eb00`).
Relevant environment: Windows 11, Git for Windows, Python 3.14.7; Linux via WSL Ubuntu (native ext4 Git repository), Python 3.14.4.

| AC / check | Result | Evidence summary / reference |
| --- | --- | --- |
| AC-01 | Passed | `test_verify.py` `test_auto_selects_framework_like_ci` (report records `target_selection: auto`); `test_ci.py` `test_auto_matches_assess_ci_on_the_test_merge` (auto and `assess_ci` agree on the same merge for a framework and a product path); `test_auto_ignores_working_tree_policy_edits` (B1). |
| AC-02 | Passed | `test_auto_selects_product_and_blocks_without_product_checks`. |
| AC-03 | Passed | `test_auto_requires_base` (status `error`, no checks run). |
| AC-04 | Passed | `test_ci.py` `test_product_framework_path_routes_as_framework` and `test_without_product_ci_the_same_path_is_product`; `test_verify.py` `test_auto_uses_product_framework_paths`. |
| AC-05 | Passed | `test_product_ci_raises_a_scope` (L1 PR runs `broad`). |
| AC-06 | Passed | `test_product_ci_cannot_lower_scope_or_add_unknown_keys` (lower scope, unknown key, missing version, invalid pattern, version, unknown level, non-object; every message names the file); `test_product_ci_rejects_catch_all_framework_paths`; `test_verify.py` `test_dangling_product_ci_link_fails_closed` (Linux; needs symlinks). |
| AC-07 | Passed | `test_candidate_product_ci_does_not_apply_to_its_own_pr`, `test_candidate_cannot_relax_or_remove_base_product_ci`, `test_invalid_candidate_product_ci_fails_the_assessment`; `test_agent_governance.py` `test_product_ci_file_is_an_l3_framework_path`. |
| AC-08 | Passed | All earlier `test_ci.py` and `test_verify.py` cases pass unchanged without a product CI file. |
| AC-09 | Passed | `test_install.py` `test_product_ci_settings_are_created_once_and_kept`, `test_upgrade_refuses_product_ci_below_shipped_scope`. `test_verify.py` `test_auto_dry_run_and_ci_scope_warning` (N6). |
| AC-10 | Passed (review) | `automation.md` "Connecting the product" (clean runner, runner image runtimes, first check installs pinned dependencies, registration order), `ci-enforcement.md` (product CI settings; registering checks), `commands.md` (`--target auto`), `verify` workflow, manual 02 step 6, manual 04 targets. |
| AC-11 | Passed | `check-docs` passed; `sync_adapters --check` 0 stale; broad gate below. |
| Full suites | Passed | Windows: automation tests in the broad gate run, 57 adapter tests. Linux: 286 automation tests (no skips) and 57. |
| Level floor | Passed | `python3 scripts/check-change-level --base main --level L3 --change CHG-007-ci-parity --scope broad`: floor L3. |
| Broad gate | Passed | `python3 scripts/verify broad --target framework --base main --level L3 --change CHG-007-ci-parity`: docs, adapters, adapter-tests, automation-tests (200 s, 286 tests) passed on snapshot `665fd75a8fbf765e` after review round 2 (earlier passes `d890ac0a8c5d3e69`, `c4c75f60b7dd8b4f`); report `.sdd/results/verify-20261019T191507848395Z-d1c78cdd.json` (local, untracked); only this line changed afterwards. The Windows suite uses two thirds of the 300 s timeout. |

Independent review: automated reviewer (`sdd-independent-review`, Claude sub-agent), fresh context without the implementation conversation (a different reviewer from earlier changes), read-only tools; it ran no code, and every count, hash, and result it cites is requester-supplied. Round 2 resumed the same reviewer context. Not a human review or approval.

| Round | Target | Result | Resolution |
| --- | --- | --- | --- |
| 1 | Full patch vs `main`, snapshot `d890ac0a8c5d3e69` | Blocking: B1 (auto read working-tree policy files while CI reads the base), B2 (product file errors not named). Non-blocking: N1 (catch-all patterns), N2 (check order and registration PR wording), N3 (no upgrade preflight for product CI settings), N4 (test gaps), N5 (plan wording), N6 (CI scope in local report) | All fixed; see Deviations |
| 2 | Full patch vs `main`, snapshot `c4c75f60b7dd8b4f` | No blocking findings. Non-blocking: N1-r2 (`*.py`-style patterns), N7 (auto did not validate working-tree policy), N8 (installer JSON parsing), N9 (cosmetic, docs precision) | All fixed; not re-reviewed |

Review limitations: an isolated session of the same model is not human independence; round 2 was not a fresh context. Not exercised: CI (`sdd-gate` skipped in this repository), a real product with product checks.

Outstanding items / exceptions: `sdd-gate` is skipped in this repository by design, so no live CI run exercises the product settings here. The round-2 fixes (N1-r2, N7, N8, N9 in `policy.py`, the `verify` auto path, and the installer) were not re-reviewed: the owner chose on 2026-10-19 to merge without that focused check, which the reviewer had suggested.

Delivery: merged by the owner (Idaika Iglesias) through [PR #12](https://github.com/idaik-stuff/lightweight-sdd/pull/12) as squash commit `4927381` on 2026-10-19; `sdd-gate` skipped in this repository by design. Released as part of 2.0.0 once the owner tags it.
