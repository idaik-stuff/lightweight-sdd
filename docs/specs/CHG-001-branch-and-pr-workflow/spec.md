# Spec: CHG-001-branch-and-pr-workflow | Branch and pull request for every change

Status: `approved` | Level: `L3` | Level rationale: changes the framework's own enforcement contract (`ci-governance`: `AGENTS.md`, `.github/**`; `verification-controls`: `scripts/check-change-level`, `scripts/verify`, `scripts/sdd/**`; `agent-integration-controls`: `.agents/workflows/**`). A faulty check could block legitimate work or pass silently.
Owner: Idaika Iglesias | Scope accepted by / date: Idaika Iglesias, 2026-10-19 (in conversation).
Related changes: first of the SDD Lite 2.0 rollout; CHG-002 (gates on behavior) and CHG-003 (levels) build on it.

## Problem and goal

Adopters following the framework literally can commit every change, including L3 changes, straight to the default branch. The `sdd-gate` workflow runs only on `pull_request`, so in that case it never runs and nobody notices: silence looks like success. The adopter loses server-side enforcement, the PR record (level, change id, evidence), and the owner's merge as a distinct, recorded decision.

Goal: every change, at every level (L0–L3), is made on its own branch and integrated through a pull request that the owner merges; agents are told so, and local checks detect the unsafe default instead of passing silently.

## Context and current behavior

Observed facts (source: `FEEDBACK-branch-and-pr-workflow.md`, adoption in `idaik-stuff/cv-online`, framework `1.0.0`):

- `AGENTS.md` mentions "base-commit policy and the final `sdd-gate`" but never says to work on a branch or open a PR. "Commit and push" was read as "commit to the default branch".
- `.agents/workflows/implement/SKILL.md` has no branch step; `verify` and the [handoff contract](../../../.agents/references/handoffs.md) have no PR step. The handoff lists "branch/worktree if known" only.
- `scripts/check-change-level` and `scripts/verify` compare a `--base` with the working snapshot and pass on the default branch.
- `.github/workflows/sdd.yml` triggers only on `pull_request`.
- The README Quick start lists CI activation as optional (step 5).
- `docs/development/ci-enforcement.md` already notes that rulesets and required reviews are not available on some private repositories on free plans.
- In a local clone, `refs/remotes/origin/HEAD` may be unset (observed in this repository), so the default branch is not always discoverable from Git alone.

Constraint for the target product: GitHub Free with a private repository, so no branch protection, rulesets, required checks, or required reviews; a PR author cannot approve their own PR. Local guards are therefore the main protection.

## Scope and non-goals

Includes:

- A permanent rule in `AGENTS.md`: never commit to the default branch; one branch per change named after its change id; integrate through a PR that uses the PR template; "commit and push" means the change branch; the agent never merges; the owner merges only with a green `sdd-gate`, or with a noted exception.
- Workflow instructions: `implement` confirms or creates the change branch before the first edit; `verify` / completion pushes the branch and opens or updates the PR with level and change id, and reports the `sdd-gate` result or `blocked` when CI is not active; the handoff contract includes branch and PR URL.
- PR template: level, Change-ID, how it was verified, and AC when the change has them. For L0/L1 the PR description is the change record.
- Merge policy documented: squash merge only, default commit message "Pull request title and description", automatic deletion of head branches, so the PR description lands in Git history.
- Deterministic local checks: `scripts/check-change-level` and `scripts/verify` fail with a clear message when run on the default branch with changes against the base.
- An opt-in `pre-push` hook in `scripts/hooks/` that refuses pushes to the default branch, enabled with `git config core.hooksPath scripts/hooks`.
- Path classification for the new governance path: `scripts/hooks/**` is added to `framework_paths` in `.sdd/ci.json` and to an L3 risk rule in `.sdd/risk-rules.json`, so a change touching only the hook is not classified as product without a floor.
- An optional CI workflow on `push` to the default branch that flags commits that did not arrive through a merged PR.
- Adoption docs: Quick start documents the bootstrap order (initial commit on the default branch, then enable the hook, then every change through branch + PR) and makes "open the first change as a PR and see `sdd-gate` run" an explicit step; `ci-enforcement.md` states the GitHub Free private-repository limitation and that the local guards become the main protection.
- Regenerated client adapters so all clients receive the updated `implement` / `verify` entrypoints.
- Removal of the root input file `FEEDBACK-branch-and-pr-workflow.md` once its content is covered or explicitly deferred.

Does not include:

- The feedback's addendum (product checks runnable on a clean CI runner, runtime setup, `--target auto` CI-parity mode, general guidance for registering project governance paths), except the `scripts/hooks/**` classification above. Deferred to a separate change that must land before the framework is used in a product, because mandatory PRs make the CI gate run, and fail, on every product PR.
- A recorded bootstrap exception or flag. The initial commit has no base and no PR target; the checks do not fire without a diff (AC-04), and the hook is enabled after bootstrap.
- Changes to levels, gates on placeholder prose, templates, or the installer (CHG-002 to CHG-005).
- Configuring GitHub repository settings on anyone's behalf; the change documents them.
- Server-side enforcement that the GitHub plan does not provide.

## Expected behavior

- An agent following the framework never creates commits on the default branch. Before its first edit it is on a change branch; if it starts on the default branch, it creates the branch first.
- An owner's "commit and push" results in a pushed change branch and an open PR, never in a push to the default branch.
- The agent never merges a PR. The owner's merge is the recorded human decision.
- Local checks that see changes on the default branch fail with a message naming the branch and the expected action (create a change branch). Silence never stands in for success.
- Running the checks without changes on the default branch (for example the Quick start health check on a fresh template) is not blocked by this rule.
- Running inside CI on a detached checkout of the PR merge commit is not blocked by this rule.
- When the default branch cannot be determined, the checks do not silently pass; they report how to make it determinable.
- The hook and the push workflow are opt-in safety nets; they do not replace the PR gate or human review.

## Acceptance criteria

| ID | Scenario / precondition | Action | Observable outcome |
| --- | --- | --- | --- |
| AC-01 | Current branch is the default branch; working snapshot differs from `--base` | Run `scripts/check-change-level` | Exits non-zero; message names the default branch and says to create a change branch |
| AC-02 | Same as AC-01 | Run `scripts/verify <scope>` with any target | Exits non-zero before running checks, with the same branch message; the JSON report records the failure |
| AC-03 | Current branch is a non-default change branch; same diff as AC-01 | Run both commands | Results are identical to 1.0.0 behavior for that diff (no branch failure) |
| AC-04 | Current branch is the default branch; snapshot equals `--base`, or no `--base` is given (Quick start health check) | Run `scripts/verify standard --target framework` | Not failed by the branch rule |
| AC-05 | Detached HEAD, as in the CI checkout of the PR merge commit | Run the checks as `sdd.yml` does | Not failed by the branch rule; `sdd-gate` results unchanged |
| AC-06 | Default branch cannot be determined from repository configuration or Git | Run either command with changes | Fails (not passes) with a message explaining how to declare the default branch |
| AC-07 | Hook enabled via `core.hooksPath scripts/hooks` | `git push` to the default branch | Push is refused with a message; nothing is pushed |
| AC-08 | Hook enabled | `git push` of a change branch | Push proceeds |
| AC-09 | Optional push workflow enabled; a commit reaches the default branch without a merged PR | Push to the default branch | Workflow run fails and names the commit(s); a squash-merged PR commit passes |
| AC-10 | Updated `AGENTS.md`, `implement`, `verify`, handoff contract | Read them | Each contains the branch/PR obligations listed in Scope, including "commit and push means the change branch" and "the agent never merges" |
| AC-11 | Updated canonical workflows | Run `python3 .agents/tools/sync_adapters.py --check` | Passes; every configured client's `implement` / `verify` entrypoint reflects the update |
| AC-12 | Updated PR template | Open a new PR | Template asks for level, Change-ID, how verified, and AC if any; `sdd-gate` still parses the metadata block |
| AC-13 | Updated README and `ci-enforcement.md` | Read them | Quick start includes the bootstrap order and opening the first change as a PR; `ci-enforcement.md` states the GitHub Free private-repository limitation, the squash-only merge settings, and the hook as main local guard |
| AC-14 | Diff touching only `scripts/hooks/**` | Run `scripts/check-change-level` with `--level L2` | Fails because the declared level is below the L3 path floor; the path is classified as framework, not product |

AC-06 covers the failure boundary; AC-04 and AC-05 cover the boundaries where the rule must not fire.

## Constraints and compatibility

- Consumers at risk: adopters on 1.0.0 (for example `idaik-stuff/cv-online`) and the CI gate in `.github/workflows/sdd.yml`. The rule must not break `sdd-gate` on PRs (AC-05) and must not block the template health check (AC-04).
- Property at risk: no silent pass. Any undeterminable state fails closed (AC-06).
- New behavior in local checks is a breaking change for adopters who work on the default branch; it ships under the 2.0.0 target version with a CHANGELOG entry.
- In this framework repository `sdd-gate` is skipped by design (no real code owners). A skipped gate is never reported as passed; local verification recorded in the plan is the evidence.
- Framework automation stays Python 3.10+ standard library only; the hook must run where Git runs.

## Uncertainties

| Question / assumption | Owner | Blocks | Resolution or evidence |
| --- | --- | --- | --- |
| Is the feedback addendum (CI runtimes, `--target auto`, governance paths) out of this change? | Idaika | Scope | Resolved 2026-10-19 (owner, in conversation): out of scope and deferred to a change before product use, except `scripts/hooks/**` classification (AC-14). |
| Bootstrap exception: does the bootstrap commit need a recorded exception? | Idaika | AC-01/AC-02 | Resolved 2026-10-19 (owner, in conversation): no flag; document the bootstrap order in the Quick start (AC-13); AC-04 covers the no-diff health check. |
| This framework repository skips `sdd-gate` (`if: github.repository != 'idaik-stuff/lightweight-sdd'`). Does the PR rule apply here with only local checks as evidence? | Idaika | Verification of this rollout | Resolved 2026-10-19 (owner, in conversation): yes. Every change here uses branch + PR; evidence is local `scripts/verify broad --target framework` recorded in `plan.md` and linked from the PR, which states that the gate was skipped. A CI job for this repository is possible future work, not in scope. |

## Acceptance and next steps

Scope acceptance: accepted by Idaika Iglesias on 2026-10-19 (in conversation), with AC-01 to AC-14 and all uncertainties resolved. Next: plan with strategy.

Related plan: [plan.md](plan.md). States and completion rules: [docs/specs/README.md](../README.md).

Upon completion, record evidence and delivery status in the plan. If another change replaces this behavior, reference that change without rewriting history.
