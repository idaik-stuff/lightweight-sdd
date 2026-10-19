# Spec: CHG-003-levels | L1 as the default level, L2 by explicit triggers

Status: `approved` | Level: `L3` | Level rationale: changes the classification contract every agent and adopter follows (`AGENTS.md`, `ci-governance`) and the CI scope policy (`.sdd/ci.json`); a mistake could route risky work through a lighter path or make small work heavier again.
Owner: Idaika Iglesias | Scope accepted by / date: Idaika Iglesias, 2026-10-19 (in conversation).
Related changes: third of the SDD Lite 2.0 rollout; builds on [CHG-001](../CHG-001-branch-and-pr-workflow/spec.md) (the PR description is the L0/L1 record) and [CHG-002](../CHG-002-gates-on-behavior/spec.md) (evidence guidance). CHG-004 (templates) follows.

## Problem and goal

In 1.0.0, L2 is the default bucket: "everything else is L2", and any intentionally new behavior is L2 "however small". A one-line new option or a small capability with two obvious acceptance criteria therefore needs a spec, a plan, and their acceptance. Adopters find the framework too dense for small changes.

Goal: L1 becomes the default level for fixes, refactors, adjustments, and small new capabilities whose behavior fits one to three clear acceptance criteria. L2 applies only when an explicit trigger is present, and the agent says which. L0 and L3 keep their meaning, so L3 rigor is unchanged.

## Context and current behavior

Observed at `381748f` (main after CHG-002):

- `AGENTS.md`: "Evaluate L3 first. If it does not apply, evaluate L0, then L1; everything else is L2." L1 is "Local fix or refactor, with no new capability or L3 risk", with route "verify focused/standard". L2 is "Intentionally new or modified behavior, with no L3 risk".
- `docs/manual/06-practices.md`: "The L1/L2 boundary is intent. If the change makes the product do something it was not meant to do before, it is L2, however small." `docs/manual/01-concepts.md` and `03-working-a-change.md` repeat the 1.0.0 definitions and order.
- `.agents/evals/scenarios.md` E04 ("Bounded feature requirements") expects an L2 spec.
- Verification scopes: `scripts/sdd/changes.py` already requires focused for L0/L1, standard for L2, broad for L3 locally. `.sdd/ci.json` `scopes` selects L0 focused, L1 standard, L2 standard, L3 broad in CI; `ci.py` enforces only the minimums.
- Since CHG-001, the L0/L1 change record is the PR description, and the PR template asks for one to three criteria for L0/L1.

Closed design decision (ideation, 2026-10-19, point A):

- Keep the labels L0-L3. L0 Mechanical keeps its own label although it behaves like L1.
- L1 Quick is the default: fixes, refactors, adjustments, and small new capabilities whose behavior fits one to three clear AC.
- L2 Feature applies when any trigger holds: T1 ambiguity about what to build; T2 a new user-visible flow (screen, command, or flow, not an adjustment); T3 several areas with coordinated changes; T4 more than one PR or more than about one day of work; T5 a durable design decision worth recording. The owner can always force L2.
- L3 Critical: unchanged criteria and path floors.
- Evaluation order: L3, then L0, then L2 triggers, then L1.
- The agent declares the level in one line at the start, citing triggers (for example `L2: T1, T3`). It escalates on its own; only the owner downgrades.
- Routes unchanged. Verification: locally L0/L1 focused, L2 standard, L3 broad; in CI standard for L0-L2 and broad for L3.

## Scope and non-goals

Includes:

- `AGENTS.md` classification table and order: names (Mechanical, Quick, Feature, Critical), the new L1 and L2 criteria with triggers T1-T5, the owner's right to force L2, the evaluation order, the one-line declaration, and the escalation/downgrade rule. The L1 route says "verify focused".
- `.sdd/ci.json`: `scopes.L0` becomes `standard`. L1-L3 stay as they are.
- Documentation that restates the levels: `docs/development/methodology.md` section 1, `docs/development/ci-enforcement.md` scope table, `docs/manual/01-concepts.md`, `03-working-a-change.md`, `04-verification-ci.md`, `06-practices.md`, and the PR template's level guidance.
- `.agents/evals/scenarios.md`: E04 updated, plus scenarios for a small capability classified L1 and for each kind of L2 trigger and an owner-forced L2.
- A test that the shipped CI policy selects standard for L0-L2 and broad for L3.
- CHANGELOG entry marked breaking (2.0.0): L2 now means "has a trigger".

Does not include:

- Changes to L3 criteria, path floors, or `scripts/sdd/changes.py` minimum scopes (already as decided).
- A machine check of triggers or of the declaration line: triggers are judgement, and the declaration is an instruction, not a gate.
- Template changes (CHG-004), the installer (CHG-005), or the manual's worked example records beyond wording that contradicts the new rules.

## Expected behavior

- An agent classifying a change answers in order: L3 criteria; L0 (no functional, contractual, or operational effect); any of T1-T5 (L2); otherwise L1.
- Before its first change, the agent writes one line such as `L1: no L2 trigger`, `L2: T2`, or `L3: security boundary`. If it later finds a trigger or an L3 risk, it raises the level and says why; it never lowers a level unless the owner says so.
- A small new capability with one to three clear AC and no trigger is L1: no spec or plan; its AC and evidence live in the PR description.
- A change touching an L3 path floor is still blocked when declared below L3.
- CI runs at least standard verification for every L0-L2 PR; local L0/L1 verification stays focused.

## Acceptance criteria

| ID | Scenario / precondition | Action | Observable outcome |
| --- | --- | --- | --- |
| AC-01 | Updated `AGENTS.md` | Read the classification section | Order L3, L0, L2 triggers, L1; L1 includes small capabilities with one to three clear AC; L2 lists T1-T5 and the owner's right to force L2; L1 route is "verify focused" |
| AC-02 | Updated `AGENTS.md` | Read it | Requires a one-line level declaration citing triggers before the first change; the agent may only raise a level, the owner may lower it |
| AC-03 | Shipped `.sdd/ci.json` | Run the new policy test | L0, L1, L2 select `standard`; L3 selects `broad` |
| AC-04 | PR declaring L0 in an adopter with this policy as base | `ci.py` assesses it | Selected scope is `standard`, not `focused` |
| AC-05 | A change touching an L3 path floor declared L1 or L2 | Run `scripts/check-change-level` | Fails as in 1.0.0 (unchanged) |
| AC-06 | Local L0 or L1 change | Run `scripts/check-change-level --scope focused` | Passes the scope check, as in 1.0.0 |
| AC-07 | Methodology, CI enforcement guide, manual pages, PR template | Read them | No statement says that new behavior is L2 regardless of size, or that L2 is the default; the CI scope table shows L0 standard |
| AC-08 | Updated eval scenarios | Read them | E04 and new scenarios cover: small capability is L1; T1-T5 each lead to L2 with the trigger named; owner-forced L2; agent never lowers a level on its own |
| AC-09 | Repository at the end of this change | Run `scripts/check-docs` and `scripts/verify broad --target framework` | Pass |

AC-04 and AC-05 are the boundaries: CI never gets lighter for L0, and an L3 path still cannot be declared lower.

## Constraints and compatibility

- Consumers at risk: adopters' agents and owners, who now classify differently; adopters' CI, where L0 PRs run standard checks once this policy is their base (longer runs, never weaker).
- Property at risk: L3 detection and rigor must not change (AC-05). Lowering L2 to L1 never bypasses a path floor, because floors only raise levels.
- Breaking for adopters (2.0.0): an L2 spec written under 1.0.0 stays valid; new work that 1.0.0 would call L2 may now be L1.

## Uncertainties

None open. The level rules are the closed ideation decision A (2026-10-19).

## Acceptance and next steps

Scope acceptance: accepted by Idaika Iglesias on 2026-10-19 (in conversation), with AC-01 to AC-09. Next: plan with strategy.

Related plan: [plan.md](plan.md). States and completion rules: [docs/specs/README.md](../README.md).

Upon completion, record evidence and delivery status in the plan. If another change replaces this behavior, reference that change without rewriting history.
