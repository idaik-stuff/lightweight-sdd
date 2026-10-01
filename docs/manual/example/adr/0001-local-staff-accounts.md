# ADR-0001: Local staff accounts instead of the city's single sign-on

> Fictitious example. See the [example index](../README.md).

Status: `accepted` | Date: 2026-04-05 | Owner: Tom Berg.
Accepted by / date: Tom Berg and Ana Ruiz, 2026-04-05 | Related change or plan: [CHG-002](../CHG-002-sign-in-and-permissions/plan.md).
Supersedes: `N/A` | Superseded by: `N/A`.

## Context and decision drivers

Staff must sign in to the desk app ([CHG-002](../CHG-002-sign-in-and-permissions/spec.md)).
The library belongs to the city, which offers a single sign-on service to its
employees. Most desk staff are volunteers who are not city employees.

## Alternatives considered

1. **City single sign-on.** No passwords stored by us; accounts managed by the city.
   But volunteers have no city accounts, getting them takes weeks per person, and the
   desk stops working whenever the city service is down.
2. **Local accounts in the app.** Works for volunteers immediately and offline from
   the city. We must store passwords safely and manage accounts ourselves.
3. **Shared desk password plus names typed per action.** Simple, but it does not
   identify who acted and does not protect deletion.

## Decision

Option 2: local accounts, with administrators managing staff accounts at the desk.

## Consequences

- We are responsible for password storage, lockout, and session handling; these are
  covered by the CHG-002 plan and its independent review.
- Staff have one more password to remember; administrators reset it at the desk.
- If the city later offers accounts to volunteers, moving to single sign-on is a new
  decision in a new ADR; the central sign-in hook keeps that change contained.

## Validation and future review

Validated by the CHG-002 tests and independent review. Reconsider if the city offers
accounts to volunteers, or if the library adds a second branch with shared staff.
