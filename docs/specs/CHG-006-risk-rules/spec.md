# Spec: CHG-006-risk-rules | Framework and product risk rules, and path mapping

Status: `approved` | Level: `L3` | Level rationale: changes how path floors are loaded and which file owns each rule (`verification-controls`), and what upgrades deliver to products; a mistake could drop a floor or keep products on stale framework rules.
Owner: Idaika Iglesias | Scope accepted by / date: Idaika Iglesias, 2026-10-19 (in conversation).
Related changes: sixth of the SDD Lite 2.0 rollout; builds on [CHG-005](../CHG-005-installer/spec.md) (installer and file ownership). CHG-007 (CI runtimes, `--target auto`, project governance paths) follows.

## Problem and goal

`.sdd/risk-rules.json` holds both the framework's own floors and the generic product floors. Since CHG-005 the installer treats it, and `.sdd/ci.json`, as product-owned: created once, never replaced. A framework release that adds or changes a framework floor, or a framework path for CI routing, therefore never reaches installed products. The generic product rules are also never mapped to a product's real layout by any defined step.

Goal: framework floors and CI routing are framework-owned and arrive with every upgrade; product floors live in a product-owned file that upgrades never replace; and the first change that creates product code maps the real paths, or says why the generic patterns are enough.

## Context and current behavior

Observed at `658216c` (main after CHG-005):

- `.sdd/risk-rules.json` has eight L3 rules: `public-contract`, `security-boundary`, `persistent-data`, `production-delivery` (generic product rules) and `delivery-policy`, `verification-controls`, `ci-governance`, `agent-integration-controls` (framework controls). `ci-governance` includes `.agents/adapters/**` and `.agents/tools/**`, which exist only in the framework repository.
- `scripts/sdd/changes.py` `load_rules(root)` reads only `.sdd/risk-rules.json`; `ci.py` calls it on the trusted base, `verify.py` and `assess()` on the working tree or a policy root.
- `scripts/sdd/install.py` lists `.sdd/ci.json` and `.sdd/risk-rules.json` under `PRODUCT`.
- `docs/manual/02-adoption.md` step 7 asks adopters to review the risk rules once the layout exists; no workflow step or record says when or where that happens.

Closed design decisions (ideation 2026-10-19, point 4, and the CHG-006 design discussion of the same day):

1. Split the rules: `.sdd/risk-rules.json` becomes framework-owned and holds only the four framework rules; when copying it to a product, the installer drops the patterns that exist only in the framework repository (`.agents/tools/**`, `.agents/adapters/**`). A new product-owned `.sdd/product-risk-rules.json` holds the four generic product rules as a starting point. The loader reads both and requires rule IDs to be unique across them; CI reads both from the base.
2. `.sdd/ci.json` becomes framework-owned and is replaced on upgrade. Project governance paths are CHG-007.
3. Path mapping: the plan of the first change that creates product code maps the real paths in `.sdd/product-risk-rules.json`, or states in one line why the generic patterns suffice. Documented in manual 02 step 7, the methodology, and the `plan` workflow; no automated check. No L2 path floors by default.

## Scope and non-goals

Includes:

- `.sdd/risk-rules.json` reduced to the four framework rules; new `.sdd/product-risk-rules.json` with the four generic rules, same patterns, levels, and reasons as today.
- `load_rules()` reading both files: the framework file is required; the product file is optional; both use the same schema and validation; a duplicate ID across files is an error.
- `.sdd/product-risk-rules.json` protected like the framework file: an L3 floor (`verification-controls`) and listed in `framework_paths` of `.sdd/ci.json` so CI routes it as framework policy.
- Installer: `.sdd/risk-rules.json` (filtered) and `.sdd/ci.json` move to framework-owned; `.sdd/product-risk-rules.json` is a product stub. An upgrade whose target `.sdd/risk-rules.json` contains rules beyond the shipped framework rules, while `.sdd/product-risk-rules.json` is missing, is refused with migration steps; the 1.0.0 migration steps include moving product rules.
- Path-mapping guidance in manual 02 step 7, the methodology, and the `plan` workflow; automation and verification docs that describe the rules file.
- CHANGELOG entry.

Does not include:

- Project-specific governance paths in `ci.json` or a product extension of `framework_paths` (CHG-007).
- Any automated check that product paths were mapped.
- Changing any rule's patterns, level, or reason, or adding L2 floors.

## Expected behavior

- Every path gets exactly the same floor as before this change, in this repository and in a product installed from it (except the framework-repository-only patterns, which do not exist in products).
- A product upgrade delivers new or changed framework floors and CI routing; the product's own floors stay as the product wrote them.
- The policy used by CI is still the base commit's: a PR cannot lower a floor by editing either file.

## Acceptance criteria

| ID | Scenario / precondition | Action | Observable outcome |
| --- | --- | --- | --- |
| AC-01 | This repository after the change | Load the rules | The union of both files equals the eight 1.0.0 rules (IDs, levels, patterns, reasons); the framework file has the four framework rules, the product file the four generic ones |
| AC-02 | A repository with both files; one with only the framework file; one with a duplicate ID across files; one with an invalid product file | `load_rules()` / `check-change-level` | Floors from both files apply; framework rules alone apply; duplicate is an error; invalid file is an error |
| AC-03 | A PR that removes a product floor in `.sdd/product-risk-rules.json` and touches that path | CI assessment with the base policy | The base floor still applies; the PR is assessed against it |
| AC-04 | A change touching only `.sdd/product-risk-rules.json` | `check-change-level --level L2` | Fails: L3 floor; CI routes it as framework policy |
| AC-05 | Fresh install | Run the installer | `.sdd/risk-rules.json` is the framework file without `.agents/tools/**` and `.agents/adapters/**`; `.sdd/ci.json` is the framework file; `.sdd/product-risk-rules.json` is created |
| AC-06 | Upgrade of a target with an edited `.sdd/product-risk-rules.json` and outdated framework `risk-rules.json` and `ci.json` | Run the installer | Framework files replaced; product rules file byte-identical |
| AC-07 | Upgrade of a target whose `.sdd/risk-rules.json` has rules beyond the shipped framework rules and no `.sdd/product-risk-rules.json` | Run the installer | Refused with steps to move those rules into `.sdd/product-risk-rules.json`; nothing written |
| AC-08 | Updated manual 02 step 7, methodology, `plan` workflow | Read them | The first change that creates product code maps real paths in `.sdd/product-risk-rules.json` or states why the generic patterns suffice |
| AC-09 | Repository at the end of this change | `scripts/check-docs`, `scripts/verify broad --target framework` | Pass |

AC-02, AC-03, and AC-07 are the boundaries: no floor is lost by the split, by a PR, or by an upgrade.

## Constraints and compatibility

- Property at risk: no path loses its floor (AC-01, AC-03).
- A product whose base still has the single 1.0.0-style file keeps using it in CI until the upgrade is merged; the base rules are a superset, so the transition is safe.
- Products installed before this change (only from unreleased 2.0.0 work) and 1.0.0 adopters migrate their product rules into the new file before upgrading (AC-07).
- Standard library only; the rules schema is unchanged.

## Uncertainties

None open. Design closed with the owner on 2026-10-19.

## Acceptance and next steps

Scope acceptance: accepted by Idaika Iglesias on 2026-10-19 (in conversation), with AC-01 to AC-09. Next: plan with strategy.

Related plan: [plan.md](plan.md). States and completion rules: [docs/specs/README.md](../README.md).

Upon completion, record evidence and delivery status in the plan. If another change replaces this behavior, reference that change without rewriting history.
