# 4. Verification and CI

This chapter explains how verification works mechanically: which tools exist, how to
register your checks, how to read the results, and what the optional CI gate adds.
The contracts are in [automation](../development/automation.md) and
[CI enforcement](../development/ci-enforcement.md); this chapter is a guided tour.

## Three local tools

| Tool | Answers | Never answers |
| --- | --- | --- |
| `scripts/check-docs` | Do the Markdown links and anchors resolve? Are specs and plans structurally valid? | Is the content true, complete, or really approved? |
| `scripts/check-change-level` | Given the changed paths, is the declared level at least the path-based floor? Do L2/L3 artifacts exist? | Is the change semantically low-risk? |
| `scripts/verify` | Did the registered checks for this scope pass, against which source snapshot? | Do those checks cover every AC and risk? |

All three are deterministic, use only the Python standard library, and never install,
commit, publish, or deploy anything. Agents use them through the `verify` workflow;
you can run them directly.

## Scopes and targets

**Scope** decides *how much* to check. It is cumulative:

```text
focused  = focused checks
standard = focused + standard checks
broad    = focused + standard + broad checks
```

The minimum scope follows the level (L0 focused, L1 focused or standard, L2 standard,
L3 broad). A higher scope is always allowed; a lower one never.

**Target** decides *what* is checked:

- `framework`: only the framework's own checks (documents, adapters, maintenance
  tests). Use it to confirm the framework is healthy.
- `product` (the default): framework checks plus your registered product checks. This
  is the only target that produces product evidence.

A product run with no product checks registered is `blocked`, not passed:

```text
Verification: blocked | target=product | scope=standard
  No product checks configured for this scope; framework checks cannot substitute
```

This is the most important guard in the framework: an empty suite can never look green.

## Registering your checks

Checks live in [`.sdd/verification.json`](../../.sdd/verification.json). Suppose the
library app is a Python service with a linter, unit tests, and slower integration tests:

```json
{
  "id": "lint",
  "kind": "product",
  "argv": ["{python}", "-m", "ruff", "check", "."],
  "timeout_seconds": 120
},
{
  "id": "unit-tests",
  "kind": "product",
  "argv": ["{python}", "-m", "pytest", "tests/unit", "-q"],
  "timeout_seconds": 600
},
{
  "id": "integration-tests",
  "kind": "product",
  "argv": ["{python}", "-m", "pytest", "tests/integration", "-q"],
  "timeout_seconds": 1800,
  "requires_env": ["TEST_DATABASE_URL"]
}
```

and the product profiles:

```json
"product": {
  "focused": ["lint", "unit-tests"],
  "standard": ["integration-tests"],
  "broad": []
}
```

Points to remember:

- `argv` is a list of arguments, never a shell string. `{python}` is replaced by the
  interpreter running the tool. For a component in a subfolder, add `"cwd"`.
- `requires_env` makes the check `blocked` (not failed, not skipped) when the variable
  is missing, so an unavailable database is reported honestly.
- Every selected check is required. There is no "optional" or "allow failure".
- Put each command in the README **Commands** table too: the README is the human
  registry, the JSON file the machine one.
- Changing this file is L3 under the default risk rules, because it changes what
  produces evidence.

Preview what a scope would run without executing anything:

```bash
python3 scripts/verify standard --base main --level L1 --dry-run
```

Every selected check is listed as `not_run`, and the run exits with 3. A dry run is
never evidence.

## Running a product verification

A product run needs an explicit base, the declared level, and the change ID for L2/L3:

```bash
python3 scripts/verify standard --base main --level L2 --change CHG-001-book-reservations
```

Before executing anything, the runner does a change check against that base. It lists
every changed path (committed, staged, unstaged, and untracked), applies the
[risk rules](../../.sdd/risk-rules.json), and refuses to run if the declared level is
below the floor:

```text
Declared L1 is below detected minimum L3; reclassify before continuing
Level L3 requires at least broad verification
L2/L3 requires --change with its paired spec.md and plan.md
```

Path rules only raise the level. A change that matches no rule is not certified as
low risk; the level still comes from your own classification.

## Reading the results

The runner prints a summary and an exit code:

| Exit | Meaning | What to do |
| --- | --- | --- |
| 0 | All selected checks passed. | Record the evidence. This is not approval. |
| 1 | A check or a mechanical rule failed. | Fix the cause; do not weaken the check. |
| 2 | Invalid input or configuration. | Fix the command line or the JSON file. |
| 3 | Blocked: missing tool, environment, base, or checks; dry run; no changes. | Record it as blocked with its impact, or resolve the prerequisite. |
| 130 | Interrupted. | Run again. |

Each run also writes a JSON report to the ignored `.sdd/results/` directory. It
contains the status, every check with its argument list, exit code and duration, the
change-gate result (base, paths, declared and detected levels), the environment, and
fingerprints of the sources before and after the run. If the sources changed while the
checks were running, a clean result is invalidated and the run must be repeated.

The report deliberately does **not** contain raw output, environment values, or any
claim of readiness, review, or deployment; those fields say `not-assessed`. Keep the
report locally. What goes into Git is a short summary in the plan's
*Completion evidence* section (or in the commit or PR for L0/L1), for example:

```text
| AC-01, AC-02 | Passed | verify standard at 3f2c9e1 against main; unit-tests 42 passed. |
| AC-03 | Blocked | integration-tests needs TEST_DATABASE_URL; not available locally. Run in CI. |
```

## Is the evidence good enough?

A green run proves that the commands passed. Whether they prove the AC is a judgment
the plan, the `verify` workflow, and the reviewer must make. Ask:

- Does a test actually exercise each AC, including the failure cases?
- For a bug, did the regression test fail before the fix?
- For a migration, contract, permission, or performance requirement, is there a check
  that really exercises it, not only unit tests around it?
- Did the evidence run against the final diff, after the last edit?
- Are blocked and not-run checks visible, with their impact?

The [risk checks reference](../../.agents/references/risk-checks.md) lists the
questions for each kind of risk.

## The CI gate

The optional GitHub Actions workflow runs the same tools on every pull request, but
with one crucial difference: **the policy comes from the base branch, not from the
pull request**.

```text
PR opened or updated
  │
  ├─ sdd-policy   reads PR metadata; classifies the paths with the BASE risk rules
  │               and routing policy; checks CODEOWNERS in both revisions
  │
  ├─ sdd-verify   runs the BASE runner with the BASE check registry
  │               against the PR's test merge
  │
  └─ sdd-gate     succeeds only if both jobs explicitly succeeded
```

Because of that, a pull request cannot lower its own risk floor, remove a check it
does not like, or register its own first product check for its own run. Those changes
take effect only after they are reviewed and merged.

### What the PR declares

The [PR template](../../.github/pull_request_template.md) has one machine-readable block:

```text
<!-- sdd:metadata -->
Change-Level: L2
Change-ID: CHG-001-book-reservations
<!-- /sdd:metadata -->
```

`Change-ID` is `none` for L0/L1. Editing the block starts a new assessment. In CI,
L1 always runs `standard` (see [`.sdd/ci.json`](../../.sdd/ci.json)).

### How a PR is routed

- If every changed path is a framework path, the target is `framework`.
- If every changed path is a Markdown document under `docs/` or the README, the PR is
  **design-only**: you can merge a brief, a draft spec, or an ADR without an
  implementation or product checks.
- Anything else is `product`, and needs registered product checks to pass.

### What CI cannot do on its own

CI produces a status. Blocking a merge is the job of a GitHub ruleset that requires
`sdd-gate`, a human approval, and code-owner review. A workflow file can also be
changed by the pull request itself, which is why `.github/` must be owned by
independent code owners. Until the ruleset is active and has been tested with failing
pull requests, describe enforcement as "not active", even if every check is green.
The ordered steps and the negative scenarios are in the
[activation sequence](../development/ci-enforcement.md#activation-sequence).

A green `sdd-gate` never replaces the required human review, and for L3 it never
replaces the independent review.

## Next

The next chapter covers the agent side: using the workflows in each client and
qualifying a client before relying on it.
