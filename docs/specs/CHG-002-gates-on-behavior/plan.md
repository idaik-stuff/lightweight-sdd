# Plan: CHG-002-gates-on-behavior | Placeholder checks on values, not prose

Status: `in-progress` | Technical owner: Idaika Iglesias | Accepted by / date: Idaika Iglesias, 2026-10-19 (in conversation); the result-cell exception was withdrawn after review with owner acceptance (see Deviations).
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

1. Replace `PENDING` with two helpers over a cleaned value (`clean()`: whitespace including NBSP, list dashes, and emphasis, quote, bracket, and backtick wrappers removed):
   - `placeholder(value)`: the value fully matches `(TBD|TODO|pending|not\s+run)` (any case), with optional closing wrappers and end punctuation, or followed by a dash (`-`, en dash, em dash) or colon and any text. Used for AC cells.
   - `unresolved(value)`: the value is empty, or starts with one of those tokens as a whole word. Used for `Level rationale`, `Scope accepted by / date`, and `Accepted by / date`.
2. AC cells: for each AC table row (the rows whose first cell is `AC-NN`), split cells on unescaped `|` and flag the spec when any cell is a `placeholder`. Prose and header rows are not checked (AC-05).
3. Targeted sentence checks run on `sentences(text)`: the code-stripped text from `prose()`, or the raw text when a fence is left unclosed, so quoted code is ignored (AC-12) without hiding an open sentence: `Scope acceptance:\s*pending` on the spec, `Verified version or diff:\s*pending` on the Completion evidence section.
4. Completion result cells keep the 1.0.0 rule unchanged. (A stricter backtick rule was planned and withdrawn after review: see Deviations.)
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
| Compatibility and consumers | The gate accepts more documents, except near-template placeholders that 1.0.0 missed (`_TBD_`, irregular spacing in `not run`), which now fail as the spec states; every template placeholder form still fails (tests per form). Error messages unchanged. `ci.py` uses the base's `docs.py`, so in adopters the new rule applies only after this change is in the base; until then their PRs see the stricter 1.0.0 rule, which is safe. `docs/specs/` of this repository is not product content for adopters. |
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
| AC-09, AC-12 | Sentences with and without backticks, and an unclosed fence; result cells as in 1.0.0 | `test_docs.py` | Plain sentences fail, quoted pass, unclosed fence still fails; result cells unchanged |
| Template risk | Copy `docs/templates/spec.md` and `plan.md` as approved/completed records | `test_docs.py` | Fails with placeholder errors |
| AC-10 | Repository change records and full framework verification | `python3 scripts/check-docs`; `python3 scripts/verify broad --target framework --base main --level L3 --change CHG-002-gates-on-behavior` | Passed, including this change's own approved spec |
| AC-11 | Inspection | Diff review and independent review | Guidance present |
| Level floor | Change-level check | `python3 scripts/check-change-level --base main --level L3 --change CHG-002-gates-on-behavior --scope broad` | Passed |
| L3 review | Independent review in a fresh session | `sdd-independent-review` agent with `.agents/review/independent-review.md` | Findings recorded and resolved |

## Affected documentation

`docs/development/methodology.md` (section 8), `.agents/references/handoffs.md`, `CHANGELOG.md`. Templates are unchanged (CHG-004).

## Deviations and decisions during execution

- Independent review round 1 (owner accepted the corrections, 2026-10-19, in conversation):
  - F1 (blocking): the planned backtick tightening of completion result cells contradicted the spec ("only accepts more documents") and, through `ci.py` checking every change folder, would have failed historical records in every later PR. Withdrawn: the result-cell rule is unchanged from 1.0.0. The spec's Scope wording now names only the two sentence checks.
  - F2/F3: `clean()` also strips list dashes, emphasis, quotes, and brackets; `PLACEHOLDER` accepts end punctuation, a colon separator, and `not\s+run`, so near-template forms (`TBD.`, `*TBD*`, `(pending)`, `TBD: ...`, `not  run`) keep failing as in 1.0.0.
  - F4: accepted trade-off recorded in the spec's Expected behavior.
  - F5: `sentences()` falls back to raw text when a fence is left unclosed.
  - F6: tests for rationale starting with a token, whole backticked field replacement, the plan template as a completed record, and the exact-state trade-off.

## Completion evidence

Verified version or diff: working snapshot on branch `chg-002-gates-on-behavior` after both review rounds (HEAD `7da8814` plus uncommitted changes; snapshot recorded in the Broad gate row), base `main` (`3d54c13`). Earlier runs: `31cfa68bf1ff7074` (before review), `4331cfe03e9e5a07` (after round 1 corrections).
Relevant environment: Windows 11, Git for Windows, Python 3.14.7; Linux via WSL Ubuntu (native ext4 copy written from the index), Python 3.14.4. This clone declares `sdd.defaultBranch main` and has `origin/HEAD` -> `main`.

Pre-fix evidence: with the new tests and the 1.0.0 `docs.py`, `test_docs.py` had 10 failures, all in the false-positive and strengthened cases (domain vocabulary, prose outside the table, concrete fields with later words, quoted sentences, and the since-withdrawn backticked result cells); the negative cases already passed. This change's own approved spec also failed `check-docs` with both messages before the fix.

| AC / check | Result | Evidence summary / reference |
| --- | --- | --- |
| AC-01, AC-02 | Passed | `test_domain_vocabulary_in_criteria_is_not_a_placeholder`: `` `Changes pending` ``, "shows as pending", "pending payment", "TODO items remain". |
| AC-03, AC-04 | Passed | `test_placeholder_criteria_cells_rejected` (24 forms: case, backticks, emphasis, brackets, quotes, end punctuation, dash and colon guidance, irregular spacing in `not run`), `test_exact_state_name_cell_is_a_placeholder`, and `test_placeholder_in_any_criteria_column_rejected`. |
| AC-05 | Passed | `test_prose_outside_the_criteria_table_is_not_checked`. |
| AC-06 | Passed | `test_acceptance_fields_starting_with_placeholder_rejected` (spec and plan; 9 forms including `` `TBD` ``, `pending owner review`, `(pending)`, `*TBD*`, `- pending`), `test_rationale_starting_with_placeholder_rejected`. |
| AC-07 | Passed | `test_concrete_fields_with_later_placeholder_word_pass`. |
| AC-08 | Passed | `test_draft_records_are_not_checked_for_placeholders`. |
| AC-09, AC-12 | Passed | `test_targeted_sentences_fail_unless_quoted`, `test_completed_plan_verified_sentence_fails_unless_quoted`, `test_sentence_quoted_in_closed_fence_passes`, `test_unclosed_fence_does_not_hide_open_sentences`, `test_unresolved_result_cells_keep_the_1_0_rule`. |
| Template risk | Passed | `test_unchanged_templates_as_accepted_records_fail`: as approved records, rationale, scope acceptance, AC placeholders, acceptance statement, and technical acceptance; as implemented/completed, version/diff and unresolved result. |
| AC-10 | Passed | `python3 scripts/check-docs`: 64 files, 2 change records, passed, including this spec and the CHG-001 record. |
| AC-11 | Passed (review) | Guidance added to methodology section 8 and handoffs "Verification evidence". |
| Full suites | Passed | Windows: 214 automation tests (6 platform skips) and 57 adapter tests. Linux native ext4 copy: 214 (1 skip) and 57. |
| Level floor | Passed | `python3 scripts/check-change-level --base main --level L3 --change CHG-002-gates-on-behavior --scope broad`: floor L3 (`verification-controls`). |
| Broad gate | Passed | `python3 scripts/verify broad --target framework --base main --level L3 --change CHG-002-gates-on-behavior`: docs, adapters, adapter-tests, automation-tests passed on snapshot `c383321f15a5b3dd`; report `.sdd/results/verify-20261019T122851577361Z-6e6801cd.json` (local, untracked); only this line changed afterwards. |

Independent review: automated reviewer (`sdd-independent-review`, Claude sub-agent), fresh context without the implementation conversation (a different reviewer from CHG-001), read-only tools; it ran no code, and every count, hash, and result it cites is requester-supplied. Round 2 resumed the same reviewer context. Not a human review or approval.

| Round | Target | Result | Resolution |
| --- | --- | --- | --- |
| 1 | Full patch vs `main`, snapshot `31cfa68bf1ff7074` | Blocking: F1 (result-cell tightening contradicted the spec and would fail historical records in every PR). Non-blocking: F2/F3 (near-template forms now passing), F4 (exact state-name cells; trade-off question), F5 (unclosed fence hides sentence checks), F6 (test gaps) | All fixed; F1 by reverting to 1.0.0 with owner acceptance of the spec wording; see Deviations |
| 2 | Changed files vs `main`, snapshot `4331cfe03e9e5a07` | No blocking findings. Non-blocking: R2-1 (compatibility statement ignored forms 1.0.0 missed), R2-2 (stale rule descriptions in spec Scope and plan steps 1, 3), R2-3 (stale evidence), R2-4 (no closed-fence passing test) | Wording fixed in spec, plan, CHANGELOG; evidence refreshed; test added. Re-review not required for wording; the one added test is not re-reviewed |

Review limitations: an isolated session of the same model is not human independence; round 2 was not a fresh context. Not exercised: CI (`sdd-gate` skipped in this repository).

Outstanding items / exceptions: `sdd-gate` is skipped in this repository by design.

Delivery: not merged; not released.
