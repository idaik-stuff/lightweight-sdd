---
name: spec
description: "Use when defining or revising the what, why, scope, and testable acceptance criteria for an L2/L3 change in this Lightweight SDD repository. Create or update the active change specification from user intent and inspected evidence. Do not use for initial product-brief drafting, a routine L0/L1 fix, technical planning, or coding."
---

# Specify a change

## Inputs and boundaries
Run within the Lightweight SDD repository; resolve repository paths from its root.
Read `AGENTS.md` and applicable local instructions. Accept user intent, relevant
requirements, or an existing change identifier. Do not invent a ticket or approval.
Use an existing identifier, or the local convention in `docs/specs/README.md`.
Edit only the active spec unless another documentation change is explicitly in scope.

## Procedure
1. Classify the change using `AGENTS.md`. For L0/L1, explain why a spec is unnecessary
   and return the smaller route; do not manufacture a feature package.
2. Inspect only the relevant existing behavior, tests, and accepted product
   constraints. Reference facts and mark assumptions. Product discovery belongs in
   the brief/MVP/PRD, not in a fabricated implementation feature.
3. Read the [spec template](../../../docs/templates/spec.md) and, when creating or
   transitioning an artifact, [its lifecycle](../../../docs/specs/README.md).
   Update an existing spec in place. Never reset its accepted content from a template.
4. Write problem, goal, current and expected behavior, scope, and non-goals. Keep
   technical choices out unless they are genuine contractual constraints.
5. Define stable AC identifiers with preconditions, actions, and observable outcomes.
   Cover applicable failure and boundary cases, not a universal checklist. Link to
   existing cross-cutting thresholds rather than duplicating or inventing them.
6. For L3, identify the consumer, data, boundary, or property at risk and the required
   compatibility or integrity outcome. Leave implementation strategy to the plan.
7. List unresolved questions with their effect on implementation. Ask a small set of
   blocking questions when needed; draft supported sections without filling gaps.
8. Summarize the scope and seek acceptance only where it is missing. Actual prior
   acceptance of the same contents is sufficient. Never self-approve. On a material
   scope revision, return the affected spec to draft and record the acceptance needed.

## Output
Create or update `docs/specs/<change-id>/spec.md`; retain useful sections only and
adjust links for its destination. A plan may not exist yet; leave its link pending
rather than creating a meaningless plan just to satisfy a link checker.

Return the level and rationale, path, principal AC, unresolved blockers, actual
acceptance status, and next permitted action. Use the
[handoff contract](../../references/handoffs.md) for a new session.
Do not create `plan.md`, code, extra review documents, or a new ADR in this phase.

## Exit and escalation
Ready for an accepted plan means scope and AC are accepted and implementation-
blocking questions are resolved. A useful but unapproved spec is still a draft.
A request to specify is not permission to implement. Reopen the appropriate product
boundary when a requested feature contradicts the accepted MVP; do not silently
expand it. Do not rewrite implemented historical specs to describe a new change.
