# Plan: CHG-001-branch-and-pr-workflow | Branch and pull request for every change

Status: `completed` | Technical owner: Idaika Iglesias | Accepted by / date: Idaika Iglesias, 2026-10-19 (in conversation).
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
   Refined after review: see Deviations (F3, F4, N1, N2).
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

- `scripts/tests/support.py`: `Fixture.init_git()` now declares the initial branch as `sdd.defaultBranch` and switches to `chg-fixture`, so existing tests keep exercising unchanged behavior on a change branch (AC-03); `git_env()` was extracted for the hook tests. Test-only; no scope impact.
- `docs/manual/02-adoption.md` (not listed above): one paragraph after step 2 says every later change goes through branch + PR and points to the Quick start. Without it the manual's step 1 clean-up reads as work on the default branch. Minor documentation addition within the accepted scope.
- The README Quick start was renumbered (6 steps): branch work and the hook are step 3, CI activation with the first PR is step 4.
- AC-09's execution test can run on Linux through WSL Ubuntu on this workstation, so it is evidence rather than blocked.
- Review-driven refinements (owner accepted the corrections, 2026-10-19, in conversation); same AC, stricter fail-closed behavior:
  - F3: `sdd.defaultBranch` is read from repository-local config only (`--local`), must name an existing local or `origin` branch, and must agree with `origin/HEAD` when both exist; otherwise the checks and the hook fail. The hook applies the same rules.
  - F4: `scripts/sdd/common.py` gains `run_git()` and `git_optional()`; only Git exit status 1 means "absent" (detached HEAD, unset config, missing ref). Any other failure propagates instead of skipping the rule.
  - F5: `sdd-direct-push` counts only PRs merged into the default branch, fails on force pushes, on pushes listing no commits, and at the 2048-commit event limit.
  - F6: the hook gives URL pushes their own message (no `set-head` advice); tests cover deletion, mixed multi-ref, URL, and declaration errors.
  - F1: `scripts/hooks/pre-push` is recorded as mode `100755`, with a test.
  - N1/N2 (second review): the hook refuses on Git exit codes other than 0/1 and compares a declaration only with `origin/HEAD`, as `changes.py` does; a secondary remote with another HEAD no longer blocks change-branch pushes. N3: README and CHANGELOG list the declaration failure cases.
  - F2/F7/F8: per-file branch/merge obligations in `implement`, `verify`, handoffs; manual pages `01-concepts.md`, `03-working-a-change.md`, `example/README.md` now name the PR description as the L0/L1 record; Quick start step 1 covers existing repositories; CHANGELOG and `ci-enforcement.md` document named-branch CI jobs and the event limit.

## Completion evidence

Verified version or diff: working snapshot on branch `chg-001-branch-and-pr-workflow` after both review rounds (HEAD `7fc53ce` plus uncommitted changes, snapshot `f81ae8709f03a2f3`), base `main` (`ebf25ad`). Earlier runs: `b259b48de359da5f` (after F1-F8), `7e9559021a4b47c1` (before corrections), `8d8f10310b25a317` (with the feedback file). Only this plan's evidence and review lines changed after the final run.
Relevant environment: Windows 11, Git for Windows, Python 3.14.7; Linux via WSL Ubuntu, Python 3.14.4. This clone declares `git config sdd.defaultBranch main` (no `origin/HEAD`).

| AC / check | Result | Evidence summary / reference |
| --- | --- | --- |
| AC-01, AC-03, AC-04, AC-05, AC-06 | Passed | `test_changes.py`: default-branch failure (API and CLI exit 1), change branch unaffected, no-diff not failed, detached checkout unaffected, undeterminable default fails closed, `origin/HEAD` resolution, declaration that disagrees, names no branch, or is only global fails, Git errors other than exit 1 propagate. |
| AC-02, AC-04 | Passed | `test_verify.py`: failure before any check runs for both targets, report saved by CLI with `default_branch`, health check without `--base` unaffected. |
| AC-07, AC-08 | Passed | `test_hooks.py`: real pushes to a local bare remote on Windows, WSL on `/mnt/e`, and a native ext4 copy written from the index (hook mode `-rwxr-xr-x`); default branch, deletion, and mixed pushes refused; change branch accepted; `<remote>/HEAD`, URL, and declaration errors covered; secondary remote, unreadable declaration (Git stub, Linux only), index mode `100755` asserted. |
| AC-09 | Passed (local only) | `test_direct_push_workflow.py`: static contract on Windows and Linux; shell execution with stubbed `gh` on Linux only (bootstrap, merged, direct, API failure, force push, empty, 2048 limit). The jq filter on `.base.ref` is not exercised by the stub, and there is no live GitHub run (skipped in this repository). |
| AC-10, AC-12, AC-13 | Passed (review) | Text present in `AGENTS.md`, `implement`, `verify`, handoffs, PR template, README, `ci-enforcement.md`, manual; metadata block unchanged and `test_ci.py` passes. Confirmed by the independent review after F2 and F7. |
| AC-11 | Passed | `python3 .agents/tools/sync_adapters.py --check`: 20 generated files, 0 stale. |
| AC-14 | Passed | `test_agent_governance.py` and `test_changes.py`: `scripts/hooks/**` is a framework path with L3 floor; L2 declaration fails. |
| Full suites | Passed | Windows: 199 automation tests (6 platform skips) and 57 adapter tests. Linux native ext4 copy: 199 (1 skip: index-mode test needs a Git checkout) and 57. |
| Level floor | Passed | `python3 scripts/check-change-level --base main --level L3 --change CHG-001-branch-and-pr-workflow --scope broad`: floor L3, 4 L3 rules matched, 28 changed paths. |
| Broad gate | Passed | `python3 scripts/verify broad --target framework --base main --level L3 --change CHG-001-branch-and-pr-workflow`: docs, adapters, adapter-tests, automation-tests passed; report `.sdd/results/verify-20261019T102714983037Z-8d87c45b.json` (local, untracked); source unchanged during the run. Rerun on commit `106aa80` (snapshot `02f626e603ce26c0`): passed, report `verify-20261019T103241904090Z-3d73770b.json`. |

Independent review: automated reviewer (`sdd-independent-review`, Claude sub-agent), fresh context without the implementation conversation, read-only tools (Read, Grep, Glob); it ran no code or tests, and every count, hash, and mode it cites is requester-supplied. The same reviewer context was resumed for rounds 2 and 3. Not a human review or approval.

| Round | Target | Result | Resolution |
| --- | --- | --- | --- |
| 1 | Full patch vs `main`, snapshot `7e9559021a4b47c1` | Blocking: F1 (hook committed without executable bit), F2 (AC-10 obligations missing per file). Non-blocking: F3 (global or invalid declaration fails open), F4 (any Git error read as absent), F5 (workflow accepts PRs into other branches, force and empty pushes), F6 (hook edge-case tests, URL message), F7 (manual drift), F8 (named-branch CI jobs) | All fixed; see Deviations |
| 2 | Full patch vs `main`, snapshot `b259b48de359da5f` | No blocking findings. Non-blocking: N1 (hook ignores Git exit codes > 1), N2 (hook compares declaration with any remote's HEAD), N3 (docs omit declaration failures), N4 (API may not yet list a just-merged PR; hypothesis) | N1-N3 fixed; N4 kept as a watch item for the first live adopter run |
| 3 | Hook, hook tests, README, CHANGELOG diff only | No blocking findings, no new findings | None needed |

Review limitations: an isolated session of the same model is not human independence. Not exercised anywhere: a live run of `sdd-direct-push`, its jq `.base.ref` filter, macOS, and a Git exit status above 1 on the hook's `remote_head` path. By design, with a declaration only the declared branch is protected on every remote, so a secondary remote with a different default branch is not protected. Confirm mode `100755` for `scripts/hooks/pre-push` in the final commit.

Outstanding items / exceptions: `sdd-gate` and `sdd-direct-push` are skipped in this repository by design, so the PR has no server-side gate; AC-09 has no live GitHub evidence. The untracked `FEEDBACK-pending-placeholder-false-positive.md` (input for CHG-002) is present in the verified snapshot.

Delivery: merged by the owner (Idaika Iglesias) through [PR #1](https://github.com/idaik-stuff/lightweight-sdd/pull/1) as squash commit `3d54c13` on 2026-10-19; `sdd-gate` skipped in this repository by design. Not released: the 2.0.0 version is pending the rest of the rollout.
