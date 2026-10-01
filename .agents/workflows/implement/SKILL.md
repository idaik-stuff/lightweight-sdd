---
name: implement
description: "Use only when the user explicitly authorizes implementing a bounded change in this Lightweight SDD repository. Apply an accepted spec and plan for L2/L3, or the authorized request for L0/L1, with incremental edits, tests, documentation, and verification handoff. Do not activate from a request only to investigate, specify, plan, or review."
---

# Implement a bounded change

## Inputs and boundaries
Run within the Lightweight SDD repository; resolve repository paths from its root.
Require explicit implementation authorization for the actual scope. An instruction
to design, investigate, or review is insufficient. In an agent integration that makes
this workflow manual-only, require its explicit invocation; do not work around it by
reading this file directly. Read `AGENTS.md` and applicable local instructions.

## Procedure
1. Classify before editing. For L0/L1, use the bounded request and diagnosis when
   needed; do not invent spec/plan requirements. For L2/L3, read the active spec and
   plan, validate their actual scope/technical acceptance, and inspect blockers.
2. Inspect the relevant code, tests, and worktree. Identify the base and existing user
   changes, including staged and untracked work. Do not reset, overwrite, stage, or
   commit another person's work. Avoid assuming a clean worktree or a `main` branch.
3. For an accepted L2/L3 plan, mark execution in progress. Implement one bounded step
   at a time using existing patterns. Add or update tests alongside behavior; for a
   bug, demonstrate pre-fix failure and post-fix success when safely feasible.
4. Run available focused checks during implementation from the README registry.
   Inspect commands for side effects and use a safe local environment. Preserve
   evidence of failures instead of repeatedly retrying without a changed hypothesis.
5. Record minor approach deviations in the plan. Stop the affected work when scope,
   contracts, risk, data safety, or recovery changes materially; revise the spec/plan
   and obtain the missing acceptance. Do not add opportunistic refactors or features.
6. Update only affected living documentation to match what now exists. Do not claim
   a planned component is implemented or rewrite historical specs wholesale.
7. Inspect the final diff for scope, unwanted changes, generated files, and sensitive
   data. Include staged, unstaged, and relevant untracked changes in the boundary.
   Never infer the complete change from the default unstaged diff alone.
8. Hand off to the `verify` workflow at the required scope. Verification is part of
   this authorized change, not permission to deploy or perform destructive actions.
   For L3, prepare the packet in the [review contract](../../review/independent-review.md)
   after initial verification. Do not act as your own independent reviewer.

## Output
Return changed areas, level, acceptance-criteria coverage, checks actually run,
material deviations, documentation updates, and remaining checks or review.
Retain durable evidence in the active plan for L2/L3. For L0/L1, prepare the short
change-record/commit-summary text for the user without committing it automatically.
Use the [handoff contract](../../references/handoffs.md) when resuming elsewhere.

## Exit and escalation
Editing code does not satisfy completion. Keep spec/plan states open until applicable
verification and review gates are met. Never call implementation deployed. Preserve
blocked work explicitly, and request human risk authorization where required.
Do not publish, commit, push, install tools, access production, or weaken permissions
merely because those operations would make the implementation easier.
