# Plan: CHG-001-branch-and-pr-workflow | Branch and pull request for every change

Status: `approved` | Technical owner: Idaika Iglesias | Accepted by / date: Idaika Iglesias, 2026-10-19 (in conversation).
Spec: [spec.md](spec.md) | Verification scope: `broad`.

## System inspection

Inspected at base `ebf25ad` (1.0.0):

- `scripts/sdd/changes.py` `assess()` computes changed paths against an explicit `--base`, path floors, and spec/plan pairing. It is the single entry point for both `scripts/check-change-level` and, through `verify.run()`, `scripts/verify`. It never reads the current branch.
- `scripts/sdd/verify.py` `run()` calls `assess()` only when `target == "product"` or any of `--base`/`--level`/`--change` is given (`needs_gate`). `verify standard --target framework` without those flags (Quick start step 2) never reaches `assess()`.
- `assess()` already returns `blocked` with "No changes relative to the explicit base" when the diff is empty.
- `.github/workflows/sdd.yml`: the `sdd-verify` job checks out `needs.policy.outputs.merge` (a SHA), so `sdd-candidate` is a detached HEAD, and runs `scripts/verify --root sdd-candidate --base ... --level ...`. `scripts/sdd/ci.py` reads the diff between explicit SHAs and never uses branches. All three jobs are skipped in `idaik-stuff/lightweight-sdd`.
- `ci.py` `ci_configuration()` uses `require_keys` with no optional keys: a new key in `.sdd/ci.json` would make a 1.0.0 base reject the candidate. Adding configuration there is therefore avoided.
- `scripts/sdd/common.py` `git()` is the safe Git reader (no shell, no prompts, scrubbed `GIT_DIR`). Tests use `scripts/tests/support.py` `Fixture.init_git()`, which creates repositories with the Git default branch and sets `core.hooksPath` to a disabled folder.
- In this clone `refs/remotes/origin/HEAD` is not set (observed); after `git clone` it normally is.
- `.agents/tools/sync_adapters.py` generates thin wrappers that point to the canonical `.agents/workflows/<phase>/SKILL.md` and copy only its frontmatter `description`. Editing procedure bodies does not change wrappers; editing descriptions does.
- `.sdd/ci.json` `framework_paths` and `.sdd/risk-rules.json` do not match `scripts/hooks/**`. `.github/CODEOWNERS.example` already covers `/scripts/`.
- `scripts/tests/test_ci_workflow.py` asserts properties of `sdd.yml` only (pinned actions, read-only permissions, only the upstream-skip condition).
- `docs/development/methodology.md` line 79 places the L0/L1 record in "the commit message or an existing change record"; `.github/pull_request_template.md` has the metadata block parsed by `ci.py metadata()`.

## Technical approach

**Branch rule in `assess()`.** Add a `branch_guard(root)` helper in `changes.py`, called from `assess()` only when the diff is non-empty. Both commands inherit it (AC-01, AC-02) and the CI/health-check paths stay untouched (AC-04, AC-05):

1. Current branch: `git symbolic-ref -q --short HEAD`. Detached HEAD → rule does not apply (AC-05).
2. Default branch, in order:
   - Git config `sdd.defaultBranch`, when set (explicit local declaration; no schema change to `.sdd/ci.json`);
   - otherwise `refs/remotes/origin/HEAD` (set by `git clone` or `git remote set-head origin --auto`);
   - otherwise undeterminable → error naming both ways to declare it (AC-06).
3. Current branch equals the default branch → error: "Changes on default branch '<name>'; create a change branch (for example `chg-NNN-<slug>`) before editing" (AC-01, AC-02). The report records `branch` and `default_branch` fields.

The error goes through the existing `errors` list, so `check-change-level` exits 1 and `verify` fails before running checks and saves the JSON report, as today.

**Pre-push hook.** `scripts/hooks/pre-push`, POSIX `sh` (Git runs hooks with `sh`, including Git for Windows). It reads the refs Git passes on stdin and refuses any update of `refs/heads/<default>`, resolving the default branch with the same order (`sdd.defaultBranch`, then `refs/remotes/<remote>/HEAD`). If it cannot resolve it, it refuses with the same guidance (fail closed). It does not call Python, so it works where only Git exists.

**Direct-push workflow.** New `.github/workflows/sdd-direct-push.yml`: `on: push` to the repository default branch, `permissions: contents: read, pull-requests: read`, no secrets beyond the job's `GITHUB_TOKEN`, pinned actions only. For each commit in `before..after` it asks the GitHub API for associated pull requests (`gh api repos/{repo}/commits/{sha}/pulls`) and fails, listing the SHAs, when a commit has no merged PR. A branch-creation push (`before` all zeros, the bootstrap) is reported and passes. Like `sdd.yml`, its job is skipped in `idaik-stuff/lightweight-sdd` (`if: github.repository != 'idaik-stuff/lightweight-sdd'`), by owner decision for consistency with the existing gate. The check logic lives in the workflow's `run:` block so that a test can execute it with a stubbed `gh`, the same pattern as the existing gate-shell test. "Optional" means it never gates merges and the owner can disable it in the Actions UI; the docs say so.

**Instructions and docs.** Text-only edits to `AGENTS.md`, `implement`, `verify`, the handoff contract, PR template, methodology, README, `ci-enforcement.md`, CHANGELOG. Frontmatter descriptions stay unchanged, so generated wrappers do not change; `sync_adapters.py --check` still runs as evidence (AC-11).

**Classification.** Add `scripts/hooks/**` to `framework_paths` in `.sdd/ci.json` and to the `verification-controls` L3 rule in `.sdd/risk-rules.json` (AC-14).

Rejected alternatives:

- A `default_branch` key in `.sdd/ci.json`: versioned and visible, but 1.0.0 bases reject unknown keys, so adopters' first PR with it would fail `sdd-policy`. Git config plus `origin/HEAD` avoids that.
- Assuming `main`: a silent pass on `master` repositories, which breaks the no-silent-pass property.
- The hook in Python: Windows often has `python`, not `python3`, and a hook that fails to start blocks every push for the wrong reason.
- A check in `verify` alone: `check-change-level` would still pass on the default branch.

## Affected components and contracts

| Area / path | Proposed change | Impact / consumer |
| --- | --- | --- |
| `scripts/sdd/changes.py` | `branch_guard()`; `branch`/`default_branch` in report | Both local commands; JSON report readers (additive fields) |
| `scripts/hooks/pre-push` (new) | Refuse pushes to the default branch | Opt-in via `git config core.hooksPath scripts/hooks` |
| `.github/workflows/sdd-direct-push.yml` (new) | Flag commits on the default branch without a merged PR | Runs on push to default branch in adopters; skipped in this repository |
| `.sdd/ci.json`, `.sdd/risk-rules.json` | `scripts/hooks/**` as framework path with L3 floor | CI target selection and path floors |
| `AGENTS.md` | Permanent branch/PR rule | All clients (read at session start) |
| `.agents/workflows/implement/SKILL.md`, `verify/SKILL.md`, `.agents/references/handoffs.md` | Branch step; PR step; branch + PR URL in handoff | All four clients through thin wrappers |
| `.github/pull_request_template.md` | Level, Change-ID, how verified, AC if any; metadata block unchanged | `ci.py metadata()` parser (unchanged format) |
| `docs/development/methodology.md` | L0/L1 record = PR description; squash merge | Human readers |
| `README.md`, `docs/development/ci-enforcement.md` | Bootstrap order, first PR step, GitHub Free limits, merge settings, hook | Adopters |
| `CHANGELOG.md` | `Unreleased` entry marked breaking (2.0.0) | Adopters |
| `scripts/tests/test_changes.py`, `test_verify.py`, new `test_hooks.py`, new `test_direct_push_workflow.py`, `test_agent_governance.py` | Tests below | Framework automation tests |
| `FEEDBACK-branch-and-pr-workflow.md` | Deleted (untracked input) once covered | None; addendum deferral recorded in the spec |

## Risk-proportionate strategy

| Area | Decision, check, or reason for non-applicability |
| --- | --- |
| Compatibility and consumers | Breaking only for working on the default branch with changes, by design (2.0.0). CI is unaffected: detached checkout (AC-05, tested with a detached fixture). Health check unaffected (AC-04). JSON report fields are additive. PR metadata format unchanged (AC-12, existing `test_ci` metadata tests). `.sdd/ci.json` schema unchanged. |
| Data, integrity, and migration | N/A - no persistent data. Adopters "migrate" by reinstall; existing default-branch work must move to a branch (documented in CHANGELOG). |
| Permissions, security, and privacy | The new workflow gets `contents: read`, `pull-requests: read`, no secrets, pinned actions, no `pull_request_target`. The hook runs local Git only, no network. `git()` keeps scrubbing `GIT_DIR`. A user can bypass the hook with `--no-verify`; documented as a human decision, never used by agents. |
| Failures, load, and availability | Fail closed: undeterminable default branch → error, not pass (AC-06). Risk of blocking legitimate work is bounded to the default branch with a diff; message gives the fix. API errors in the workflow fail the run (no `|| true`), visible but non-gating. |
| Change observability | Explicit error text in both commands and the hook; `branch`/`default_branch` in the JSON report; workflow run lists offending SHAs. |
| Rollout and feasible recovery | Ships in the 2.0.0 release with this PR. Recovery: revert the squash commit; the hook is opt-in (`git config --unset core.hooksPath`); the workflow can be disabled in the Actions UI. |

## Implementation steps

1. Classification: `scripts/hooks/**` in `.sdd/ci.json` and `.sdd/risk-rules.json`, plus governance test (AC-14).
2. `branch_guard()` in `changes.py` and tests for AC-01 to AC-06 (default branch with diff, change branch, no diff, no base, detached HEAD, undeterminable, `sdd.defaultBranch` override).
3. `scripts/hooks/pre-push` and `test_hooks.py` pushing to a local bare repository (AC-07, AC-08, fail-closed case).
4. `sdd-direct-push.yml` and static tests for pins, permissions, events, and no error suppression (AC-09 structure).
5. Text: `AGENTS.md`, `implement`, `verify`, handoffs, PR template, methodology, README, `ci-enforcement.md`, CHANGELOG (AC-10, AC-12, AC-13).
6. Remove `FEEDBACK-branch-and-pr-workflow.md`; run broad verification; prepare the independent-review packet.

Each step is checked with `python3 -m unittest discover -s scripts/tests -p "test_*.py"` before the next one.

## Verification plan and traceability

Environment: Windows 11, Git for Windows, local Python 3; fixtures are isolated temporary repositories (no network).

| AC / risk | Test, check, or manual procedure | Command / location / environment | Expected result |
| --- | --- | --- | --- |
| AC-01 | Fixture on default branch with diff runs `check-change-level` | `scripts/tests/test_changes.py` | Exit 1; message names branch |
| AC-02 | Same fixture runs `verify` | `scripts/tests/test_verify.py` | Status `failed`; no check executed; report saved with error |
| AC-03 | Fixture on change branch, same diff | `test_changes.py`, `test_verify.py` | Same result as without the guard |
| AC-04 | Default branch, empty diff; and no `--base` with `--target framework` | `test_changes.py`, `test_verify.py` | No branch error |
| AC-05 | Detached HEAD fixture (`git checkout --detach`) with diff | `test_changes.py` | No branch error |
| AC-06 | No `origin/HEAD`, no `sdd.defaultBranch` | `test_changes.py` | Error with both declaration options |
| AC-07, AC-08 | Push to bare remote with hook enabled | new `scripts/tests/test_hooks.py` | Default branch refused; change branch accepted; undeterminable refused |
| AC-09 | Static workflow tests (pins, permissions, event, upstream-skip condition, no error suppression); execution of the `run:` block with a stubbed `gh` for a commit with and without a merged PR, and a branch-creation push | new `scripts/tests/test_direct_push_workflow.py` | Static tests pass everywhere; the execution test passes on Linux with bash and is skipped on Windows (same rule as the existing gate-shell test). No live run: the job is skipped in this repository |
| AC-10 | Inspection of rule text | Diff review + independent review | Obligations present |
| AC-11 | Adapter drift check | `python3 .agents/tools/sync_adapters.py --check` | Passes |
| AC-12 | Metadata parser unchanged | existing `test_ci.py`; inspection of template | Passes; fields present |
| AC-13 | Inspection of docs; links | `python3 scripts/check-docs` + diff review | Passes; content present |
| AC-14 | Governance test | `scripts/tests/test_agent_governance.py` | `scripts/hooks/pre-push` matches framework paths and an L3 rule |
| Broad gate | Full framework verification | `python3 scripts/verify broad --target framework --base main --level L3 --change CHG-001-branch-and-pr-workflow` | `passed`; JSON report referenced below |
| Level floor | Change-level check | `python3 scripts/check-change-level --base main --level L3 --change CHG-001-branch-and-pr-workflow` | `passed` |
| L3 review | Independent review in a fresh session | `sdd-independent-review` agent with `.agents/review/independent-review.md` | Findings recorded and resolved |

Known limitation: `sdd-gate` does not run in this repository (spec, Uncertainties), so the PR has no server-side gate; evidence is local and recorded here. Before running the checks in this clone, `refs/remotes/origin/HEAD` must exist (`git remote set-head origin --auto`) or AC-06 correctly fails the run.

## Affected documentation

`AGENTS.md`, `README.md` (Quick start), `docs/development/methodology.md`, `docs/development/ci-enforcement.md`, `.agents/workflows/implement` and `verify`, `.agents/references/handoffs.md`, `.github/pull_request_template.md`, `CHANGELOG.md`.

Technical decisions accepted by the owner (Idaika Iglesias, 2026-10-19, in conversation): default-branch resolution order (`sdd.defaultBranch`, then `origin/HEAD`, else fail); pre-push hook in POSIX `sh`; direct-push workflow skipped in this repository.

## Deviations and decisions during execution

None recorded yet.

## Completion evidence

Verified version or diff: pending. Relevant environment: pending.

| AC / check | Result | Evidence summary / reference |
| --- | --- | --- |
| AC-01 to AC-14 | Not run | Pending implementation. |

Independent review: pending; required for L3. Record reviewer, isolation, scope, findings, and resolution.

Outstanding items / exceptions: `sdd-gate` and `sdd-direct-push` are skipped in this repository by design; AC-09 has no live GitHub evidence, and its execution test is skipped on this Windows workstation, so it needs a Linux run (for example WSL or a Linux machine) or is recorded as blocked.

Delivery: not merged; not released.
