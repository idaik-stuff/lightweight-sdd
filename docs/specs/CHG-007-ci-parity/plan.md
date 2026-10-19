# Plan: CHG-007-ci-parity | Product checks in CI, local CI parity, and product CI settings

Status: `approved` | Technical owner: Idaika Iglesias | Accepted by / date: Idaika Iglesias, 2026-10-19 (in conversation).
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
   - `ci_configuration(root)`: moved unchanged from `ci.py`, which re-exports it so existing callers and tests keep working.
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

None recorded yet.

## Completion evidence

Verified version or diff: pending. Relevant environment: pending.

| AC / check | Result | Evidence summary / reference |
| --- | --- | --- |
| AC-01 to AC-11 | Not run | Pending implementation. |

Independent review: pending; required for L3.

Outstanding items / exceptions: `sdd-gate` is skipped in this repository by design, so no live CI run exercises the product settings here.

Delivery: not merged; not released.
