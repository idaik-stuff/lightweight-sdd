# Maintenance

This guide is for whoever maintains the framework: in a product that installed it,
and in the upstream framework repository itself. Day-to-day product work is covered by the
previous chapters.

## Versions

The framework uses semantic versioning. The version appears in the header of the
[README](../../README.md), the [methodology](../development/methodology.md),
[workflow usage](../development/workflows.md), and [automation](../development/automation.md),
and each release is described in the upstream `CHANGELOG.md`.

| Change | Version |
| --- | --- |
| Rule, gate, artifact, configuration schema, or command interface that adopters must adapt to | Major |
| New capability that existing adopters can ignore (a new optional check, a new client adapter) | Minor |
| Corrections, wording, and fixes that do not change behavior | Patch |

## Upgrading an adopting repository

Upgrade with the installer, from a checkout of the target framework release:

```bash
git -C ../lightweight-sdd checkout v2.1.0
python3 ../lightweight-sdd/scripts/install --target . --dry-run
python3 ../lightweight-sdd/scripts/install --target .
```

Run it on a clean change branch of the product. It replaces only framework-owned files
(including `.sdd/risk-rules.json` and `.sdd/ci.json`; keep your floors in
`.sdd/product-risk-rules.json`, moved in the same pull request as the upgrade, and the installer
refuses an upgrade that would drop one),
keeps the clients recorded in `.sdd/install.json` unless you pass `--clients`, creates
product files that are missing, and lists files it no longer ships as orphans. Then:

1. Read the CHANGELOG entries between the two versions.
2. Review the diff; remove orphans in the same reviewed change if you agree.
3. Run the standard framework verification.
4. Rerun the compatibility trials for your clients if workflows or adapters changed.
5. Merge through the normal process. Framework upgrades are L3 under the default risk
   rules.

A repository adopted from 1.0.0 (template or manual copy) has no `.sdd/install.json`.
The installer refuses it until it is migrated: move any rules added to `AGENTS.md` into
`docs/project-rules.md`, move product floors from `.sdd/risk-rules.json` into
`.sdd/product-risk-rules.json`, remove the `adapters` and `adapter-tests` checks from
`.sdd/verification.json`, delete `.agents/tools/` and `.agents/adapters/`, commit, and run
the installer with `--clients`. Its orphan list then names every file in the directories
of clients you did not choose (for example `.github/agents/` or `CLAUDE.md`), including
any you wrote yourself: keep those.

### When the CI gate is already active

The gate evaluates each pull request with the policy from its **base**. An upgrade
that changes the policy itself cannot rely on its own new version during its own run.
This matters when an upgrade:

- adds new framework paths to `.sdd/ci.json` (for example a new client folder);
- changes the protected CODEOWNERS block that `check-ci-setup` requires;
- replaces or renames a registered check.

In those cases, split the upgrade into two reviewed L3 changes:

1. **Prepare the base.** Register the new paths, and make the ownership check accept
   both the old and the new protected block (complete blocks only, never partial
   coverage). For a renamed check, add the new one while keeping the old one working.
   Merge it.
2. **Land the upgrade** on top of that base. Remove the transitional acceptance and the
   old check.

Never disable the gate, point it at the candidate's policy, or bypass required reviews
to get a structural migration through.

## Changing the framework

In a product, framework-owned files are replaced by every upgrade and the generator
is not installed: put project-specific agent rules in `docs/project-rules.md`, change
product-owned configuration (`.sdd/*.json`, README commands) locally, and propose
changes to workflows, templates, or scripts upstream. The table below is for the
framework repository, where every framework file is protected by the risk rules and,
when CI is active, by the CODEOWNERS block; changes go through the L3 route.

| To change | Edit | Then |
| --- | --- | --- |
| A workflow procedure | `.agents/workflows/<workflow>/SKILL.md` | Regenerate adapters; rerun the behavior scenarios. |
| Shared workflow detail | `.agents/references/` | Rerun the affected scenarios. |
| Skill names, descriptions, reviewer tools | `.agents/adapters/clients.json` | Regenerate; update tests if the generator's expectations change. |
| The review procedure | `.agents/review/independent-review.md` | Rerun compatibility trials C09–C12. |
| Risk floors | `.sdd/risk-rules.json` (framework), `.sdd/product-risk-rules.json` (starter product floors) | Run `check-change-level` on a few representative changes. |
| Check registry | `.sdd/verification.json` and `docs/development/commands.md` | Run each changed scope once. |
| CI routing | `.sdd/ci.json` | Run the automation tests; observe a real PR. |
| Permanent agent rules | `AGENTS.md` | Keep it short; rerun compatibility trial C01. |

Regenerate and check the adapters with:

```bash
python3 .agents/tools/sync_adapters.py
python3 .agents/tools/sync_adapters.py --check
```

Never edit generated adapter files directly. The generator refuses to overwrite files
it does not own and never deletes anything; remove obsolete files explicitly.

## Periodic checks

- **Pinned actions.** Review updates to the actions pinned in `sdd.yml` as control
  changes: read the release, update the SHA and its comment, and observe a real run.
  Do not let a bot merge them without review.
- **Client documentation.** The [compatibility guide](../development/agent-compatibility.md)
  and [workflow usage](../development/workflows.md) cite the client documentation they
  were checked against, with dates. Clients change quickly: recheck those sources and
  rerun the trials when you upgrade a client.
- **Python.** The tools target Python 3.10 or later and the standard library only. CI
  runs a pinned newer version; test the minimum version occasionally.
- **Platform tests.** Four automation tests run only on POSIX systems (process groups,
  executable bits, newline file names, the bash gate). On Windows they are skipped;
  CI on Linux runs them.

## Maintaining the upstream framework repository

The upstream repository uses its own process: L2/L3 changes have a spec and plan under
`docs/specs/`. The installer never ships `docs/specs/CHG-*`, so products do not inherit
them. In addition:

- Every change goes through a pull request with a clear description and its checks.
- The `sdd.yml` gate is skipped in the upstream repository (see the
  [execution model](../development/ci-enforcement.md#execution-model)), because
  upstream has no real code owners for adopters to inherit. Run the standard
  framework verification and both test suites locally on every pull request and
  report the result in it.
- `CHANGELOG.md` records each release; the version strings listed above are updated
  together.
- Before a release, run the standard framework verification and both test suites, and
  check that `docs/product/`, `docs/architecture/`, `docs/adr/`, and
  `docs/project-rules.md` still contain only placeholders (the installer copies them as
  product stubs).
- Keep the [worked example](example/README.md) consistent with the templates: it is
  validated as a completed spec and plan when copied into `docs/specs/`.
- Keep project-specific content out of the shipped files: no product names, real
  people, or real infrastructure.
