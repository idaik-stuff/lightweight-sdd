# Deterministic automation

Framework version `1.0.0`. This layer executes local checks; it does not replace the
five workflows, acceptance criteria, independent review, or human authorizations. No
application stack is assumed. The supplied executable checks verify the framework itself.

Contents: [requirements](#requirements), [commands](#three-entrypoints),
[configuration](#verification-configuration), [risk](#risk-floors-and-git-scope),
[documents](#document-checks), [evidence](#results-and-evidence),
[safety](#execution-boundaries), [extension](#connecting-the-product),
[CI boundary](#ci-boundary), [sources](#technical-basis),
[trusted policy](#trusted-policy-execution-in-ci).

## Requirements

Python 3.10+ is the syntax target; Git is required for change checks and product runs.
The tools use the standard library only. The entrypoints resolve
the repository from their own location; `--root` can explicitly select a fixture or
another repository. They do not search arbitrary parent directories for instructions.

## Three entrypoints

| Entry | Mechanical responsibility | Does not establish |
| --- | --- | --- |
| `scripts/verify` | Validate configuration, select required checks, run them, record outcomes and source fingerprints. | AC sufficiency, authorization, independent review, readiness, deployment. |
| `scripts/check-docs` | Check local Markdown links/anchors and change-record structure. | Truth, completeness, valid human approval, external URL availability. |
| `scripts/check-change-level` | Compare explicit Git scope with conservative path rules and declared level; require applicable artifacts. | Semantic risk classification or a trusted enforcement boundary. |

The existing `.agents/tools/sync_adapters.py` remains the adapter generator and drift
checker. There is no new wrapper, classifier Skill, verification Skill variant, or
mandatory per-change JSON file. The plan remains the evidence summary for L2/L3.

### Run now

```bash
python3 scripts/check-docs
python3 scripts/verify focused --target framework
python3 scripts/verify standard --target framework
python3 scripts/verify broad --target framework
```

Focused framework checks cover documentation and adapter drift. Standard adds both
maintenance test suites. Broad inherits standard; the starter has no additional broad
framework checks. These modes do not invent integration or product tests.

For one documentation edit, use selected paths and inspect the actual diff:

```bash
python3 scripts/check-docs docs/product/brief.md
```

### Product verification

The default target is `product`. The template registers no product checks, so a
product run is `blocked` until you [connect the product](#connecting-the-product).
A product run requires configured product checks, an explicit base, a declared level,
and the change ID for L2/L3. For example, after replacing the placeholders:

```bash
python3 scripts/verify standard --base BASE_COMMIT --level L1
```

```bash
python3 scripts/verify standard --base BASE_COMMIT --level L2 --change CHANGE_ID
```

Missing product checks never become a framework-only pass. Selecting `--target
framework` is an explicit limitation of the claim, not a workaround for product gates.
An optional base/level can also be supplied to a framework run when checking a specific
framework change. Otherwise that run is a framework health check, not change clearance.

## Verification configuration

[`.sdd/verification.json`](../../.sdd/verification.json) is the machine source of truth.
The root [README](../../README.md#commands) documents entrypoints, not duplicated
check lists. Review changes to the configuration as executable code.

A check has an ID, `kind` (`framework` or `product`), an `argv` string array, and a
positive `timeout_seconds` up to 86400. Optional `cwd` is repository-relative and must
exist; optional `requires_env` lists variable names whose nonempty values are required.
Missing executables or required environment values produce `blocked`.

The exact argument `{python}` is replaced with the interpreter running the tool.
There is no shell expansion, automatic dependency installation, `.env` loading,
package-manager detection, credential acquisition, or automatic test discovery.
Arguments containing spaces remain individual arguments. Deliberately invoking a
shell or an unsafe executable remains possible in trusted configuration: this is
not a sandbox or a command allowlist.

Profiles are cumulative additions, not complete replacement lists:

```text
focused  = focused entries
standard = focused entries + standard entries
broad    = focused entries + standard entries + broad entries
```

Do not repeat inherited IDs. IDs must be unique; unknown fields, missing modes,
unknown checks, wrong kinds, invalid timeouts, and duplicate JSON keys are errors.
All selected checks are required. There is no `optional`, `allow_failure`, quiet
skip, or per-run switch to drop a required registered check.

A product run selects the matching cumulative framework and product profiles. At
least one actual product check must be selected. This guard prevents an empty suite
from passing; it cannot determine whether an inadequate registered command genuinely
covers the product. The plan and reviewer must still assess that coverage.

Dry runs validate configuration and show selected checks without executing them:

```bash
python3 scripts/verify standard --target framework --dry-run
```

A dry run returns `not_run`, exit 3. It is not verification evidence. Preconditions
such as missing product configuration can instead leave it `blocked`.

## Risk floors and Git scope

[`.sdd/risk-rules.json`](../../.sdd/risk-rules.json) supplies conservative starter path
rules for public contracts, permission boundaries, migrations, delivery configuration,
and verification controls. Each rule has an ID, a minimum level, path patterns, and a
reason. Adjust these patterns to the actual repository during adoption; they are not
an exhaustive catalog of its risks. Editing verification controls is intentionally
review-sensitive in the starter.

```bash
python3 scripts/check-change-level --base BASE_COMMIT --level L1
python3 scripts/check-change-level --base BASE_COMMIT --level L3 --change CHANGE_ID --scope broad
```

Replace `BASE_COMMIT` with the intended baseline; the tool never assumes `main`,
`master`, a PR target, or a merge base. `HEAD` is appropriate only when the intended
scope is uncommitted changes. To assess a whole feature branch, choose its intended
integration baseline instead. No network fetch or branch switch is performed.

The comparison includes committed differences from that base plus current working
changes, staged changes, and non-ignored untracked files. Deleted paths are retained.
Rename detection is disabled, so both the old and new paths are risk-checked; moving
a sensitive file out of a directory cannot hide its original location. A staged
change masked by an opposing unstaged edit is conservatively retained too.

Patterns use case-sensitive Python `fnmatchcase` on slash-separated paths. Wildcards
can match slash characters; a leading `**/` also matches the repository root. This is
a small documented matching rule, not Git pathspec or gitignore syntax. Rules only
raise floors. A non-matching change is not certified L0: the declared level remains,
and semantic risks must still be assessed under [AGENTS.md](../../AGENTS.md).

A declared level below the floor fails. L2/L3 requires a paired spec/plan and matching
spec level. An optional scope is checked against the minimum: standard for L2,
broad for L3. Structural checks do not authenticate the approval or declare a draft
ready for implementation. No-change comparisons return `blocked`, not a vacuous pass.

Invalid bases, unresolved merges, submodule repositories, and `assume-unchanged` or
`skip-worktree` indexes produce errors rather than silently incomplete evidence.
Changes inside ignored files are not enumerated. Product verification requires a
Git repository with a resolvable base; archive-only framework checks need no Git.

## Document checks

Default scope is root Markdown plus `docs/`, `.agents/`, and `.claude/`. Explicit path
arguments narrow the scan. `--json` prints a machine-readable result; `--change ID`
adds structural validation of that change record.

The Markdown checker supports simple inline links/images, reference definitions,
repository-root-relative links, percent-encoded paths, and ATX headings with duplicate
heading suffixes. Fenced and inline code are excluded from link scanning. Explicit
HTML anchor IDs are recognized. Links outside the repository are rejected.

This is deliberately not a full Markdown renderer. Reference usage resolution,
complex/nested destination syntax, setext headings, arbitrary HTML links, external
URLs, and code-formatted paths are not exhaustively validated. Use the supported
subset for framework navigation; adopt a full parser if the repository needs more.

Specs and plans follow their [templates](../templates/spec.md) and states. Mechanical checks include
valid levels/statuses, a concrete level rationale, unique AC IDs, plan verification
mappings, and obvious contradictions in accepted/completed metadata. Product and
architecture template placeholders are allowed. The checker never fills them in.

A draft or approved spec can exist before planning. While its plan is absent, leave
that reference pending as plain text, not as a broken Markdown link. Product-change
verification requires both files. This preserves `spec -> plan` rather than forcing
an invented plan merely to pass a drafting check.

For accepted specs/plans, recorded acceptance fields cannot still be placeholders.
For completed plans, version/diff evidence and AC references cannot be missing and
obvious unresolved result rows fail. These are structural checks, not evidence that
the named person approved anything or that a test actually satisfied an AC. Arbitrary
prose about blockers, exception legitimacy, and review findings still needs judgment.

## Results and evidence

| Exit code | Meaning |
| --- | --- |
| 0 | Selected mechanical checks passed; not a release or approval decision. |
| 1 | A required check or mechanical constraint failed. |
| 2 | Invalid input/configuration, unavailable Git context, or evidence error. |
| 3 | Blocked prerequisites, unavailable command/environment, timeout, no changes, or dry run. |
| 130 | Verification interrupted by the operator. |

Each verification invocation attempts to create a uniquely named JSON report under
ignored `.sdd/results/`, without overwriting earlier evidence. Reports contain target,
mode, UTC times, environment version/platform, commands, exit statuses, durations,
preflight results, and source fingerprints. They do not capture raw process output,
environment values, credentials, or a claim of approval/review/deployment. Command
arguments are recorded, so never put secret values in arguments or configuration.

Known failed checks dominate blocked outcomes; missing checks cannot turn success
into a complete pass. Interruptions are explicit. A source/index change during the
checks invalidates a clean result and requires rerunning against the final snapshot.
A failure remains a failure even when evidence also became stale.

Git fingerprints include tracked and non-ignored untracked files, file content and
executable mode, symlink target strings, HEAD, and index metadata. Ignored local
results are excluded; tracking files under `.sdd/results/` is rejected. Archive-mode
fingerprints cover delivered framework paths and state that no Git base exists.
This is best-effort change detection, not an atomic filesystem snapshot or an
attestation: dependency caches, ignored inputs, external services, and environment
changes require additional provenance when material to a check.

Review the report and preserve the necessary summary in `plan.md` or the existing
L0/L1 change record. Reports are local working evidence, not a new required Git
artifact. The CI adapter adds bounded artifact retention and a recorded base-policy snapshot; see [CI enforcement](ci-enforcement.md).

## Execution boundaries

The runner executes reviewed argument arrays without `shell=True`, inherits the
local environment, supplies no interactive stdin, and applies per-check timeouts.
On POSIX it starts a separate process group and attempts to kill that group on timeout
or interruption. This does not contain detached children or replace a sandbox.
Windows process-tree behavior has not been validated; direct `.cmd`/`.bat` entrypoints
are blocked and need a reviewed platform adapter.

Child stdout/stderr goes to the terminal and may contain sensitive output from the
underlying tools. It is not automatically redacted. The runner does not automatically
install dependencies, rewrite failing snapshots, auto-fix code, commit, publish,
access production, or deploy. Configured commands can still have those effects if
misconfigured: inspect them first, and use permission controls and isolated execution
for untrusted changes. A timeout cannot undo side effects already performed.

## Connecting the product

Keep this order: choose the real stack and supported environments; establish actual
lint/type/test/build commands; add those commands as `kind: product`; assign them to
the relevant cumulative profiles; run and inspect the result against an explicit base.
Use regression and contract/migration/security checks when the actual risk warrants
them. Do not add invented commands just to make the product profile nonempty.

Use `cwd` for a component when needed. The first implementation intentionally has no
automatic changed-component selection or test-dependency graph. Configure a safe
baseline first; add narrower selection only when it can be validated without silently
missing shared dependencies. High-impact checks and manual AC remain plan-specific.

The `verify` Skill selects scope and evaluates coverage; the runner executes registered
checks. The separate reviewer receives initial evidence. After corrections, rerun
checks and review material changes before closing the workflow. Passing this runner
does not bypass any of those gates.

## CI boundary

The local tools alone do not activate branch protection or merge requirements. They
are editable and do not form a trusted security boundary; no `--force` waiver is
provided. The framework adds a [GitHub Actions adapter](ci-enforcement.md) using base-commit
policy, restricted jobs, and ownership prerequisites. Its workflow and required
reviews still need server-side protection before mandatory enforcement can be claimed.

## Technical basis

External primary documentation checked on 2026-09-27:

- Python subprocess arguments, timeouts, environment, and security notes:
  `https://docs.python.org/3/library/subprocess.html`.
- Git diff scope, NUL-separated filenames, rename control, and external diff controls:
  `https://git-scm.com/docs/git-diff`.
- Git tracked/untracked enumeration and standard exclusions:
  `https://git-scm.com/docs/git-ls-files`.

These sources describe underlying interfaces. Product guarantees and measured test
results come only from actual execution.

## Trusted policy execution in CI

Normal local invocations retain the behavior above. The CI adapter adds `scripts/check-ci`, `scripts/check-ci-setup`, and optional `scripts/verify --policy-root PATH` when running the verifier from that trusted checkout. The external policy supplies risk rules and the check registry; the candidate remains the execution root. The evidence report includes the policy snapshot. Archive inventory and default Markdown discovery also include `.github/`. See [CI enforcement](ci-enforcement.md) for the complete contract and bootstrap restrictions.
