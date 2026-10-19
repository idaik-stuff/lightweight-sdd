# Plan: CHG-006-risk-rules | Framework and product risk rules, and path mapping

Status: `completed` | Technical owner: Idaika Iglesias | Accepted by / date: Idaika Iglesias, 2026-10-19 (in conversation).
Spec: [spec.md](spec.md) | Verification scope: `broad`.

## System inspection

Inspected at base `658216c` (main after CHG-005):

- `scripts/sdd/changes.py` `load_rules(root)` reads `.sdd/risk-rules.json` and validates version, unique IDs, levels, reasons, and patterns; callers are `assess()` (working tree or `policy_root`), `verify.configuration()`, and `ci.assess_ci()` (trusted base). None of them reads any other rules file.
- `.sdd/ci.json` `framework_paths` lists `.sdd/verification.json`, `.sdd/risk-rules.json`, `.sdd/ci.json` explicitly; the `verification-controls` rule lists `.sdd/verification.json` and `.sdd/risk-rules.json`.
- `scripts/sdd/install.py`: `PRODUCT` includes `.sdd/ci.json` and `.sdd/risk-rules.json`; generated framework content already has a precedent (`CODEOWNERS.example` filtered by client); `mode()` holds the 1.0.0 `MIGRATION` text.
- Tests that write or read the rules: `support.py` `Fixture.rules()` writes `.sdd/risk-rules.json`; `test_changes.py` (duplicate ID, invalid level, shipped rules valid, hook floor), `test_agent_governance.py` (L3 floors for client paths), `test_install.py` (fixture removes `.sdd/`).
- Documentation naming the file: `automation.md` "Risk floors and Git scope", manual 02 step 7 and the ownership table, manual 04, `maintenance.md` table, manual example README (adoption narrative).

## Technical approach

1. Data: move `public-contract`, `security-boundary`, `persistent-data`, `production-delivery` unchanged into a new `.sdd/product-risk-rules.json` (same schema, `version: 1`). `.sdd/risk-rules.json` keeps `delivery-policy`, `verification-controls`, `ci-governance`, `agent-integration-controls`; `verification-controls` gains `.sdd/product-risk-rules.json`. `.sdd/ci.json` `framework_paths` gains `.sdd/product-risk-rules.json`.
2. Loader: extract the current validation into `validate_rules(data, source)`; `load_rules(root)` validates the required framework file and, when present, the product file, then concatenates them and rejects a duplicate ID across files. Error messages name the file. Callers are unchanged, so CI keeps reading both files from the base.
3. Installer:
   - `.sdd/risk-rules.json` and `.sdd/ci.json` become framework-owned; the rules file is generated with `.agents/tools/**` and `.agents/adapters/**` removed from every rule (a rule left with no patterns is dropped); `ci.json` is copied.
   - `.sdd/product-risk-rules.json` becomes a product stub copied from this repository.
   - Upgrade guard in `plan()`, before any write (as first planned: rule IDs only, when the product file is missing; superseded by the stricter guard recorded in Deviations, review rounds 1 and 2). `MIGRATION` (1.0.0) gains the same step.
4. Path mapping: manual 02 step 7 rewritten around the two files and the first-product-change rule; one sentence in the methodology (section 1 or 2) and in the `plan` workflow step 5 ("for the first change that creates product code, map the real paths in `.sdd/product-risk-rules.json` or state why the generic patterns suffice"). Automation, manual 04, maintenance, and the example README name the right file.
5. Tests and CHANGELOG.

Rejected alternatives:

- One file with a `"framework": true` flag per rule: the installer would have to merge files on upgrade, which breaks the "replace framework-owned files" rule.
- Making the product file required: every fixture and 1.0.0 layout would need it, and it adds nothing to safety, because deleting it is itself an L3 change judged against the base policy.

## Affected components and contracts

| Area / path | Proposed change | Impact / consumer |
| --- | --- | --- |
| `.sdd/risk-rules.json`, `.sdd/product-risk-rules.json` (new), `.sdd/ci.json` | Rules split; product file protected and routed | Every floor check here and in products |
| `scripts/sdd/changes.py` | Two-file loader | `check-change-level`, `verify`, CI |
| `scripts/sdd/install.py` | Ownership change, filtered rules, upgrade guard, migration text | Products |
| `scripts/tests/test_changes.py`, `test_ci.py`, `test_install.py`, `test_agent_governance.py` | Tests below | Framework tests |
| Manual 02/04, maintenance, example README, `automation.md`, methodology, `plan` workflow, CHANGELOG | Wording | Readers, agents |

## Risk-proportionate strategy

| Area | Decision, check, or reason it is not affected |
| --- | --- |
| Compatibility and consumers | Floors identical (AC-01, checked against the base file); callers unchanged; a 1.0.0-style single file in a base still works because the product file is optional. Products with mixed rules are refused until migrated (AC-07). |
| Data, integrity, and migration | Product rules are product data: never replaced; the upgrade guard prevents losing rules kept in the old single file. |
| Permissions, security, and privacy | No floor is lowered; the new file gets an L3 floor and framework routing (AC-04); CI still uses base policy (AC-03). |
| Failures, load, and availability | An invalid or duplicate product rule fails closed with the file named (AC-02). |
| Change observability | Error messages name the file; the installer reports the refusal and steps. |
| Rollout and feasible recovery | Ships with 2.0.0 through this PR; revert the squash commit to recover. |

## Implementation steps

1. Data split and loader, with tests (AC-01 to AC-04).
2. Installer ownership, filtering, upgrade guard, with tests (AC-05 to AC-07).
3. Documentation and workflow (AC-08), CHANGELOG.
4. Broad verification (AC-09) and independent review.

## Verification plan and traceability

Environment: Windows 11 with Python 3; Linux via WSL Ubuntu (native ext4 Git repository) for the full suites.

| AC / risk | Test, check, or manual procedure | Command / location / environment | Expected result |
| --- | --- | --- | --- |
| AC-01 | Union of both files equals the base file | One-off comparison against `git show main:.sdd/risk-rules.json`, recorded here; `test_changes.py` shipped-rules test for the expected IDs per file | Identical rules |
| AC-02 | Loader cases: both files, framework only, duplicate across files, invalid product file | `test_changes.py` | Merge, framework only, error, error |
| AC-03 | CI with a base product floor and a candidate that removes it | `test_ci.py` | Floor retained |
| AC-04 | Floor and routing of the new file | `test_agent_governance.py` | L3; framework path |
| AC-05, AC-06, AC-07 | Install, upgrade, mixed-rules refusal | `test_install.py` | As specified |
| AC-08 | Inspection | Diff review, independent review | Present |
| AC-09 | Full framework verification | `python3 scripts/check-docs`; `python3 scripts/verify broad --target framework --base main --level L3 --change CHG-006-risk-rules` | Passed |
| Level floor | Change-level check | `python3 scripts/check-change-level --base main --level L3 --change CHG-006-risk-rules --scope broad` | Passed |
| L3 review | Independent review in a fresh session | `sdd-independent-review` agent | Findings recorded and resolved |

## Affected documentation

`docs/manual/02-adoption.md`, `04-verification-ci.md`, `maintenance.md`, `example/README.md`, `docs/development/automation.md`, `methodology.md`, `.agents/workflows/plan/SKILL.md`, `CHANGELOG.md`.

## Deviations and decisions during execution

- Independent review round 2 (2026-10-19): no blocking findings. N1 (moving floors in a PR before the upgrade leaves them unenforced, since the old scripts read only the framework file) fixed by requiring, in RULES_MIGRATION, MIGRATION, the CHANGELOG, and the maintenance guide, that the move happens in the same branch and pull request as the upgrade. N2 (a product rule with the same ID as a custom framework-file rule but fewer patterns was accepted) fixed: `rules_guard()` compares patterns and floor against the shipped rule or, failing that, the product rule with the same ID; new test `test_upgrade_refuses_product_copy_with_fewer_patterns`. N3: Technical approach step 3 now points to the superseding guard. N4: the guard was run against the real 1.0.0 rules file (`git show ebf25ad:.sdd/risk-rules.json`): no framework rule has extra patterns beyond the framework-repository-only ones, so an unmodified 1.0.0 adopter only needs to move the four starter product rules.
- Independent review round 1 (owner accepted all corrections, 2026-10-19, in conversation):
  - F1 (blocking): the upgrade guard compared rule IDs only and was skipped once a product file existed, so patterns a product had added to a framework rule, or a custom rule left in the framework file, were silently dropped. `rules_guard()` now always runs on upgrade and refuses when the target framework file has a rule that is neither shipped nor in the product file, a pattern the shipped rule lacks (framework-repository-only patterns ignored), or a higher floor.
  - F2: an upgrade is refused when the product file reuses a shipped rule ID.
  - F3: CHANGELOG, the 1.0.0 migration text, and the maintenance upgrade steps say that `ci.json` is replaced and that added patterns move too.
  - F4: the refusal message also covers rules retired by an older framework version ("delete them").
  - F5: duplicates inside one file are reported with the file named; cross-file duplicates keep their own message.
  - F6: a dangling symlink for the product file fails closed instead of being ignored.
  - F7: tests added for the starter product rules, a duplicate inside the product file, a dangling link, an L2 change touching only the product file, each guard case, a malformed target rules file, and a migrated 1.0.0 single-file layout.

## Completion evidence

Verified version or diff: working snapshot on branch `chg-006-risk-rules` (HEAD `d938b65` plus uncommitted changes; snapshot in the Broad gate row), base `main` (`658216c`).
Relevant environment: Windows 11, Git for Windows, Python 3.14.7; Linux via WSL Ubuntu (native ext4 Git repository), Python 3.14.4.

| AC / check | Result | Evidence summary / reference |
| --- | --- | --- |
| AC-01 | Passed | One-off comparison of `load_rules()` on this branch with `git show main:.sdd/risk-rules.json`: same 8 IDs, levels, and reasons; patterns identical except the planned addition of `.sdd/product-risk-rules.json` to `verification-controls`. `test_changes.py` `test_shipped_rules_are_split_by_owner` pins the framework IDs and, in this repository, the four starter product rules. |
| AC-02 | Passed | `test_changes.py` `test_product_rules_add_floors`, `test_framework_rules_alone_without_product_file`, `test_duplicate_id_across_files_rejected`, `test_duplicate_inside_product_file_names_the_file`, `test_dangling_product_rules_link_fails_closed` (Linux; needs symlinks), `test_invalid_product_rules_name_the_file`. |
| AC-03 | Passed | `test_ci.py` `test_candidate_cannot_remove_base_product_floor` (candidate empties the product file and touches `billing/`; base floor L3 still applies). |
| AC-04 | Passed | `test_agent_governance.py` `test_product_rules_file_is_an_l3_framework_path`; `test_changes.py` `test_change_to_product_rules_file_requires_l3` (an L2 change touching only the product file fails on the `verification-controls` floor). |
| AC-05 | Passed | `test_install.py` `test_rules_and_ci_policy_ownership` (filtered framework rules, framework `ci.json`, product stub, file list). |
| AC-06 | Passed | `test_upgrade_replaces_framework_policy_and_keeps_product_rules`. |
| AC-07 | Passed | `test_upgrade_with_product_rules_in_framework_file_is_refused`, `test_upgrade_refuses_patterns_added_to_framework_rules`, `test_upgrade_refuses_custom_rule_left_in_framework_file`, `test_upgrade_accepts_custom_rule_already_in_product_file`, `test_upgrade_refuses_product_copy_with_fewer_patterns`, `test_upgrade_ignores_framework_repository_only_patterns`, `test_upgrade_refuses_shipped_id_reused_by_product`, `test_upgrade_with_malformed_framework_rules_is_refused`, `test_migrated_1_0_target_with_single_rules_file_is_refused`; 1.0.0 `MIGRATION` text names the product rules and `ci.json` steps. |
| AC-08 | Passed (review) | Manual 02 step 7 rewritten ("Map the risk rules to your layout"), methodology section 1, `plan` workflow step 5; automation, manual 04, maintenance, and example README name the right files. |
| AC-09 | Passed | `check-docs` passed; `sync_adapters --check` 0 stale; broad gate below. |
| Full suites | Passed | Windows: 265 automation tests (7 platform skips, in the broad gate run) and 57 adapter tests. Linux: 265 (no skips). Linux product install (`claude`) passed `check-docs` and `verify standard` (227 tests); its `check-change-level --level L1` on the install diff detected the L3 floor as expected. |
| Level floor | Passed | `python3 scripts/check-change-level --base main --level L3 --change CHG-006-risk-rules --scope broad`: floor L3. |
| Broad gate | Passed | `python3 scripts/verify broad --target framework --base main --level L3 --change CHG-006-risk-rules`: docs, adapters, adapter-tests, automation-tests (161 s) passed on snapshot `0a56015796f96ae8` after review round 2 (earlier passes `d5ba640f4003619e`, `d463d8cf9dc2e1e6`); report `.sdd/results/verify-20261019T180555649434Z-cba83d70.json` (local, untracked); only this line changed afterwards. |

Independent review: automated reviewer (`sdd-independent-review`, Claude sub-agent), fresh context without the implementation conversation (a different reviewer from earlier changes), read-only tools; it ran no code, and every count, hash, and result it cites is requester-supplied. Not a human review or approval.

| Round | Target | Result | Resolution |
| --- | --- | --- | --- |
| 1 | Full patch vs `main`, snapshot `d5ba640f4003619e` | Blocking: F1 (upgrade could silently drop patterns added to framework rules, or a custom rule left in the framework file). Non-blocking: F2 (shipped ID reused by the product), F3 (`ci.json` edits discarded silently), F4 (message for retired rules), F5 (duplicate inside one file), F6 (dangling product file link), F7 (test gaps) | All fixed; see Deviations |
| 2 | Full patch vs `main`, snapshot `d463d8cf9dc2e1e6` | No blocking findings. Non-blocking: N1 (unenforced window between a separate move PR and the upgrade), N2 (same-ID product rule with fewer patterns accepted), N3 (stale plan text), N4 (guard not checked against a real 1.0.0 file) | All fixed or checked; see Deviations. N2 changed `rules_guard()` logic |

Review limitations: an isolated session of the same model is not human independence. Not exercised: CI (`sdd-gate` skipped in this repository) and a real adopter upgrade.

Outstanding items / exceptions: `sdd-gate` is skipped in this repository by design. The round-2 N2 change to `rules_guard()` (comparing against the same-ID product rule, with its test) was not re-reviewed: the owner chose on 2026-10-19 to merge without that focused check, which the reviewer had advised.

Delivery: merged by the owner (Idaika Iglesias) through [PR #10](https://github.com/idaik-stuff/lightweight-sdd/pull/10) as squash commit `baa5770` on 2026-10-19; `sdd-gate` skipped in this repository by design. Not released: the 2.0.0 version is pending CHG-007.
