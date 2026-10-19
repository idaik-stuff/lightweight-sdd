# Spec: CHG-007-ci-parity | Product checks in CI, local CI parity, and product CI settings

Status: `implemented` | Level: `L3` | Level rationale: changes how CI and local verification choose their target and scope, adds a product-owned CI policy file read from the base, and sets the rules for product checks on a clean runner (`verification-controls`, `ci-governance`); a mistake could route product changes past product checks or lower a scope.
Owner: Idaika Iglesias | Scope accepted by / date: Idaika Iglesias, 2026-10-19 (in conversation).
Related changes: last of the SDD Lite 2.0 rollout; it is the addendum deferred by [CHG-001](../CHG-001-branch-and-pr-workflow/spec.md) and the project-governance part left open by [CHG-006](../CHG-006-risk-rules/spec.md). The 2.0.0 release follows.

## Problem and goal

Three gaps remain before the framework can serve a real product:

1. Product checks registered in `.sdd/verification.json` run in `sdd-verify` on a clean runner that only sets up Python. A check such as `node node_modules/...` fails on every product PR, and the PR that fixes the registry cannot make its own run pass, because CI reads the registry from the base.
2. Local `scripts/verify` uses `--target product` by default, while CI chooses the target from `framework_paths`. A local run can therefore check a different target than CI will.
3. Since CHG-006, `.sdd/ci.json` is framework-owned and replaced by upgrades. A product cannot declare its own governance paths or raise a scope without losing it on the next upgrade.

Goal: product checks that work on a clean runner, documented; a local mode that picks the same target as CI; and a product-owned CI settings file that upgrades never replace and that can only make CI stricter.

## Context and current behavior

Observed at `baa5770` (main after CHG-006):

- `.github/workflows/sdd.yml` `sdd-verify` checks out the base (`sdd-trusted`) and the candidate merge, sets up Python 3.13 only, and runs `sdd-trusted/scripts/verify MODE --root sdd-candidate --policy-root sdd-trusted --target TARGET [...]`. A comment says product dependency setup belongs in the check registry.
- `scripts/sdd/ci.py` `assess_ci()` sets `target = 'framework'` when every changed path matches `framework_paths` of the base `.sdd/ci.json`, otherwise `product`; `design_only` when every path is Markdown under `design_paths`; the scope comes from `scopes` of the required level.
- `scripts/sdd/verify.py` accepts `--target framework|product` (default `product`); `product` without product checks is blocked.
- `docs/development/automation.md` "Connecting the product" describes registering real checks but not running them on a clean runner.

Closed design decisions (CHG-007 design discussion, 2026-10-19):

1. Runtimes: use what the CI runner image provides (`ubuntu-24.04`); no workflow change. The first registered product check installs pinned dependencies (for example `npm ci` from a lockfile). Document checking the runner's runtime versions and the bootstrap order: the PR that registers product checks touches only `.sdd/verification.json`, so its checks first run on the next PR.
2. `scripts/verify --target auto`: requires `--base`; uses the same rule as CI (every changed path is a framework path → `framework`, otherwise `product`), with the same policy files; records the chosen target in the report. The default target stays `product`. The `verify` workflow and the docs recommend `auto`.
3. A product-owned `.sdd/product-ci.json`, never replaced by upgrades, with two optional keys: `framework_paths` (extra paths routed as framework policy) and `scopes` (per level, only equal or higher than `.sdd/ci.json`; a lower scope is rejected). `ci.py` and `--target auto` merge it with `.sdd/ci.json`. It has an L3 floor, and CI reads it from the base.

## Scope and non-goals

Includes:

- `.sdd/product-ci.json` schema, validation, and merge with `.sdd/ci.json` in one place used by CI and by `verify --target auto`; rejection of a lower scope, unknown keys, or invalid patterns.
- `.sdd/product-ci.json` protected by an L3 floor (`ci-governance`) and listed in `framework_paths`.
- `verify --target auto` and its report field; the `verify` workflow and `docs/development/commands.md` recommend it.
- Installer: `.sdd/product-ci.json` as a product-owned stub with no extra settings.
- Documentation: `automation.md` "Connecting the product" (clean runner, first check installs dependencies, runner versions, bootstrap order), `ci-enforcement.md` (product CI settings), manual 04 and 02 where they describe registering checks.
- CHANGELOG entry.

Does not include:

- Setting up runtimes in `sdd.yml` (decision 1; possible later when a product needs a pinned version).
- Changing the default `--target` of `scripts/verify`.
- Product extensions of `design_paths` or of any other CI setting beyond `framework_paths` and raising `scopes`.
- Publishing the 2.0.0 release.

## Expected behavior

- `verify MODE --target auto --base B --level L` runs the framework target when every changed path is a framework path (including product-declared ones), otherwise the product target, and the report records `target_selection: auto` with the resolved target.
- In CI and locally, a path listed in the product's `framework_paths` is routed as framework policy; its floor, if any, still comes from the risk rules.
- A product scope setting can only keep or raise the CI scope for a level.
- Without `.sdd/product-ci.json`, behavior is exactly as before.

## Acceptance criteria

Include at least one failure or boundary AC, or state in one line why there is none.

| ID | Scenario / precondition | Action | Observable outcome |
| --- | --- | --- | --- |
| AC-01 | Changes only under framework paths | `verify standard --target auto --base B --level L1` | Framework target selected and recorded; same target as `assess_ci` for the same diff |
| AC-02 | Changes include a product path | Same command | Product target selected; blocked when no product checks are registered, as with `--target product` |
| AC-03 | `--target auto` without `--base` | Run `verify` | Refused with a clear message; nothing executed |
| AC-04 | `.sdd/product-ci.json` lists `tools/release/**` in `framework_paths`; a change touches only that path | CI assessment and `--target auto` | Both select the framework target |
| AC-05 | `.sdd/product-ci.json` sets `L2: broad` | CI assessment of an L2 PR | Scope `broad` |
| AC-06 | `.sdd/product-ci.json` sets `L3: standard`, or has an unknown key or an invalid pattern | Load the CI policy | Rejected with the file named |
| AC-07 | A PR edits `.sdd/product-ci.json` to raise or lower settings | CI assessment | The base file's settings apply to that PR; the change itself has an L3 floor |
| AC-08 | No `.sdd/product-ci.json` | CI assessment and `verify --target auto` | Same results as before this change |
| AC-09 | Fresh install, then upgrade with an edited `.sdd/product-ci.json` | Run the installer | Created on install; byte-identical after upgrade |
| AC-10 | Updated automation, CI enforcement, commands, manual 02/04, `verify` workflow | Read them | Clean-runner rule, first-check dependency install, runner versions, bootstrap order, `--target auto`, and product CI settings are documented |
| AC-11 | Repository at the end of this change | `scripts/check-docs`, `scripts/verify broad --target framework` | Pass |

AC-03, AC-06, and AC-07 are the boundaries: auto never guesses without a base, a product file can never lower a scope, and a PR cannot use its own CI settings.

## Constraints and compatibility

- Property at risk: CI never runs a weaker scope or skips product checks for a product path because of product settings (AC-05 to AC-07).
- A base without `.sdd/product-ci.json` behaves exactly as today (AC-08); a 1.0.0 base ignores the new file, which is safe because it only adds strictness.
- `sdd.yml` is unchanged; standard library only.

## Uncertainties

None open. Design closed with the owner on 2026-10-19.

## Acceptance and next steps

Scope acceptance: accepted by Idaika Iglesias on 2026-10-19 (in conversation), with AC-01 to AC-11. Next: plan with strategy.

Related plan: [plan.md](plan.md). States and completion rules: [docs/specs/README.md](../README.md).

Upon completion, record evidence and delivery status in the plan. If another change replaces this behavior, reference that change without rewriting history.
