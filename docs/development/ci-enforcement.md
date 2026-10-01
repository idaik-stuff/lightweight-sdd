# CI enforcement and activation

The framework supplies one GitHub Actions adapter over the stack-neutral
verification tools. Its files are ready; remote enforcement is **not activated
by creating a repository from this template**. Real reviewer identities and
GitHub settings are supplied by each adopting repository.

Contents: [execution](#execution-model), [declarations](#pr-declarations),
[trust](#trust-boundaries), [activation](#activation-sequence),
[product checks](#registering-product-checks), [operations](#operational-boundaries),
[references](#official-references).

## Execution model

```text
PR event and exact test merge
    |
    v
sdd-policy: base-commit Python and policy; inspect candidate as data
    |        + ownership-file prerequisites in both revisions
    v
sdd-verify: base runner and check registry; execute checks on candidate
    |
    v
sdd-gate: both jobs must explicitly succeed
    |
    v
GitHub ruleset: current human approval + code owners + required gate
```

The [workflow](../../.github/workflows/sdd.yml) has no path or branch filters.
It handles opened, synchronized, reopened, edited, and ready-for-review PRs.
An edit to the PR declaration starts a new assessment. New runs cancel older
runs for that PR. Cancellation, a skipped prerequisite, neutral results, and
failed checks do not count as successful inputs to the final gate.

The workflow has one job condition: `sdd-policy` and `sdd-gate` are skipped
only in the upstream template repository (`idaik-stuff/lightweight-sdd`), which
has no real code owners and therefore could never pass the ownership check. In a
repository created from the template the condition is always true, so the gate
still runs on every PR, including when its prerequisites fail or are skipped. You
may delete the condition after adopting; do not add any other condition.

Only `sdd-gate` should be the required status context. `sdd-policy` and
`sdd-verify` are visible diagnostic jobs. The final gate uses `always()` and
explicit result comparisons: GitHub can otherwise treat skipped jobs as
successful. See [GitHub's required-check guidance][checks].

The tested version is the PR's generated test merge, not an arbitrary current
branch. The assessor checks that the candidate HEAD is the event's expected
SHA and has exactly the event base and head as its two parents. It rejects a
stale merge, mismatched checkout, dirty checkout, or missing history rather
than substituting `HEAD~1` or comparing the wrong commits.

Changes are compared from the base to that merge. Deletions and both sides of
renames are included. This avoids classifying unrelated base-branch progress
as part of an out-of-date feature branch.

## PR declarations

The [PR template](../../.github/pull_request_template.md) contains exactly two
machine-readable fields:

```text
<!-- sdd:metadata -->
Change-Level: L2
Change-ID: CHG-001-example
<!-- /sdd:metadata -->
```

Use `Change-ID: none` for L0/L1. For an L2/L3 implementation, supply its actual
`docs/specs/<id>/` identifier. Duplicate blocks, duplicate fields, placeholders,
unknown fields, unsafe IDs, and extra target/skip declarations are rejected.
Values are never interpolated as shell commands.

The PR body is input, not authority. The base risk rules may raise the minimum
level; they never lower a declared level. A nonmatching path proves nothing
about semantic risk. A human still reviews the declaration and its rationale.
The report binds the event's declaration with a SHA-256 digest. This records
what was evaluated; it is not a server-side signature over future body edits.

### Scopes and targets

The base [CI policy](../../.sdd/ci.json) maps levels to scopes:

| Declared / required level | CI scope |
| --- | --- |
| L0 | focused |
| L1 | standard |
| L2 | standard |
| L3 | broad |

L1 uses standard in this adapter, although local methodology permits a focused
check when justified. This is a conservative CI default, not a fifth level.
Scopes remain cumulative and use the existing check registry. Broad has no
invented product, load, migration, or security tests.

The author cannot request a framework-only exemption. All changed paths must
match the base policy's framework allowlist to select `framework`; an unknown
path selects `product`. Until product checks are registered in the base,
product verification cannot pass. A PR that adds application code and adds
its own first product-check registration does not authorize that registration
for its current run.

The allowlist is a practical routing heuristic, not proof that a file contains
no executable content or product logic. Reviewers must not permit business
code to be hidden in an allowed automation or documentation directory.

### Documentation proposals and implementation

If every changed path is an allowed Markdown design/documentation path,
the assessment marks the PR `design_only`. This supports committing a brief,
draft spec, approved spec awaiting a plan, architecture proposal, or ADR
without creating a fictitious implementation record.

Document-only PRs still receive risk classification, structural documentation
checks, the appropriate scope, and required human review. A missing plan must
be described as pending text, not as a broken Markdown link. An explicit
Change-ID is validated when supplied; `none` is allowed for a design-only PR.
No source-code path can use this exemption.

For L2/L3 implementation, both the spec and plan must exist. The spec must be
`approved` or `implemented`; the plan must be `approved`, `in-progress`, or
`completed`. The local structural checks remain applicable. CI does
not require a completed plan before it has produced the first verification
evidence, and it does not mark a change implemented or deployed automatically.

## Trust boundaries

### Base policy versus candidate code

The assessor and its imports run from a separate checkout of the PR base
commit. It reads the base risk rules, CI routing policy, and registered
verification commands. It inspects candidate Markdown and configuration as
data, without importing candidate Python modules or running candidate tools.
Python isolated mode and explicit package paths prevent candidate modules
from being selected through the current directory or `PYTHONPATH`.

The verification job invokes the base runner with `--policy-root` pointing to
that same checkout. The candidate remains the execution root. The command
list is taken from the base registry, not the candidate's revised registry.
Reports retain the policy snapshot as well as the candidate snapshots. The
CLI refuses an external policy path that does not contain the executing
runner. Local runs without this option use the candidate's own policy.

A candidate may legitimately change test implementations. Its test code is
therefore still untrusted code executed in the verification job. Reading the
base command list does not make candidate tests honest or sufficiently
complete, and the runner is not a sandbox. Deliberately weakened assertions,
malicious test commands, and false acceptance text need independent review.

### The workflow itself also needs protection

A `pull_request` workflow is not an immutable authority: its proposed YAML
can be changed by the PR. Reading base policy alone does **not** prevent an
author from proposing a replacement workflow that simply reports success.
The protected ownership block covers `.github/`, the tools, policies, agent
instructions, and methodology files. GitHub uses the base branch's CODEOWNERS
for PR ownership decisions. Activate required code-owner reviews, dismissal
of stale approvals, and approval of the last reviewable push. See [code
owners][owners] and [protected branches][branches].

The baseline therefore assumes responsible repository administrators and
independent code owners. Repository contributors with sufficient privileges,
compromised administrators, a trusted approver colluding with an author, and
forged same-name checks are not solved by this repository's scripts. A status
context identifies a check name, not a cryptographically unique workflow.
Choose the expected GitHub Actions source when configuring the required
check, but that still does not distinguish two workflows from the same app.

For stronger organizational separation, use an organization-required workflow
from a separately administered governance repository where that feature is
available. Configure and test it at the organization level; this package does
not silently claim to have created one. See [ruleset workflow guidance][rules].

### Permissions and execution environment

The shipped workflow uses `pull_request`, not `pull_request_target` or
`workflow_run`. It requests only `contents: read`; the final gate requests no
token permissions. Checkout does not persist credentials. No user secrets,
environments, deployments, caches, remote write operations, self-hosted
runners, or artifact-to-code execution are configured. Candidate commands
must never be moved into a privileged event merely to make a secret-dependent
test pass. See [GitHub's secure-use guidance][security].

Actions are pinned to full upstream commit SHAs, with release comments for
review. Python 3.13 and `ubuntu-24.04` are CI infrastructure choices, not the
application stack. Both hosted runner images and interpreter patch versions
can change. The report records the actual interpreter and operating system;
this is not a completely reproducible software supply chain.

## Activation sequence

### 1. Review and integrate the framework

Create the repository from the template, or merge the framework deliberately
into an existing repository. Run:

```bash
python3 scripts/verify standard --target framework
```

No product commands are configured. Do not use this framework-only success as
product evidence.

### 2. Configure real ownership before activation

Copy `.github/CODEOWNERS.example` to `.github/CODEOWNERS` and replace every
placeholder with a real account or visible organization team that has write
permission. Add product ownership above the protected block; keep that block
last and in its supplied order. GitHub's own CODEOWNERS UI/API must confirm
that the owners exist and have the necessary access.

```bash
python3 scripts/check-ci-setup
```

The unconfigured distribution intentionally exits **3** with `blocked`.
After local configuration it can report `local-files-ready`, but always
reports `remote_enforcement: not-checked`. It cannot verify account existence,
team visibility, permissions, or branch protection from local files.

The workflow runs this check on both the trusted and candidate revisions.
Removing owners or replacing them with placeholder entries cannot pass that
unchanged workflow. This structural check does not prove the proposed owner
is an appropriate independent reviewer.

### 3. Establish the initial trusted version

The first installation has a bootstrap boundary: a PR cannot substitute its
own new policy when the base lacks `scripts/check-ci` and `.sdd/ci.json`. A
repository created from the template has them in its initial commit. When
adopting into an existing repository, the PR that adds the framework cannot
validate itself through the trusted-base path.

Review that installation under the repository's existing governance, run
local checks, and have a responsible independent reviewer inspect it.
Establish the framework and the real CODEOWNERS on the intended base before
making the new status mandatory. Do not weaken unrelated existing protections
or introduce a permanent bootstrap flag. The bootstrap is not a live CI test.

### 4. Run a controlled PR

Open a small PR with the metadata block after the trusted base exists.
Confirm that the correct base, head, and merge SHAs are recorded; inspect the
policy result, verification report, ownership requests, and `sdd-gate` result.
A merge-conflicted PR cannot obtain a successful test-merge run. Resolve the
conflict rather than changing the workflow to test an unrelated commit.

### 5. Activate GitHub rules

Review `.github/sdd-ruleset.template.json` and import or reproduce it in
Settings -> Rules -> Rulesets. Its `enforcement` is deliberately `disabled`;
a committed JSON file does not create or activate a remote rule. Set it to
Active only after checking ownership and a real workflow run. Availability
and administration depend on the repository and GitHub plan; see [creating
rulesets][create-rules].

The template targets the default branch and requests one approving human
review, code-owner review, dismissal of stale approvals, approval of the most
recent reviewable push, resolved review conversations, a current `sdd-gate`,
and prohibition of force pushes and deletion. There are no bypass actors.
Select the expected check source in the UI after the check exists. Do not
copy a guessed GitHub App installation ID into the template.

One human approval is a deliberate team baseline for every PR, including
L0/L1. It does not impose feature artifacts on a typo. L3 still needs the
substantive independent review defined by the methodology. A model reviewer
can assist but cannot impersonate a GitHub human approval. A solo maintainer
needs an eligible independent reviewer or an explicitly reviewed alternative
policy; the package does not silently grant a self-approval exception.

### 6. Prove that the platform blocks bad merges

Before declaring enforcement active, run these scenarios on the live
repository. Keep each one pending until actual platform evidence exists:

| Scenario | Required observation |
| --- | --- |
| Valid documentation typo | Focused framework checks; green gate; required human review. |
| Missing/duplicate metadata | Policy failure and blocked merge. |
| Known L3 path declared L0/L1 | Base risk floor retained; blocked merge. |
| Product code without registered checks | No framework-only bypass. |
| Change own risk rules or allowlist | Current run uses base policy. |
| Candidate removes configured check | Current run still selects the base check. |
| Failing test / missing command / timeout | No successful final gate. |
| Skipped or cancelled prerequisite | No successful final gate. |
| Metadata edited after a result | New assessment corresponds to the new declaration. |
| New head or changed test merge | Old evidence does not satisfy current checks. |
| Unreviewed workflow or ownership edit | Required base code-owner review blocks merge. |
| New push after approval | Stale approval dismissed; current approval required. |
| Fork PR | Read-only permissions, no user secrets; expected approval policy. |
| Conflicted PR | No unrelated-commit verification; resolve before merge. |
| Missing artifact | Upload failure is visible and prevents a successful gate. |
| Ruleset bypass / direct push attempt | Default-branch protection behaves as configured. |

Record the observed results in your repository's change record. Do not mark these
steps complete from local unit tests alone. Independently inspect the workflow's own
ability to change required checks: a repository-local workflow plus same-name status
requirements is not a substitute for separately administered governance when that
threat matters.

### When the platform cannot enforce the rules

Rulesets and required reviews are not available on every repository and plan (for
example, some private repositories on free plans). The checks still run and report,
but nothing blocks a merge. Record that state honestly, for example:

| Control | Status |
| --- | --- |
| `sdd-policy`, `sdd-verify`, `sdd-gate` CI checks | Operational |
| CODEOWNERS configuration | Configured |
| Required `sdd-gate`, required approvals, merge blocking | Not enforced by platform |

Until enforcement becomes available, apply a written operating policy:

- Every change is submitted through a pull request.
- Do not merge a pull request unless `sdd-gate` is successful.
- A green `sdd-gate` does not replace required human review.
- L3 changes still require the independent review defined by the methodology.
- The ability to merge manually is not evidence that the gates were satisfied.
- If a gate must be bypassed in an emergency, use the authorized exception
  procedure in the methodology; do not treat the change as verified.

The absence of merge blocking is a platform limitation, not a successful
enforcement result. When enforcement becomes available, complete steps 5 and 6
and update the recorded state from what you observe. If you also deploy
automatically, the same plan limits affect deployment; see the
[continuous deployment recipe](../manual/recipes/continuous-deployment.md#a-private-repository-on-github-free-what-is-missing-and-why-it-matters).

## Registering product checks

Keep real setup, lint, types, unit/integration/contract tests, migration checks,
and risk-specific checks in `.sdd/verification.json`. The commands must be
reviewed, noninteractive, bounded, and appropriate for the environment.
Nothing in this release selects npm, uv, Maven, Docker, a database, or a cloud.

The template begins with no product checks. Adding or changing a check is a
reviewed framework/configuration change (L3 under the default risk rules). Use
`--dry-run` when a command cannot run in the current environment; never claim that it
passed. Record any remaining prerequisite explicitly.

To change a check interface, keep the old base command working for the
transition PR. Add the replacement without removing the old command, accept
the registry transition, and remove the old interface in a subsequent change.
Do not fall back to candidate policy merely because the trusted command fails.

The workflow supplies no secret-based installation step. Add a separately
reviewed strategy for private dependencies or credential-dependent integration
tests; those checks remain blocked until that exists. The current artifact
upload captures reports, not arbitrary directories or the whole workspace.

## Operational boundaries

**Evidence.** Policy and verification JSON artifacts are requested even after
failure, with 14-day retention. Missing reports fail the upload step. Only
the ignored verification-report directory is explicitly included as hidden
content. Reports from candidate execution are evidence, not authenticated
attestations. Do not put secrets in command arguments, source paths, reports,
or stdout. Keep the durable, reviewed result in the plan/change record before
short-lived artifacts expire. Upload behavior is documented upstream in
[upload-artifact][artifacts].

**Urgent changes.** A label or PR checkbox cannot bypass these jobs. Use the
existing emergency procedure and explicitly authorized platform governance
when required; record a deferred gate as an exception, not a passed check.
This package does not automate administrative bypass.

**Unsupported modes.** This adapter deliberately does not support merge
queues, push/release/deployment validation, GitHub Enterprise Server-specific
actions, sparse checkouts, Git LFS product data, symlinks, submodules, Windows
runners, or persistent self-hosted runners. Do not enable a merge queue until
an adapter for `merge_group` and aggregated change metadata is implemented
and tested. GitHub notes that missing merge-group triggers prevent required
queue checks from being reported [in its ruleset guidance][rules].

**Updates.** Review pinned action upgrades as control changes. Do not have a
bot rewrite them and merge automatically without the required review. The
source URLs below identify the inspected releases, not a promise that these
will remain the latest versions.

## Official references

Public platform behavior was checked against these primary sources on
2026-09-27. This research is separate from local execution tests and does not
establish that your repository has those settings enabled.

[checks]: https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks
[owners]: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
[branches]: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule
[security]: https://docs.github.com/en/actions/reference/security/secure-use
[rules]: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/troubleshooting-rules
[create-rules]: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository
[artifacts]: https://github.com/actions/upload-artifact/tree/043fb46d1a93c77aae656e7c1c64a875d1fc6a0a

Pinned actions: [checkout v7.0.1](https://github.com/actions/checkout/commit/3d3c42e5aac5ba805825da76410c181273ba90b1),
[setup-python v7.0.0](https://github.com/actions/setup-python/commit/5fda3b95a4ea91299a34e894583c3862153e4b97),
and [upload-artifact v7.0.1](https://github.com/actions/upload-artifact/commit/043fb46d1a93c77aae656e7c1c64a875d1fc6a0a).
