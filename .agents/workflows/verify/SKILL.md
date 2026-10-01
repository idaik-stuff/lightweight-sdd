---
name: verify
description: "Use when checking a completed or in-progress change against acceptance criteria and risk in this Lightweight SDD repository. Select focused, standard, or broad verification, execute real documented checks, and record evidence and limitations. Do not use as a substitute for independent review, to implement fixes silently, or to deploy."
---

# Verify a change

## Inputs and boundaries
Run within the Lightweight SDD repository; resolve repository paths from its root.
Read `AGENTS.md`, applicable local instructions, the change boundary, and the active
spec/plan when required. Accept `focused`, `standard`, or `broad` as a requested scope,
not permission to under-check risk. Use the README's real command registry.
Do not edit product code, update snapshots to hide failures, or install missing tools.
Update evidence in the plan when authorized by the current change.

## Procedure
1. Identify the exact target: commit/range, or working snapshot including relevant
   staged, unstaged, and untracked files. Compare against the intended base, not an
   assumed branch. Note pre-existing changes. Record version, environment, and scope.
2. Select the minimum scope from `AGENTS.md` and
   [methodology section 6](../../../docs/development/methodology.md#6-verification-scopes).
   Explain any elevation; never lower an L3 check to focused because the diff is small.
3. Map AC and material risks to actual tests, checks, or defined manual procedures.
   Use [risk checks](../../references/risk-checks.md) only for relevant branches.
   Distinguish a proposed check, a check that ran, and what that evidence establishes.
4. Inspect configured commands before execution. Use `python3 scripts/verify <scope>`
   with an explicit `--base`, `--level`, and `--change` for L2/L3. Read the
   [automation contract](../../../docs/development/automation.md) only when needed.
   The default product target blocks without real product checks; `--target framework`
   is for framework-only checks, never a substitute for product evidence. For an L0
   document-only change, a targeted `scripts/check-docs` run and diff inspection can
   suffice. Do not install missing tools or treat a dry run as successful execution.
5. Read the local JSON report and its source fingerprints; any source mutation requires
   rerunning against the final change. Record outcomes as passed, failed, blocked, or not run, with the command or
   manual procedure, relevant result, and limitations. Distinguish pre-existing
   failures without treating them as passes. Do not copy raw logs or secrets to Git.
6. Assess whether the evidence exercises the claimed behavior. Unit tests alone do
   not establish a migration, public contract, permission boundary, or load property
   that they never exercise. Do not silently fix code or relax assertions to pass.
7. For L3, provide initial evidence to a separate reviewer through the
   [review contract](../../review/independent-review.md). If isolated delegation is
   supported, request that reviewer and record its real result; otherwise state that
   review is pending. Do not label this verification pass an independent review.
8. After review-driven edits, rerun affected checks and obtain review of material
   corrections. Bind evidence to the final diff and confirm the broad risk coverage.
   Rerun checks whose inputs changed; do not reuse stale evidence as final verification.

## Output and completion
Use the [evidence/handoff contract](../../references/handoffs.md). Report verification
outcome separately from review-gate and deployment state. A passed subset plus missing
required checks is not a complete pass. A completed run with failed required checks is
failed; list blocked checks separately. With no known failure but incomplete required
coverage, the outcome is blocked. Optional omissions need rationale, not a false pass.

For L2/L3, update plan evidence; mark spec implemented and plan completed only when
actual acceptances, AC, verification, review, and affected documentation are complete.
For L0/L1, supply the durable change summary without committing automatically.
An authorized exception is not full verification. Never infer approval or deployment.
