# Plan: CHG-001-book-reservations | Reserve a book that is on loan

> Fictitious example. See the [example index](../README.md).

Status: `completed` | Technical owner: Tom Berg | Accepted by / date: Tom Berg, 2026-03-03.
Spec: [spec.md](spec.md) | Verification scope: `standard`.

## System inspection

Read `app/loans/service.py` (lend and check-in), `app/loans/models.py`,
`app/books/models.py` (availability is derived from open loans), the check-in view,
and `tests/loans/`. Confirmed: availability has no stored status, and check-in is a
single service call wrapped in one database transaction. No existing queue or
reservation concept exists.

## Technical approach

Add a `reservations` module with a `Reservation` model (book, member, created time,
status `active`/`held`/`cancelled`). Queue order is creation time among active
reservations. Check-in calls `reservations.on_return(book)` inside the existing
transaction, so a return and the resulting hold are recorded together. Lending
checks for a hold before creating the loan.

Rejected: storing an explicit position number, which would need renumbering on every
cancellation; ordering by creation time gives the same result with no updates.

## Affected components and contracts

| Area / path | Proposed change | Impact / consumer |
| --- | --- | --- |
| `app/reservations/` (new) | Model, service, views. | New desk screens only. |
| `app/loans/service.py` | Check-in calls `on_return`; lending checks holds. | Lend and check-in for reserved books. |
| `migrations/0004_reservations.py` (new) | Create the `reservations` table. | Additive; no existing data touched. |

## Risk-proportionate strategy

| Area | Decision, check, or reason for non-applicability |
| --- | --- |
| Compatibility and consumers | Books without reservations follow the old paths; covered by the existing loan tests. |
| Data, integrity, and migration | Additive table only; no existing row is changed. `check-change-level` reports the team's `persistent-data` floor (L2) for `migrations/`; the migration has no material risk, so L2 stands. Tested on a copy of the production database. |
| Failures, load, and availability | Check-in and hold share one transaction, so a failure leaves neither. |

Permissions, observability, and rollout: N/A - no permission change; the desk already
logs every action; the release follows the usual process.

## Implementation steps

1. Model, migration, and service with unit tests for AC-01, AC-02, AC-03, AC-06.
2. Check-in and lending integration for AC-04 and AC-05, with integration tests.
3. Desk views and a short manual check of the screens.

## Verification plan and traceability

| AC / risk | Test, check, or manual procedure | Command / location / environment | Expected result |
| --- | --- | --- | --- |
| AC-01, AC-02, AC-03, AC-06 | `tests/reservations/test_service.py` | `verify standard` (unit-tests) | Pass |
| AC-04, AC-05 | `tests/loans/test_checkin_reservations.py` | `verify standard` (integration-tests) | Pass |
| Unchanged loans | Existing `tests/loans/` suite | `verify standard` | Pass |
| Migration | Apply `0004` to a copy of the production database | Manual, staging laptop | Applies; row counts unchanged |

## Affected documentation

PRD: `CAP-03` becomes `implemented`. Architecture overview: add the `reservations`
module and its role in check-in. Help page: add a "Reservations" section.

## Deviations and decisions during execution

2026-03-06: the hold check in lending was moved from the view into the loan service so
that every lending path enforces it. Same scope and AC; recorded here, no new
acceptance needed.

## Completion evidence

Verified version or diff: `main..c7d19e4`. Relevant environment: Python 3.12, SQLite 3.45.

| AC / check | Result | Evidence summary / reference |
| --- | --- | --- |
| AC-01, AC-02, AC-03, AC-06 | Passed | `verify standard --base main --level L2 --change CHG-001-book-reservations` at c7d19e4; unit-tests 61 passed. |
| AC-04, AC-05 | Passed | Same run; integration-tests 14 passed. |
| Unchanged loans | Passed | Same run; existing loan tests unchanged and passing. |
| Migration | Passed | Applied to a copy of the 2026-03-08 database; members 412 and loans 3,980 before and after. |

Independent review: not required for L2. Ana Ruiz approved the PR as the required
human review.

Outstanding items / exceptions: none.

Delivery: released to the desk on 2026-03-10 by Tom Berg.
