# Plan: CHG-002-sign-in-and-permissions | Staff sign-in and administrator-only member deletion

> Fictitious example. See the [example index](../README.md).

Status: `completed` | Technical owner: Tom Berg | Accepted by / date: Tom Berg, 2026-04-07.
Spec: [spec.md](spec.md) | Verification scope: `broad`.

## System inspection

Read every view module under `app/`, the request handling in `app/web.py`, the
`members`, `loans`, and `reservations` services, and their tests. Confirmed: no
authentication exists; views call services directly; member deletion is a single
service function also reachable by a direct POST. The existing tests call views
without any session.

## Technical approach

Local staff accounts as decided in [ADR 0001](../adr/0001-local-staff-accounts.md).
Authentication is enforced in one place: a request hook in `app/web.py` that rejects
every request except sign-in without a valid session. Authorization for member deletion
is checked in the `members` service, not only the view, so every path to deletion is
covered. Passwords use the standard library's `hashlib.scrypt` with a per-user salt.
Sessions are server-side rows with an expiry time; the cookie holds only a random ID.

Rejected: checking permissions in each view, which is easy to forget for a new view.

## Affected components and contracts

| Area / path | Proposed change | Impact / consumer |
| --- | --- | --- |
| `app/auth/` (new) | Accounts, password hashing, sessions, lockout. | Every request. |
| `app/web.py` | Request hook enforcing sign-in. | Every page and action. |
| `app/members/service.py` | Administrator check on deletion. | Member deletion. |
| `app/loans/`, `app/reservations/` | Record the acting staff member. | New records only. |
| `migrations/0005_staff.py` (new) | `staff`, `sessions` tables; nullable `staff_id` on records. | Additive; existing rows keep `NULL`. |

## Risk-proportionate strategy

| Area | Decision, check, or reason for non-applicability |
| --- | --- |
| Compatibility and consumers | No external consumers. Desk users must sign in from release day: announced a week before; administrators created in advance. |
| Data, integrity, and migration | Additive migration; existing rows get `staff_id = NULL` and display as "before sign-in". Tested on a copy of the production database with row counts compared. |
| Permissions, security, and privacy | Sign-in enforced centrally; deletion checked in the service; scrypt hashing; lockout after 5 failures; session cookie `HttpOnly` and `SameSite=Strict`; passwords never logged (test asserts log output). |
| Failures, load, and availability | If sign-in breaks, the desk cannot work. Mitigation: rollback path below, tested; paper fallback as today. |
| Change observability | Sign-ins, failures, lockouts, and deletions are logged with staff name and time, without passwords. |
| Rollout and feasible recovery | Database backup before release. Rollback: redeploy the previous version; the additive migration is harmless to it (rehearsed on the copy). |

## Implementation steps

1. Accounts, hashing, sessions, lockout, and first administrator, with unit tests (AC-02, AC-03, AC-07, AC-08).
2. Central request hook; update existing tests to sign in (AC-01).
3. Service-level deletion check and staff recording (AC-04, AC-05, AC-06).
4. Migration rehearsal and rollback rehearsal on the database copy.

## Verification plan and traceability

| AC / risk | Test, check, or manual procedure | Command / location / environment | Expected result |
| --- | --- | --- | --- |
| AC-02, AC-03, AC-07, AC-08 | `tests/auth/` | `verify broad` (unit-tests) | Pass |
| AC-01 | `tests/web/test_requires_sign_in.py`: every registered route without a session | `verify broad` (integration-tests) | All refused |
| AC-04, AC-05 | `tests/members/test_delete_permissions.py`, through the view and directly | `verify broad` (integration-tests) | Pass |
| AC-06 | `tests/loans/test_staff_recorded.py` | `verify broad` (integration-tests) | Pass |
| No plain-text passwords | Test asserting logs and the database contain no password | `verify broad` (unit-tests) | Pass |
| Migration and rollback | Apply `0005` to a copy; run the previous version against it | Manual, staging laptop | Counts unchanged; previous version works |

## Affected documentation

PRD: `NFR-01` becomes `implemented`. Architecture overview: new "Security" section
(accounts, sessions, central enforcement) and the `auth` module. README: the
first-administrator configuration values.

## Deviations and decisions during execution

2026-04-15: review finding R-1 (below) added a check to the CSV export view, which was
outside the original list of affected views. Same scope and AC; recorded here.

## Completion evidence

Verified version or diff: `main..e52b0aa`. Relevant environment: Python 3.12, SQLite 3.45.

| AC / check | Result | Evidence summary / reference |
| --- | --- | --- |
| AC-01 | Passed | `verify broad --base main --level L3 --change CHG-002-sign-in-and-permissions` at e52b0aa; all 37 routes refused without a session. |
| AC-02, AC-03, AC-07, AC-08 | Passed | Same run; tests/auth 24 passed. |
| AC-04, AC-05 | Passed | Same run; direct POST by a volunteer returns 403. |
| AC-06 | Passed | Same run. |
| No plain-text passwords | Passed | Same run. |
| Migration and rollback | Passed | Copy of the 2026-04-18 database: counts unchanged; previous version started and lent a book against the migrated database. |

Independent review: a fresh Claude Code session using `sdd-independent-review` (tools
limited to Read, Grep, Glob; confirmed in the agent list), given the spec, plan,
complete diff `main..41f0c2d`, and the initial broad evidence. No access to the
implementation conversation. Limitation: same model family as the implementing agent;
no human security review. Findings:

| ID | Finding | Resolution |
| --- | --- | --- |
| R-1 | Blocking: the CSV export of members (`app/members/export.py`) is served by a route registered before the request hook, so it is reachable without signing in. | Route moved under the hook; AC-01 test changed to enumerate routes from the app instead of a fixed list. Rerun at e52b0aa passed. |
| R-2 | Blocking: lockout counter resets on any successful sign-in to *any* account from the same desk, not per account. | Counter made per account; AC-03 test extended. Rerun passed. |
| R-3 | Non-blocking: session IDs are compared with `==`. | Changed to `hmac.compare_digest`. |

The corrections were reviewed again by a new fresh session with the same packet
updated to `main..e52b0aa`: no further findings.

Outstanding items / exceptions: none.

Delivery: released to the desk on 2026-04-21 by Tom Berg, after a backup.
