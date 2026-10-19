# Plan: CHG-006-risk-rules | Framework and product risk rules, and path mapping

Status: `approved` | Technical owner: Idaika Iglesias | Accepted by / date: Idaika Iglesias, 2026-10-19 (in conversation).
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
   - Upgrade guard in `plan()`, before any write: if the target's `.sdd/risk-rules.json` has rule IDs outside the shipped framework rules and `.sdd/product-risk-rules.json` is missing, refuse with steps to move those rules. `MIGRATION` (1.0.0) gains the same step.
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

None recorded yet.

## Completion evidence

Verified version or diff: pending. Relevant environment: pending.

| AC / check | Result | Evidence summary / reference |
| --- | --- | --- |
| AC-01 to AC-09 | Not run | Pending implementation. |

Independent review: pending; required for L3.

Outstanding items / exceptions: `sdd-gate` is skipped in this repository by design.

Delivery: not merged; not released.
