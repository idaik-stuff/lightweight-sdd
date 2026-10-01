# Spec: CHG-001-book-reservations | Reserve a book that is on loan

> Fictitious example. See the [example index](../README.md).

Status: `implemented` | Level: `L2` | Level rationale: new member-facing behavior on existing data; no change to permissions, public contracts, or existing records.
Owner: Ana Ruiz | Scope accepted by / date: Ana Ruiz, 2026-03-02.

## Problem and goal

Members often ask at the desk for a book that is out on loan. Volunteers write their
names on paper, the paper gets lost, and the book goes back on the shelf. We want a
member to be able to reserve a book that is on loan and be first in line when it is
returned.

## Context and current behavior

The app knows whether a book is on loan (`CAP-01`) and records returns (`CAP-02`).
Nothing records interest in a book. The PRD lists reservations as `CAP-03`, `planned`.

## Scope and non-goals

Includes: creating a reservation for a book on loan; listing a book's reservation
queue; holding a returned book for the first member in the queue; cancelling a
reservation.

Does not include: notifying members (email or SMS); reservations for books on the
shelf; limits per member; expiry of uncollected holds. These may be later changes.

## Expected behavior

- A volunteer can reserve a book on loan for a member. Reservations form a queue in
  the order they were made.
- A book on the shelf cannot be reserved; the volunteer is told to lend it instead.
- A member cannot hold two active reservations for the same book.
- When a reserved book is checked in, it is marked as held for the first member in
  the queue, and that reservation leaves the queue.
- A held book can only be lent to the member it is held for.
- Cancelling a reservation removes it and moves later reservations up.

## Acceptance criteria

| ID | Scenario / precondition | Action | Observable outcome |
| --- | --- | --- | --- |
| AC-01 | Book is on loan; member has no reservation for it. | Volunteer reserves it for the member. | Reservation is listed for the book with queue position 1. |
| AC-02 | Book is on the shelf. | Volunteer tries to reserve it. | Refused with "This book is available: lend it instead." No reservation is created. |
| AC-03 | Member already has an active reservation for the book. | Volunteer reserves it again for the same member. | Refused with "Already reserved by this member." Queue unchanged. |
| AC-04 | Book on loan has reservations by members A then B. | Book is checked in. | Book is shown as held for A; B is now at position 1. |
| AC-05 | Book is held for member A. | Volunteer tries to lend it to member B. | Refused with "Held for another member." The loan is not created. |
| AC-06 | Queue has A, B, C. | Volunteer cancels B's reservation. | Queue shows A at 1 and C at 2. |

## Constraints and compatibility

Existing loans, returns, and member records must behave exactly as before for books
with no reservations. No change to who may perform actions (all desk users may manage
reservations, as for loans).

## Uncertainties

| Question / assumption | Owner | Blocks | Resolution or evidence |
| --- | --- | --- | --- |
| May a member hold several reservations for different books? | Ana Ruiz | AC set | Yes, no limit in this change (2026-03-02). |
| What if an uncollected hold is never picked up? | Ana Ruiz | Nothing in this change | Out of scope; volunteers cancel manually for now. |

## Acceptance and next steps

Scope acceptance: accepted by Ana Ruiz on 2026-03-02.

Related plan: [plan.md](plan.md). States and completion rules: `docs/specs/README.md`.

Implemented on 2026-03-09; evidence is recorded in the plan.
