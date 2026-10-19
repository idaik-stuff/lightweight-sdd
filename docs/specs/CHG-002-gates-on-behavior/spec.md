# Spec: CHG-002-gates-on-behavior | Placeholder checks on values, not prose

Status: `implemented` | Level: `L3` | Level rationale: changes what the framework's own document gate accepts as an accepted spec or plan (`verification-controls`: `scripts/sdd/**`). A mistake could let real placeholders through or keep blocking legitimate domain vocabulary.
Owner: Idaika Iglesias | Scope accepted by / date: Idaika Iglesias, 2026-10-19 (in conversation).
Related changes: second of the SDD Lite 2.0 rollout; follows [CHG-001](../CHG-001-branch-and-pr-workflow/spec.md) (branch and PR rule). CHG-003 (levels) and CHG-004 (templates) build on it.

## Problem and goal

`scripts/check-docs` blocks accepted specs and plans that contain the words `TBD`, `TODO`, `pending`, or `not run` anywhere in the acceptance-criteria section or in an acceptance field, even inside a sentence or an inline code span. Legitimate domain vocabulary such as a product state `Changes pending`, "pending payment", or an outcome "the order shows as pending" fails the gate. Adopters rename domain terms to satisfy the checker, or learn to distrust it.

Goal: the gate flags unresolved placeholders, meaning a table cell or a field value that is only a placeholder, and stops judging prose. Real placeholders left from the templates keep failing.

## Context and current behavior

Observed facts (source: `FEEDBACK-pending-placeholder-false-positive.md`, adoption in `idaik-stuff/cv-online` CHG-002, framework `1.0.0`; and `scripts/sdd/docs.py` at `3d54c13`):

- `PENDING = re.compile(r"\b(TBD|TODO|pending|not run)\b", re.I)` is searched in the raw text of:
  - `Level rationale` (any spec);
  - `Scope accepted by / date` and the whole `## Acceptance criteria` section (spec `approved` or `implemented`);
  - `Accepted by / date` (plan `approved`, `in-progress`, or `completed`).
- The AC section search uses raw text, so words inside inline code spans also match. A `prose()` helper that strips code already exists but is not used here.
- Targeted checks that look for a template sentence rather than a word, and stay in scope as they are: `Scope acceptance: pending`, `Verified version or diff: pending`, and completion-table result cells that are exactly `not run`, `blocked`, `failed`, or `pending`.
- `scripts/sdd/ci.py` validates the PR candidate with the base commit's `docs.py`. Until this change is merged, the stricter 1.0.0 rule still applies to PRs in adopters.
- Templates (`docs/templates/spec.md`, `plan.md`) mark open values as `TBD`, `` `TBD` ``, or `TBD - <guidance>`.

Closed design decision (ideation, 2026-10-19, point E): gates on behavior, not prose. Keep the structural checks (paired spec/plan, valid states, level floor, spec level equals PR level, unique AC IDs, every AC mapped in the plan, links, not on the default branch). Acceptance fields remain records, not proof. L2/L3 evidence rows point to the PR's CI run or the `verify` JSON report, as guidance rather than a check.

## Scope and non-goals

Includes:

- Placeholder detection on values: a placeholder is a value that, with surrounding whitespace, list dashes, emphasis, quotes, brackets, and backticks removed, is only one of the tokens `TBD`, `TODO`, `pending`, `not run` (any case, any spacing in `not run`), optionally with end punctuation or followed by a dash or colon and template guidance (`TBD - What problem…`, `TBD: …`). See Expected behavior for examples.
- Where it applies:
  - each cell of the acceptance-criteria table in an accepted spec (`approved`, `implemented`);
  - the fields `Level rationale`, `Scope accepted by / date` (accepted spec), and `Accepted by / date` (accepted plan). Because these fields are records of a decision, a value that starts with a placeholder token (for example `pending owner review`) also fails.
- Prose in the acceptance-criteria section outside the table, and words inside a sentence or code span, are no longer flagged.
- The two targeted sentence checks (`Scope acceptance: pending`, `Verified version or diff: pending`) are evaluated without inline and fenced code, so a document that quotes the template sentence in backticks is not flagged; when a fence is left unclosed, they read the raw text as in 1.0.0. The completion result-cell check is unchanged from 1.0.0.
- Guidance, not a check, in `docs/development/methodology.md` (section 8) and `.agents/references/handoffs.md`: L2/L3 evidence rows reference the PR's CI run or the `verify` JSON report with its snapshot, or a defined manual procedure; L1 has no evidence table, its PR CI result is the evidence.
- Regression and negative tests in `scripts/tests/test_docs.py`.
- Removal of the root input file `FEEDBACK-pending-placeholder-false-positive.md` once covered.

Does not include:

- New checks on evidence references (rejected: the JSON report is local and untracked, so a check would validate a string, not proof, and would reject legitimate manual evidence).
- Template changes (CHG-004) and level changes (CHG-003).
- Placeholder checks on sections that are not checked today (for example Uncertainties).
- Authenticating acceptance records; they stay records.

## Expected behavior

- An accepted spec whose AC cells use domain words such as `Changes pending`, "pending payment", or "shows as pending" passes `check-docs`.
- An accepted spec with an AC cell that is only a placeholder, as copied from the template, fails with the existing message naming the spec and "pending placeholders".
- A Level rationale or acceptance field that is only a placeholder, or starts with one, fails with the existing messages.
- Draft specs and plans are not checked for placeholders, as today.
- Every change record already in the repository keeps its current result.
- Accepted trade-off: an AC cell whose whole content is only a token, or a token followed by a dash or colon (for example `pending` or `Pending - awaiting payment`), counts as a placeholder; a domain state inside an outcome sentence (``The order is `pending` ``) does not. Near-template forms with end punctuation, emphasis, brackets, or quotes (`TBD.`, `*TBD*`, `(pending)`) also count.

## Acceptance criteria

| ID | Scenario / precondition | Action | Observable outcome |
| --- | --- | --- | --- |
| AC-01 | Approved spec; an AC cell contains `` `Changes pending` `` | Run `scripts/check-docs` | Passes; no placeholder error |
| AC-02 | Approved spec; an AC outcome reads "The order shows as pending" or mentions "pending payment" | Run `scripts/check-docs` | Passes |
| AC-03 | Approved spec; an AC cell is only `TBD`, `` `TBD` ``, `TODO`, `pending`, or `not run`, in any case | Run `scripts/check-docs` | Fails with "accepted criteria contain pending placeholders" for each variant |
| AC-04 | Approved spec; an AC cell is `TBD - <guidance>` as in the template | Run `scripts/check-docs` | Fails with the same message |
| AC-05 | Approved spec; prose in the AC section outside the table mentions `pending` | Run `scripts/check-docs` | Passes |
| AC-06 | `Level rationale`, `Scope accepted by / date`, or `Accepted by / date` is only a placeholder, or starts with one (`pending owner review`) | Run `scripts/check-docs` | Fails with the existing field message |
| AC-07 | Same fields hold a concrete value that contains a placeholder word later (`Owner, 2026-10-19, after the pending items were resolved`) | Run `scripts/check-docs` | Passes |
| AC-08 | Draft spec and draft plan containing placeholders | Run `scripts/check-docs` | No placeholder errors (unchanged) |
| AC-09 | `Scope acceptance: pending`, `Verified version or diff: pending`, or a completion result cell `not run` in accepted or completed records | Run `scripts/check-docs` | Fails as in 1.0.0 (unchanged) |
| AC-10 | Repository at the end of this change | Run `scripts/check-docs` and `scripts/verify broad --target framework` | Pass; existing change records keep their result |
| AC-11 | Updated methodology and handoffs | Read them | Evidence guidance for L1 and L2/L3 is present as stated in Scope |
| AC-12 | Accepted spec or completed plan that quotes `` `Scope acceptance: pending` `` or `` `Verified version or diff: pending` `` inside backticks | Run `scripts/check-docs` | Passes; the same sentence without backticks still fails (AC-09) |

AC-03, AC-04, AC-06, and AC-09 are the failure boundaries; AC-01, AC-02, AC-05, AC-07, and AC-12 are the false positives that must disappear. This spec itself reproduces both false positives while the 1.0.0 checker is in place.

## Constraints and compatibility

- Property at risk: no real placeholder may pass. Every placeholder form shipped in `docs/templates/spec.md` and `plan.md` must still fail when left in an accepted record (AC-03, AC-04, AC-06).
- Consumers: adopters' accepted specs and plans, and `ci.py`, which uses the base's `docs.py`. The change accepts more documents, with one deliberate exception: near-template placeholders that 1.0.0 missed now fail (underscore emphasis such as `_TBD_`, and `not run` with irregular spacing). Because `ci.py` checks every change folder, an accepted historical record containing exactly one of these forms would start failing later PRs; it is a real placeholder and must be fixed in that record.
- Framework automation stays Python 3.10+ standard library only.

## Uncertainties

None open. Point 1 (where the value rule applies) and point 2 (evidence references as guidance, not a check) were accepted by the owner on 2026-10-19 in conversation.

## Acceptance and next steps

Scope acceptance: accepted by Idaika Iglesias on 2026-10-19 (in conversation), with AC-01 to AC-11, including the rule that acceptance fields starting with a placeholder fail; AC-12 (targeted checks ignore code spans) added and accepted the same day after this spec reproduced the false positive. Independent review round 1 (same day): the Scope wording on targeted checks was narrowed to the two sentences (result cells unchanged) and the trade-off above was recorded; both accepted by the owner in conversation. Review round 2: the compatibility statement now names the near-template forms that 1.0.0 missed; accepted by the owner the same day in conversation.

Related plan: [plan.md](plan.md). States and completion rules: [docs/specs/README.md](../README.md).

Upon completion, record evidence and delivery status in the plan. If another change replaces this behavior, reference that change without rewriting history.
