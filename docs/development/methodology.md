# Development methodology

Framework version: `1.0.0` | Adoption owner: `TBD`.

This document expands on [AGENTS.md](../../AGENTS.md). Classification and routes are defined only there. Agent Skills implement these procedures; see [workflow usage](workflows.md). [Local automation](automation.md) runs the configured checks, and the optional [CI adapter](ci-enforcement.md) adds the server-side team review requirements described below.

## 1. Starting and classifying work

Determine the requested outcome and inspect the relevant area. Classify by risk before size. For a small change, a sentence is enough: "L1: fixes an internal calculation without modifying contracts". For L2/L3, record the level and its rationale in the spec.

A one-line permissions fix is L3, not L1. A text change that alters recovery instructions or a contract is not necessarily L0. Do not downgrade a change because its files appear simple.

If an uncertainty could trigger L3, investigate enough to classify the change. Do not escalate merely because a trivial detail is unknown, or downgrade for convenience. Discovering new impact requires updating the level, plan, and gates before proceeding with the affected work.

## 2. Starting a product

The initial order is the brief, MVP scope, necessary cross-cutting requirements, and available knowledge of the architecture. This is not a sequence of approvals for every file, nor does it require resolving the entire product upfront.

If no system exists, the architecture overview states that absence. The design proposal belongs in the first change's plan and, when appropriate, in an ADR. After implementation, update the system overview. An exploratory experiment must have a question and a scope limit; it is not presented as a finished release and does not bypass gates before incorporation into the product.

## 3. Phase inputs and outputs

| Phase | Work | Minimum output |
| --- | --- | --- |
| investigate | Reproduce when possible, trace the flow, and test hypotheses. | Evidence, probable cause, and limitations. If the cause remains uncertain, do not present it as confirmed. |
| spec | Define what changes, why, its scope, and observable outcomes. | `spec.md` with acceptance criteria and blocking questions resolved. |
| plan | Inspect code and contracts; select the approach and checks. | An actionable `plan.md` with steps, risks, and mapping to the AC. |
| implement | Make bounded changes with tests and relevant documentation. | A diff aligned with the accepted scope; significant deviations resolved. |
| verify | Run checks and evaluate the AC, diff, and risks. | Concrete evidence and a result: passed, failed, or blocked. |

Do not create a separate investigation report by default. For L0/L1, retain the essentials in the change record. For L2/L3, include them in the plan when they affect the approach.

## 4. Approval without ceremonial rounds

For L2/L3, the product owner accepts the scope and AC; the technical owner accepts the plan. They may do so together and may be the same person. Explicit authorization that already covers those contents is sufficient: do not request repeated confirmations.

A general request for an idea does not approve requirements that the agent adds later. Record who accepted what, or leave the proposal pending. For L0/L1, authorization for the bounded change is enough; no approval documents are needed.

An implementation deviation that does not change scope, contracts, or risk can be noted in the plan. A material deviation requires revising the relevant artifact and obtaining acceptance before carrying it out.

## 5. Strategy, design, and ADRs

Implementation strategy is part of `plan.md`, not another mandatory documentation phase. For L3, consider compatibility, consumers, data, migration, failures, security, observability, and recovery according to the actual risk.

Create an ADR when there are relevant alternatives and a durable decision whose tradeoffs are worth preserving. A contract change can be L3 without an ADR. A lengthy design may be separated from the plan only when the detail justifies it; reference that file rather than copying it.

Do not promise rollback for an irreversible operation. Define prevention, restoration, or a viable roll-forward approach, and who authorizes the residual risk.

## 6. Verification scopes

| Scope | Check selection |
| --- | --- |
| focused | Directly affected diff and behavior; a targeted test or relevant inspection for documentation. |
| standard | The above, plus lint/type checks and regression checks for affected components, with integration checks when crossing boundaries. |
| broad | The above, plus contracts, cross-component integration, and tests for L3 risks: migration, permissions, failures, or recovery when applicable. |

Broad does not mean running everything indiscriminately. Include the full suite when scope or uncertainty prevents confidently narrowing it down. Command entrypoints belong in the [README](../../README.md); exact check arguments and cumulative profiles live in `.sdd/verification.json`, not in this table. The local runner executes those commands and records evidence; it does not decide whether they adequately cover every AC or risk.

For a bug, aim for a regression test that fails before the fix and passes afterward. If that is not feasible, explain the limitation and alternative evidence. An AC that cannot be automated needs a defined manual check, not a vague assertion.

Do not use the number of tests or a coverage percentage as a substitute for checking behavior. Do not claim that a contract, migration, or performance requirement has been validated using only unit tests that do not exercise it.

If a tool, environment, or credential is missing, record `blocked` or `not run`, its impact, and the outstanding action. Distinguish pre-existing failures from introduced failures; a pre-existing failure does not make the gate pass either. This documentation starter is not evidence of product verification.

## 7. Independent review for L3

First, perform initial verification. Then give a different person or a fresh session the spec, plan, diff, tests, relevant ADRs, and the minimum context needed to understand them. Avoid carrying over the conversation that defended the design.

The reviewer inspects with read-only access and returns concrete findings with location, risk, and evidence; they do not approve their own change or mix review with silent edits. In particular, they check that the AC and constraints are satisfied, not just style.

An isolated session of the same model is not equivalent to human independence and does not guarantee the absence of shared biases. Record who or what reviewed the work, the isolation used, and its limitations. Risk acceptance and sensitive authorizations remain human responsibilities.

Resolve blocking findings and repeat the affected checks; the evidence must correspond to the final diff. Confirm coverage of the full broad scope before completion. If no reviewer is available, do not declare the gate satisfied.

## 8. Evidence and completion

For L2/L3, `plan.md` contains a summary for each AC: the check, result, and a reproducible reference to the relevant test, artifact, or record. Include the version/diff and environment if they affect interpretation. Do not copy entire logs or sensitive data into the repository.

For L0/L1, recording the level and rationale, change, checks, and limitations in the commit message or an existing change record is sufficient. If evidence is in a PR, retain the necessary durable summary in Git; do not create `verification.md` just for this. The agent does not commit or publish anything without authorization.

A release is ready when the scope is resolved, applicable AC have been checked, required gates are satisfied, and affected documents reflect the outcome. "Implemented" does not mean "deployed": record production delivery separately in the plan when applicable.

## 9. Exceptions and urgent work

An operational emergency does not lower the level. If a gate must be deferred, the responsible person records explicit authorization, rationale, risk, a compensating measure, an owner, and a date to complete the deferred requirement. Use the plan or existing incident record; do not create a parallel exception system.

Mark the outcome as `authorized exception`, not complete verification, and do not mark outstanding requirements as satisfied. This procedure does not authorize the agent to bypass technical permissions or higher-level policies, or to accept destructive risks on its own.

## 10. Evolving the starter

The framework ships five workflows (`investigate`, `spec`, `plan`, `implement`, and `verify`) plus a separate reviewer. Their behavior in a given client is not assumed validated until the [behavior scenarios](../../.agents/evals/scenarios.md) have been run there; adjust them from real failures. Do not create additional Skills for tasks better solved by code.

The automation provides a deterministic runner, structural document checks, and conservative path-based risk floors. A draft or approved spec may precede its plan; paired artifacts are required by product-change verification, not merely by drafting. Path rules can raise a floor but cannot prove low risk. Move further deterministic checks into scripts, tests, and CI as they become clear. Prioritize those critical to the product's risk early: a lightweight process does not imply that a high-risk system may operate without technical controls. Do not add adapters for further agent clients until the team actually uses them.

Indicative complexity budget: four levels, two normal artifacts per feature, and a single source of instructions. An additional component must address a demonstrated need, not fill out an agent organization chart.

## 11. CI enforcement

The framework supplies a GitHub Actions adapter, not an activated remote policy. Use the [enforcement guide](ci-enforcement.md) for ownership, base-policy execution, the required final gate, and the one-time bootstrap. Human approvals and code-owner protection must be configured on the server; CI does not authenticate acceptance strings in Markdown. Documentation-only proposals do not require a fictitious implementation plan. The chosen team baseline requires one human PR approval, while L3 additionally receives the substantive independent review above.
