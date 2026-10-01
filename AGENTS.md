# Repository instructions

## Permanent rules
- Inspect the code, tests, and applicable instructions before changing anything.
- Apply the minimum process in the table; use only the workflow needed for this change.
- Do not invent requirements or approvals. State assumptions; ask about blocking uncertainties.
- Implement only when authorized to do so. A request to design or investigate does not authorize implementation.
- Make small changes; do not silently expand scope or alter contracts.
- Preserve other people's work. Do not publish secrets or use sensitive data in fixtures or logs.
- Obtain specific authorization before destructive actions, production access, or deployments.
- Record durable decisions in Git and update only the affected documentation.
- Do not claim a check passed without running it; report failures, omissions, and limitations.
- Write all repository artifacts (documentation, specs, ADRs, code, comments, commit messages) in English, regardless of the conversation language.

## Classification and routing
Evaluate L3 first. If it does not apply, evaluate L0, then L1; everything else is L2.
Risk takes precedence over diff size and labels such as "bug" or "refactor".

| Level | Criteria | Minimum workflow |
| --- | --- | --- |
| L0 | Mechanical change with no functional, contractual, or operational effect. | implement -> verify focused |
| L1 | Local fix or refactor, with no new capability or L3 risk. | investigate if the cause is uncertain -> implement -> verify focused/standard |
| L2 | Intentionally new or modified behavior, with no L3 risk. | spec -> plan -> implement -> verify standard |
| L3 | External/public contract; permissions or security boundary; migration with material risk; data loss; irreversible operation; architectural boundary or critical availability. | spec -> plan with strategy (+ design/ADR when appropriate) -> implement -> verify broad + independent review |

For L2/L3, use `docs/specs/<change-id>/spec.md` and `plan.md`; do not generate additional artifacts by default.
For L3, use a different person or an isolated session for review; record its limitations.
If you discover a higher risk, reclassify before continuing the affected work.

## Context on demand
Do not read all of `docs/` at startup or import its documents permanently.
- Purpose and scope: [brief](docs/product/brief.md), [MVP](docs/product/mvp.md), [PRD](docs/product/prd.md).
- Existing system and decisions: [architecture](docs/architecture/overview.md), [ADRs](docs/adr/README.md).
- Gates, verification, and exceptions: [methodology](docs/development/methodology.md).
- Creating a spec, plan, or ADR: templates in `docs/templates/`; read only the one needed.
- Document lifecycle: [index](docs/README.md). Active work: only its spec, plan, and relevant references.

## Workflow entrypoints
Load only `.agents/workflows/<phase>/SKILL.md` for the selected phase; never preload all five.
Use `/sdd-<phase>` in Claude Code, Cursor, or Copilot VS Code; use `$sdd-<phase>` in Codex.
Select this repository's `sdd-implement` explicitly; do not bypass manual invocation by reading its source.
If client controls are unavailable or unqualified, stop implementation and use a qualified client.
For L3, use a fresh reviewer with `.agents/review/independent-review.md`; verify its effective restrictions.
Read [compatibility](docs/development/agent-compatibility.md) or [workflow usage](docs/development/workflows.md) only when needed.

## Commands
The canonical source is the "Commands" section of [README.md](README.md).
Use only existing, documented commands; those marked `TBD` are not configured.
Use `scripts/verify` for configured checks; product verification defaults to blocked until real product checks exist.
For product changes, supply an explicit Git base and declared level; do not infer low risk from unmatched paths.
A framework-only pass does not establish product coverage, approval, independent review, or deployment.

CI uses base-commit policy and the final `sdd-gate`; a green gate does not replace required human reviews.
CI activation and trust boundaries: [enforcement](docs/development/ci-enforcement.md), read only when relevant.

## Completion
Summarize the change and its level, verification evidence, affected documents, and outstanding items.
For L2/L3, retain the evidence summary in `plan.md`; for L0/L1, in the change record.
Do not mark blocked work as verified or claim human approval on someone else's behalf.
