# Plan: CHG-002-gates-on-behavior | Placeholder checks on values, not prose

Status: `approved` | Technical owner: Idaika Iglesias | Accepted by / date: Idaika Iglesias, 2026-10-19 (in conversation), including the result-cell exception.
Spec: [spec.md](spec.md) | Verification scope: `broad`.

## System inspection

Inspected at base `3d54c13` (main after CHG-001):

- `scripts/sdd/docs.py` `validate_change()` is the only consumer of `PENDING`. It is called by `check_docs()` (all change folders, or one with `--change`), by `changes.py assess()` for `--change`, and by `ci.py assess_ci()` on the candidate using the base's code.
- `PENDING` is searched in: `Level rationale` (line 134), `Scope accepted by / date` and the whole AC section (lines 144, 146, accepted spec), `Accepted by / date` (line 157, accepted plan).
- Targeted checks: `Scope acceptance:\s*pending` over the raw spec (line 148); `Verified version or diff:\s*pending` and completion result cells `| not run | blocked | failed | pending |` over the raw Completion evidence section (lines 172, 177).
- `field()` captures a field value after an optional opening backtick, so `` `TBD` `` yields `TBD`.
- `prose()` already removes fenced and inline code while keeping line numbers; it is used only for link extraction.
- AC IDs come from table rows matching `^\s*\|\s*(AC-\d+)\s*\|` in the AC section.
- Placeholder forms in `docs/templates/spec.md` and `plan.md`: `` `TBD` `` fields, `TBD` AC cells, `TBD - <guidance>` lines, `Scope acceptance: pending.`, `Verified version or diff: pending.`, `Not run` result cells.
- Tests: `scripts/tests/test_docs.py` covers rationale, acceptance fields, AC placeholders (`TBD` cell), mapping, and completion; the fixture spec (`support.py Fixture.change()`) uses only concrete values.
- Reproduction in this repository: with the 1.0.0 checker, this change's approved spec fails with both "accepted criteria contain pending placeholders" (AC-01, AC-02 wording) and "acceptance statement is still pending" (AC-09 quotes the sentence in backticks).

## Technical approach

All logic stays in `scripts/sdd/docs.py`:

1. Replace `PENDING` with two helpers over a cleaned value (whitespace and surrounding backticks removed):
   - `placeholder(value)`: the value fully matches `(TBD|TODO|pending|not run)` (any case), optionally followed by a dash (`-`, en dash, or em dash) and any text. Used for AC cells.
   - `unresolved(value)`: the value is empty, or starts with one of those tokens as a whole word. Used for `Level rationale`, `Scope accepted by / date`, and `Accepted by / date`.
2. AC cells: for each AC table row (the rows whose first cell is `AC-NN`), split cells on unescaped `|` and flag the spec when any cell is a `placeholder`. Prose and header rows are not checked (AC-05).
3. Targeted sentence checks run on `prose(text)`, so quoted code is ignored (AC-12): `Scope acceptance:\s*pending` on the spec, `Verified version or diff:\s*pending` on the Completion evidence section.
4. Completion result cells keep their current rule on the raw section: a cell whose whole content is an unresolved result fails, also when backticked. Rationale: the cell's whole content is the result, so a backticked `not run` is still an unresolved result, not a quotation. This is the only targeted check not moved to `prose()`.
5. Error messages are unchanged, so adopters' tooling and docs stay valid.

Rejected alternatives:

- Strip code spans only (feedback option 1): fixes `` `Changes pending` `` but keeps failing plain domain prose ("shows as pending").
- Drop `pending`/`not run` from the pattern (option 3): the shipped templates use `pending` in acceptance statements, so real placeholders would pass.
- An evidence-reference check: rejected in the spec (non-goal).

## Affected components and contracts

| Area / path | Proposed change | Impact / consumer |
| --- | --- | --- |
| `scripts/sdd/docs.py` | Value-based placeholder helpers; AC cell check; targeted sentences on `prose()` | `check-docs`, `check-change-level --change`, `verify` with `--change`, CI candidate validation (after merge, as base) |
| `scripts/tests/test_docs.py` | Regression and negative tests for AC-01 to AC-09 and AC-12 | Framework automation tests |
| `docs/development/methodology.md` section 8, `.agents/references/handoffs.md` | Evidence-reference guidance (L1: PR CI; L2/L3: CI run or `verify` report with snapshot, or manual procedure) | Human and agent readers |
| `CHANGELOG.md` | `Unreleased` / Changed entry | Adopters |
| `FEEDBACK-pending-placeholder-false-positive.md` | Deleted (untracked input) once covered | None |

## Risk-proportionate strategy

| Area | Decision, check, or reason for non-applicability |
| --- | --- |
| Compatibility and consumers | The gate only accepts more documents; every template placeholder form still fails (tests per form). Error messages unchanged. `ci.py` uses the base's `docs.py`, so in adopters the new rule applies only after this change is in the base; until then their PRs see the stricter 1.0.0 rule, which is safe. `docs/specs/` of this repository is not product content for adopters. |
| Data, integrity, and migration | N/A - no persistent data or schema. |
| Permissions, security, and privacy | N/A - no permission or credential path; parsing stays regex-based over repository Markdown, with no execution. |
| Failures, load, and availability | Risk: letting a real placeholder through. Mitigation: negative tests for each shipped placeholder form, case variants, backticks, and dash guidance; a test that the unmodified templates, copied as accepted records, fail. |
| Change observability | Same messages and report shape; behavior differences are visible only as fewer false failures. |
| Rollout and feasible recovery | Ships with the 2.0.0 rollout through this PR. Recovery: revert the squash commit; no state to undo. |

## Implementation steps

1. `docs.py` helpers and AC cell check, with tests for AC-01 to AC-08 and the template-copy negative test.
2. Targeted sentence checks on `prose()`, with tests for AC-09 and AC-12.
3. Guidance in methodology and handoffs (AC-11); CHANGELOG entry.
4. Remove the feedback file; run broad verification (AC-10); independent review.

## Verification plan and traceability

Environment: Windows 11 with Python 3; Linux via WSL Ubuntu for the full suites. This clone declares `sdd.defaultBranch main`.

| AC / risk | Test, check, or manual procedure | Command / location / environment | Expected result |
| --- | --- | --- | --- |
| AC-01, AC-02, AC-05 | Approved fixture spec with `` `Changes pending` ``, "shows as pending", "pending payment", and prose outside the table | `scripts/tests/test_docs.py` | No placeholder error |
| AC-03, AC-04 | Approved fixture spec with AC cells `TBD`, `` `TBD` ``, `TODO`, `pending`, `Not run`, `TBD - guidance` | `test_docs.py` (one subtest per form) | "pending placeholders" error each time |
| AC-06, AC-07 | Field values only placeholder, starting with one, and concrete with a later placeholder word | `test_docs.py` | Fails, fails, passes |
| AC-08 | Draft spec and plan with placeholders | `test_docs.py` | No placeholder errors |
| AC-09, AC-12 | Sentences with and without backticks; backticked and plain unresolved result cells | `test_docs.py` | Plain sentences fail, quoted pass; result cells fail in both forms |
| Template risk | Copy `docs/templates/spec.md` and `plan.md` as approved/completed records | `test_docs.py` | Fails with placeholder errors |
| AC-10 | Repository change records and full framework verification | `python3 scripts/check-docs`; `python3 scripts/verify broad --target framework --base main --level L3 --change CHG-002-gates-on-behavior` | Passed, including this change's own approved spec |
| AC-11 | Inspection | Diff review and independent review | Guidance present |
| Level floor | Change-level check | `python3 scripts/check-change-level --base main --level L3 --change CHG-002-gates-on-behavior --scope broad` | Passed |
| L3 review | Independent review in a fresh session | `sdd-independent-review` agent with `.agents/review/independent-review.md` | Findings recorded and resolved |

## Affected documentation

`docs/development/methodology.md` (section 8), `.agents/references/handoffs.md`, `CHANGELOG.md`. Templates are unchanged (CHG-004).

## Deviations and decisions during execution

None recorded yet.

## Completion evidence

Verified version or diff: pending. Relevant environment: pending.

| AC / check | Result | Evidence summary / reference |
| --- | --- | --- |
| AC-01 to AC-12 | Not run | Pending implementation. |

Independent review: pending; required for L3.

Outstanding items / exceptions: `sdd-gate` is skipped in this repository by design.

Delivery: not merged; not released.
