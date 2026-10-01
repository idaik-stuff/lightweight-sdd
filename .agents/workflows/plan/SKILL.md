---
name: plan
description: "Use when translating an L2/L3 change specification into an implementation plan grounded in this Lightweight SDD repository. Inspect real components, choose the technical approach, map acceptance criteria to checks, and evaluate risk-proportionate strategy. Do not use for writing requirements, a routine L0/L1 fix, or implementing code."
---

# Plan a change

## Inputs and boundaries
Run within the Lightweight SDD repository; resolve repository paths from its root.
Read `AGENTS.md`, applicable local instructions, and the active spec. Confirm scope
acceptance from evidence, not a status word alone. A draft plan may be useful before
acceptance, but do not present it as an approved implementation baseline.
Edit the active plan and, only when justified, its proposed ADR or design detail.

## Procedure
1. Confirm level, AC, constraints, and unresolved questions. Return requirement gaps
   to `spec`; do not quietly decide product scope through technical design.
2. Inspect the actual affected implementation, callers, contracts, schemas, tests,
   and only relevant architecture/ADRs. Distinguish existing paths from proposed ones.
   For a greenfield repository, state what does not exist before proposing components.
3. Read the [plan template](../../../docs/templates/plan.md) and the README command
   registry. Select the smallest viable approach; compare real alternatives only
   where a tradeoff matters. Do not replace the project stack without authorization.
4. Describe affected areas, dependencies, incremental steps, and how each increment
   can be checked. Keep tasks here; do not generate a separate task hierarchy.
5. Apply [risk checks](../../references/risk-checks.md) only to relevant risks. For
   L3, explicitly address applicable compatibility, data, security, failures,
   observability, rollout, and feasible recovery. Explain meaningful non-applicability.
6. If a durable decision warrants an ADR, use the
   [ADR template](../../../docs/templates/adr.md); keep it proposed until accepted.
   Do not generate ADRs merely because the level is L3. Keep strategy in the plan.
7. Map each AC and material risk to a real check or defined manual procedure, command
   or location, environment, and expected outcome. Mark unavailable commands as
   pending; a proposed check is not executed evidence. Plan L3 independent review.
8. Identify affected living documents and approvals. Record the technical owner's
   actual acceptance or leave the plan draft. Reuse valid acceptance; do not ask
   for repeated confirmation of an unchanged approach.

## Output
Create or update `docs/specs/<change-id>/plan.md` with implementation steps,
traceability, risks, dependencies, documentation impact, and real approval state.
Return the approach, files, verification scope, unresolved blockers, and next action.
For a new session, use the [handoff contract](../../references/handoffs.md).

## Exit and escalation
An implementation-ready plan has accepted scope and approach, resolved blocking
questions, and feasible checks or explicitly recorded dependencies. Missing verification
infrastructure may itself be a planned implementation step; it must not disappear
from the completion gate. Do not execute application changes or mark checks passed.
A design-only request stops here. Material scope, contract, risk, or recovery changes
require revisiting the affected artifact and acceptance before implementation.
