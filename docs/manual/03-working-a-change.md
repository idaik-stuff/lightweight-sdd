# 3. Working a change

This chapter follows four changes to a small library book-loan app, one per level,
from request to completion. It shows what you ask the agent, what you should get back,
and what you record. The [worked example](example/README.md) contains the finished
artifacts. The procedures themselves are in the
[workflow sources](../../.agents/workflows/spec/SKILL.md) and the
[methodology](../development/methodology.md); the commands are in the
[README](../../README.md#commands).

Prompts below use Claude Code syntax (`/sdd-...`). In Codex use `$sdd-...`; Cursor and
Copilot VS Code use the same `/sdd-...` names. Chapter 5 covers the differences.

## The shape of every change

```text
classify ──> [investigate] ──> [spec ──> accept] ──> [plan ──> accept] ──> implement ──> verify ──> [review] ──> complete
             if cause unknown   L2/L3 only            L2/L3 only           explicit only              L3 only
```

Three rules hold at every level:

1. **Classify first, by risk.** Record the level and a one-sentence rationale.
2. **One workflow at a time.** Each one stops and reports. The next one runs only when
   you ask for it, and implementation only when you select it explicitly.
3. **Evidence belongs to the final change.** If the code changes after a check ran,
   the check runs again.

## Classifying

Work through the questions in the order `AGENTS.md` uses:

1. Could it touch a public contract, permissions or security, persistent data,
   something irreversible, an architectural boundary, or critical availability? → **L3**.
2. Does nothing observable change at all? → **L0**.
3. Is it a local fix or refactor of existing behavior with no new capability? → **L1**.
4. Otherwise, it intentionally adds or changes behavior → **L2**.

When you are unsure whether an L3 trigger applies, investigate enough to decide; do
not guess low. The criteria are in the
[classification table](../../AGENTS.md#classification-and-routing), and the reasoning
is in [starting and classifying work](../development/methodology.md#1-starting-and-classifying-work).

You can also ask the agent to classify before doing anything:

```text
Classify this request under AGENTS.md and explain why. Do not change anything yet:
members say the due date shown after borrowing a book is sometimes one day early.
```

## L0: a typo in the help page

**Request.** The help page says "retrun" instead of "return".

```text
/sdd-implement Fix the misspelling "retrun" in the help page. Change nothing else.
```

**What happens.** The agent confirms the change is L0 (no behavioral, contractual, or
operational effect), edits the one word, and verifies with a focused check: for a
document, a targeted `python3 scripts/check-docs <path>` plus inspecting the diff.

**What to watch.** A text change is not automatically L0. If the "typo" were in a
recovery runbook step or an error code that clients parse, it would change behavior.

**What you record.** The level and evidence go in the commit message or PR. No spec,
no plan:

```text
Fix typo in help page

Level: L0 - wording only; no behavioral or operational effect.
Checks: check-docs on the changed file passed; diff reviewed.
```

In the PR template, set `Change-Level: L0` and leave `Change-ID: none`.

## L1: due dates one day early

**Request.** Members report that the due date is sometimes a day early. The cause is
unknown, so start by investigating:

```text
/sdd-investigate Members say the due date shown after borrowing is sometimes one day
early. Find the cause. Do not modify code.
```

**What you get back.** The question, the level with its rationale, the evidence with
file and test locations, whether the bug was reproduced, a cause marked `confirmed`,
`likely`, or `unresolved`, the affected areas, a minimal fix direction, and a
suggested regression test. Here: loans created near midnight compute the due date in
UTC while the page shows local time. The cause is confirmed by a reproducing test
input.

**Check the level again.** The investigation also traces impact. If it found that the
same date drives overdue fines already stored in the database, correcting it might
mean repairing persisted data. That would be an L3 data concern, and the change would
be reclassified before going further. Here the date is only computed at display time,
so it stays L1.

**Authorize the fix.**

```text
/sdd-implement Apply the fix from the investigation. Add a regression test that fails
before the fix and passes after it. Do not expand the scope.
```

**Verify.** L1 uses focused or standard verification locally. The CI gate always runs
standard for L1.

```bash
python3 scripts/verify standard --base main --level L1
```

Replace `main` with the base you actually intend: the runner never assumes one.

**What you record.** As for L0, the commit message or PR holds the level, rationale,
change, checks, and limitations, including the regression test's before/after result.

## L2: reserving a book that is on loan

**Request.** Members want to reserve a book that is currently on loan and be first in
line when it comes back. This is intentionally new behavior with no L3 trigger
(assuming reservations do not change who may do what), so it is L2.

### Spec

```text
/sdd-spec Define CHG-001-book-reservations: members can reserve a book that is on
loan. Draft the spec only.
```

The agent creates `docs/specs/CHG-001-book-reservations/spec.md` from the
[spec template](../templates/spec.md): problem and goal, current behavior, scope and
non-goals (for example "no notifications in this change"), expected behavior, and
acceptance criteria such as:

| ID | Scenario / precondition | Action | Observable outcome |
| --- | --- | --- | --- |
| AC-01 | Book is on loan; member has no reservation for it. | Member reserves it. | Reservation is listed with queue position 1. |
| AC-02 | Book is available on the shelf. | Member tries to reserve it. | Reservation is refused with a message to borrow it instead. |
| AC-03 | Book with two reservations is returned. | Librarian checks the book in. | It is held for the first member in the queue. |

It asks only the blocking questions (for example: may a member hold several
reservations?). It leaves the plan link as pending text and the spec in `draft`.

**Accept the scope.** The product owner reviews the spec. Acceptance is recorded in
the spec header: the `approved` status, plus who accepted it and when. The agent never
fills this in on its own. If you already said "this scope is accepted" in the
conversation, that counts; there is no need to confirm it twice.

You can merge the draft or approved spec on its own in a documentation-only PR. CI
recognizes it as design-only and does not ask for an implementation.

### Plan

```text
/sdd-plan CHG-001-book-reservations. Inspect the repository and write the plan. Do not
implement.
```

The agent inspects the real code (the loan model, the check-in flow, existing tests)
and writes `plan.md` from the [plan template](../templates/plan.md): the smallest
approach, the affected components, the applicable risks, the implementation steps, and
a traceability table that maps every AC to a real check:

| AC / risk | Test, check, or manual procedure | Command / location / environment | Expected result |
| --- | --- | --- | --- |
| AC-01, AC-02 | Reservation service unit tests | Product `standard` profile | Pass |
| AC-03 | Check-in integration test | Product `standard` profile | Pass |

**Accept the approach.** The technical owner reviews and accepts the plan, which is
recorded in its header. If something in the spec turns out to be wrong while planning,
the fix goes back to the spec. The plan never quietly changes requirements.

### Implement and verify

```text
/sdd-implement CHG-001-book-reservations. Implement the accepted spec and plan, then
verify.
```

The agent marks the plan `in-progress`, implements one bounded step at a time with
tests, and records minor deviations in the plan. A material deviation (scope,
contract, or risk changes) stops the affected work until the spec or plan is revised
and accepted again.

Verification for L2 is standard and names the change:

```bash
python3 scripts/verify standard --base main --level L2 --change CHG-001-book-reservations
```

**What you record.** The plan's *Completion evidence* section gets the verified
version or diff, the environment, and a result per AC. Then:

- the spec moves to `implemented` and the plan to `completed`, but only when every AC
  has evidence and the gates are met;
- affected living documents are updated: the PRD capability becomes `implemented`,
  and the architecture overview mentions reservations if its description changed.

In the PR, set `Change-Level: L2` and `Change-ID: CHG-001-book-reservations`.

## L3: sign-in and permissions

**Request.** Until now anyone at the desk could do anything. The library wants staff
to sign in, and only administrators to delete members. This is L3: it creates a
security boundary and changes who can do what.

The route is the same as L2, with four additions.

**1. Strategy in the plan.** The plan's *risk-proportionate strategy* table must
address each area explicitly: compatibility (existing desk workflows), data (existing
members, a first administrator), security (password storage, sessions, lockout),
failures, observability (sign-in failures are visible), and rollout and recovery
(what if no one can sign in?). An area that does not apply gets `N/A - reason`, not
silence. The [risk checks](../../.agents/references/risk-checks.md) give the questions
for each area.

**2. An ADR when there is a real decision.** "Local accounts or the city's single
sign-on?" has real alternatives and lasting consequences, so it gets an ADR from the
[template](../templates/adr.md). A choice of library for password hashing usually does
not need one; the plan is enough.

**3. Broad verification.** Broad adds contract, integration, and risk-specific checks:
here, tests that a non-administrator really is refused, not only that an administrator
succeeds.

```bash
python3 scripts/verify broad --base main --level L3 --change CHG-002-sign-in-and-permissions
```

**4. Independent review after initial verification.**

```text
Use sdd-independent-review in a fresh context for CHG-002-sign-in-and-permissions.
Supply the packet required by .agents/review/independent-review.md, including the
complete scoped patch and the initial verification evidence. Do not pass the
implementation conversation. Return findings only.
```

The reviewer reads the spec, plan, diff, and evidence with read-only tools and returns
findings with location, risk, and evidence. Blocking findings are fixed through
`/sdd-implement`, the affected checks are rerun, and material corrections are reviewed
again. The plan records who or what reviewed the change, the isolation used, the
findings, and how each was resolved.

If no suitable reviewer is available, the gate stays pending. It is never declared
satisfied by the author.

## When things do not go to plan

| Situation | What to do |
| --- | --- |
| Work reveals a higher risk | Reclassify, and create or extend the spec and plan before continuing the affected work. Unaffected work may continue. |
| A material deviation from the plan | Stop that part, revise the spec or plan, and get the acceptance again. Minor deviations are noted in the plan. |
| A required check cannot run | Record it as `blocked` with its impact and the action needed. It is not a pass, and the change is not complete. |
| A check was already failing before the change | Record it as pre-existing. It still does not make the gate pass. |
| Something is urgent | The level does not drop. A deferred gate becomes an authorized exception with an owner and a date; see [exceptions](../development/methodology.md#9-exceptions-and-urgent-work). |
| Work continues in a new session | Hand off with the compact [handoff block](../../.agents/references/handoffs.md), not the conversation. The new session rereads the current files and worktree. |

## Completion

A change is complete when the scope is resolved, every applicable AC has evidence,
the required gates are met, and the affected documents describe the result. Statuses
reflect that, and nothing more:

| Artifact | Typical path | Meaning of the final state |
| --- | --- | --- |
| Spec | `draft` → `approved` → `implemented` | AC satisfied and gates complete. |
| Plan | `draft` → `approved` → `in-progress` → `completed` | Execution and evidence final; nothing blocking hidden. |

"Implemented" never means "deployed". Delivery is recorded separately in the plan, and
only when it actually happened. After completion, specs and plans are records: later
changes link to them instead of rewriting them. See the
[specs index](../specs/README.md#states).

## Common mistakes

- Treating a request to design or investigate as permission to write code.
- Letting the agent fill in an acceptance field, approver, or date.
- Writing "works correctly" as an acceptance criterion.
- Creating extra files by default: `tasks.md`, `investigation.md`, `verification.md`.
- Calling a framework-only pass, a dry run, or a check that ran before the last edit
  "verified".
- Lowering the level because the diff is small or the change is urgent.

## Next

The next chapter goes deeper into verification: registering checks, reading the
evidence report, and the CI gate.
