# Plan: CHANGE-ID | Change title

Status: `draft` | Technical owner: `TBD` | Accepted by / date: `TBD`.
Spec: [spec.md](spec.md) | Verification scope: `TBD`.

Copy this template alongside the spec. The italic line under each heading says whether the section is required, optional, or only needed in a given case, for L2 and for L3. Keep the sections your level requires and the conditional ones whose condition holds, add optional sections only when they help, and delete the rest; do not write `N/A`. Delete the italic marker lines too when you fill in the record. An L2 plan aims at about one page. Do not change requirements through the plan.

## System inspection

*L2: required, brief · L3: required*

TBD - Code, tests, contracts, and documents examined; confirmed behavior and gaps. Do not propose module names as though they already exist without inspecting them.

## Technical approach

*L2: required · L3: required*

TBD - The smallest change that satisfies the spec, relevant alternatives rejected, and why. Reference an ADR when the decision warrants that record; do not copy its content.

## Affected components and contracts

*L2: optional · L3: required*

| Area / path | Proposed change | Impact / consumer |
| --- | --- | --- |
| TBD | TBD | TBD |

## Risk-proportionate strategy

*L2: only applicable rows · L3: required, all six areas*

For L2, keep only the rows that apply. For L3, evaluate every area; an area that is not affected states why in one line, and unchanged areas do not need lengthy responses.

| Area | Decision, check, or reason it is not affected |
| --- | --- |
| Compatibility and consumers | TBD |
| Data, integrity, and migration | TBD |
| Permissions, security, and privacy | TBD |
| Failures, load, and availability | TBD |
| Change observability | TBD |
| Rollout and feasible recovery | TBD |

## Implementation steps

*L2: only if more than one step · L3: required*

1. TBD - A bounded change and a verifiable outcome.
2. TBD - The next increment, only if necessary.

Do not create `tasks.md` by default. Add steps only if they reduce uncertainty or help implement and review the change.

## Verification plan and traceability

*L2: required · L3: required*

| AC / risk | Test, check, or manual procedure | Command / location / environment | Expected result |
| --- | --- | --- | --- |
| AC-01 | TBD | TBD | TBD |

Reference real commands from the README. A single test may cover several AC. For NFRs, contracts, or migrations, identify evidence that actually exercises them. Declare environment dependencies before promising verification.

## Affected documentation

*L2: required, one line · L3: required*

TBD - Which living document or contract must be updated and why, or "none". Do not rewrite all old specs.

## Deviations and decisions during execution

*L2: only if any · L3: required*

None recorded yet. Add only material deviations: rationale, impact, and acceptance when required. Do not turn this section into a conversation transcript.

## Completion evidence

*L2: required · L3: required, with independent review*

Verified version or diff: pending. Relevant environment: pending.

| AC / check | Result | Evidence summary / reference |
| --- | --- | --- |
| AC-01 | Not run | Pending. |

Independent review: to be determined according to level. For L3, record the reviewer, isolation, scope, findings, and resolution; do not claim their approval on their behalf.

Outstanding items / exceptions: not evaluated. A blocked check does not count as passed.

Delivery: not deployed / to be determined. Distinguish verified implementation from deployment; record the environment, date, and authorization only if they actually occurred.
