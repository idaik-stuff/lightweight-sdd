# Spec: CHG-002-sign-in-and-permissions | Staff sign-in and administrator-only member deletion

> Fictitious example. See the [example index](../README.md).

Status: `implemented` | Level: `L3` | Level rationale: creates a security boundary (authentication) and changes who may perform actions on member records.
Owner: Ana Ruiz | Scope accepted by / date: Ana Ruiz, 2026-04-06.

## Problem and goal

Anyone using the desk computer can do anything, including deleting members. Last month
a member record was deleted by mistake and could not be recovered. We want every desk
user to sign in, and only administrators to delete members, so that mistakes are
limited and every action can be traced to a person.

## Context and current behavior

The app has no notion of users. All actions are anonymous. The PRD requirement
`NFR-01` ("Only staff may change member records") is `planned`. The decision on how
staff authenticate is recorded in [ADR 0001](../adr/0001-local-staff-accounts.md).

## Scope and non-goals

Includes: staff accounts with roles `volunteer` and `administrator`; sign-in and
sign-out; session expiry; locking after repeated failures; restricting member deletion
to administrators; recording which staff member performed each loan, return,
reservation, and deletion; creating the first administrator.

Does not include: member (patron) accounts or online access; single sign-on (see the
ADR); password reset by email (administrators reset passwords at the desk).

## Expected behavior

- Every page except sign-in requires a signed-in staff member.
- Volunteers can do everything they can do today except delete members.
- Administrators can also delete members and manage staff accounts.
- A session ends after 8 hours or on sign-out.
- Five failed sign-ins in a row lock the account for 15 minutes.
- Every loan, return, reservation, and member deletion records the staff member.
- On first start, if no administrator exists, one is created from configured values.

## Acceptance criteria

| ID | Scenario / precondition | Action | Observable outcome |
| --- | --- | --- | --- |
| AC-01 | Not signed in. | Open any page other than sign-in, or call any action. | Redirected to sign-in; no data shown; action not performed. |
| AC-02 | Valid volunteer account. | Sign in with the correct password. | Desk home is shown with the volunteer's name. |
| AC-03 | Account exists. | Sign in with a wrong password five times. | Account locked for 15 minutes; a correct password is refused during that time. |
| AC-04 | Signed-in volunteer. | Try to delete a member, through the page or a direct request. | Refused (403); member unchanged. |
| AC-05 | Signed-in administrator. | Delete a member. | Member deleted; deletion recorded with the administrator's name. |
| AC-06 | Signed-in volunteer. | Lend a book. | Loan recorded with the volunteer's name. |
| AC-07 | Session started 8 hours ago. | Perform any action. | Redirected to sign-in; action not performed. |
| AC-08 | Empty staff table, first-administrator values configured. | Start the app. | One administrator exists; starting again creates no other. |

## Constraints and compatibility

Existing members, books, loans, and reservations must be preserved unchanged. Records
created before this change have no staff member and must still display. Passwords must
never be stored or logged in plain text.

## Uncertainties

| Question / assumption | Owner | Blocks | Resolution or evidence |
| --- | --- | --- | --- |
| Local accounts or the city's single sign-on? | Tom Berg | Approach | Local accounts; see ADR 0001 (2026-04-05). |
| How are forgotten passwords handled? | Ana Ruiz | AC set | Administrator resets at the desk; no email (2026-04-06). |

## Acceptance and next steps

Scope acceptance: accepted by Ana Ruiz on 2026-04-06.

Related plan: [plan.md](plan.md). States and completion rules: `docs/specs/README.md`.

Implemented on 2026-04-20; evidence and the independent review are recorded in the plan.
