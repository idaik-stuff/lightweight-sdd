# Worked example: a library book-loan app

> **Fictitious example.** Every name, person, date, commit, and result below is
> invented to illustrate the framework. None of it is evidence of anything. The files
> live under `docs/manual/example/` so that the framework's tools never mistake them for
> real change records.

This example follows a small team through four changes to the same product, one per
level. [Chapter 3](../03-working-a-change.md) explains the route; this folder shows the
finished artifacts.

## The product

Riverside Community Library lends books to its members. A small web app used at the
front desk records loans and returns. The team is two people: Ana Ruiz (product owner)
and Tom Berg (developer and technical owner). They work with an AI coding agent.

At the start of the example, the app can register members, lend a book, show its due
date, and check it back in. There is no sign-in: anyone at the desk can do anything.

An excerpt from the product documents they maintain:

| Document | Excerpt |
| --- | --- |
| Brief | "Let volunteers at the front desk lend and return books quickly, and let members know when their books are due." |
| MVP | Includes members, loans, returns, and due dates. Excludes reservations, fines, and online access for members. |
| PRD | `CAP-01` Lend a book (`implemented`). `CAP-02` Return a book (`implemented`). `CAP-03` Reserve a book on loan (`planned`). `NFR-01` Only staff may change member records (`planned`). |
| Architecture | A single Python web service with a SQLite database; one `loans` module and one `members` module. |

## Adoption decisions

When the team adopted the framework, they reviewed `.sdd/risk-rules.json` against their
layout (an L3 change of its own, reviewed by a volunteer developer from another
library). One decision matters for this example: the template's `persistent-data` rule
raises every change under `migrations/` to L3. `AGENTS.md` makes a migration L3 only
when it carries material risk, so the team lowered that floor to L2. A migration now
always needs at least a spec and plan, and the team still classifies risky migrations
(rewriting or deleting existing data) as L3 by judgment.

## The four changes

| Level | Change | Artifacts |
| --- | --- | --- |
| L0 | Fix the "retrun" typo in the help page. | Commit message only ([below](#l0-commit)). |
| L1 | Due dates shown one day early for loans near midnight. | Commit message only ([below](#l1-commit)). |
| L2 | Members can reserve a book that is on loan. | [spec](CHG-001-book-reservations/spec.md) and [plan](CHG-001-book-reservations/plan.md). |
| L3 | Staff sign-in; only administrators may delete members. | [spec](CHG-002-sign-in-and-permissions/spec.md), [plan](CHG-002-sign-in-and-permissions/plan.md), and [ADR 0001](adr/0001-local-staff-accounts.md). |

In a real repository, change folders live in `docs/specs/<change-id>/` and ADRs in
`docs/adr/`.

<a id="l0-commit"></a>

## L0: commit message

```text
Fix typo in help page

Level: L0 - wording only; no behavioral, contractual, or operational effect.
Change: "retrun" -> "return" in templates/help.html.
Checks: diff reviewed; page renders (manual check). No product checks needed.
```

PR metadata: `Change-Level: L0`, `Change-ID: none`.

<a id="l1-commit"></a>

## L1: commit message

The investigation found that `loans.due_date()` computed the date in UTC while the
desk displays local time, so loans created between 00:00 and 01:00 local time showed
a due date one day early. Due dates are computed on display and never stored, so no
data repair was needed and the change stayed L1.

```text
Compute loan due dates in the library's local time zone

Level: L1 - local fix of existing behavior; due dates are computed on
display and not persisted, so no data or contract is affected.
Cause: due_date() used UTC; the desk shows local time (Europe/Madrid).
Regression test: test_due_date_near_midnight failed before the fix
(expected 2026-03-16, got 2026-03-15) and passes after it.
Checks: verify standard --base main --level L1 at 8a41c07: passed
(lint, unit-tests, integration-tests).
Limitations: none known.
```

PR metadata: `Change-Level: L1`, `Change-ID: none`.

## What to notice

- **L0 and L1 leave no files behind.** The commit message is the change record.
- **The L1 investigation checked for hidden L3 risk** (stored dates) before settling
  the level.
- **The L2 spec says what, not how.** The table design is in the plan.
- **The L2 plan maps every AC to a check** and records the evidence at the end.
- **The L3 plan addresses every risk area explicitly,** using `N/A - reason` where an
  area does not apply.
- **The L3 ADR records the one decision with real alternatives** (local accounts
  versus the city's single sign-on). Smaller choices stay in the plan.
- **The independent review found real problems,** and the plan records how each was
  resolved and rechecked.
- **Living documents were updated by the changes,** for example the PRD status of
  `CAP-03` and the architecture overview after sign-in was added.
