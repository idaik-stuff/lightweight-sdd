# Spec: CHG-004-templates | Spec and plan templates sized by level

Status: `approved` | Level: `L3` | Level rationale: changes the record structure every L2/L3 change in this repository and in adopters' repositories follows, and the templates are read by the `spec` and `plan` workflows of every client; the document gate depends on their placeholder forms.
Owner: Idaika Iglesias | Scope accepted by / date: Idaika Iglesias, 2026-10-19 (in conversation).
Related changes: fourth of the SDD Lite 2.0 rollout; follows [CHG-002](../CHG-002-gates-on-behavior/spec.md) (placeholder checks on values) and CHG-003 (L1 as default level, L2 by triggers). CHG-005 (installer) follows.

## Problem and goal

`docs/templates/spec.md` and `plan.md` present the same sections for L2 and L3 and invite `TBD` or `N/A - reason` for everything that does not apply. An L2 record therefore grows to L3 length, and readers have to find the few lines that matter among placeholders and non-applicable rows.

Goal: one template per artifact, the same structure as today, with each section marked required, optional, or only-if-applies for L2 and for L3. Non-applicable sections are deleted, not filled with `N/A`. An L2 spec and an L2 plan aim at about one page each. L3 keeps every section it has today.

## Context and current behavior

Observed at `381748f` (main after CHG-002):

- `docs/templates/spec.md` sections: Problem and goal; Context and current behavior; Scope and non-goals; Expected behavior; Acceptance criteria; Constraints and compatibility; Uncertainties; Acceptance and next steps. The header has Status, Level, Level rationale, Owner, and Scope accepted by / date. It says "Keep the sections that add value" but marks nothing.
- `docs/templates/plan.md` sections: System inspection; Technical approach; Affected components and contracts; Risk-proportionate strategy (six-row table); Implementation steps; Verification plan and traceability; Affected documentation; Deviations and decisions during execution; Completion evidence. Its intro asks to "leave `N/A - reason` if it helps explain the decision".
- `scripts/sdd/docs.py` requires, for recorded changes: header fields, an `## Acceptance criteria` section with at least one `AC-NN` row, a plan `## Verification plan and traceability` section mapping every AC, and for completed plans a `## Completion evidence` section with every AC. CHG-002 tests copy the templates as accepted records and expect the placeholder errors.
- The `spec` and `plan` workflows tell agents to read the template and "retain useful sections only".
- Change records in this repository (CHG-001 to CHG-003) already add a `Related changes:` header line by hand.

Closed design decision (ideation, 2026-10-19, point 3):

- Same structure; each section marked required, optional, or only-if-applies, for L2 and L3. Delete non-applicable sections instead of writing N/A.
- Spec header adds `Related changes:`.
- L2 spec and plan about one page each, as guidance, not a gate.
- The AC section gets one sentence: "Include at least one failure or boundary AC, or state in one line why there is none." No Type column and no checker rule.
- Spec: L2 requires header, Problem and goal, Scope and non-goals, Acceptance criteria; Context, Expected behavior, and Constraints are optional; Uncertainties only if any. L3 requires all sections except Uncertainties, which is only if any.
- Plan: L2 requires System inspection (brief), Technical approach, Verification plan and traceability, Affected documentation (one line), Completion evidence; Affected components is optional; the risk table keeps only applicable rows; Implementation steps only if more than one; Deviations only if any. L3 requires all sections, the risk table with all six areas, and completion evidence plus independent review.

## Scope and non-goals

Includes:

- `docs/templates/spec.md`: a short legend and a marker under each section heading giving its L2 and L3 status; `Related changes:` in the header; the AC sentence on failure or boundary AC; the intro says to delete non-applicable sections and that an L2 spec aims at about one page.
- `docs/templates/plan.md`: the same legend and markers; risk table guidance (L2 keeps applicable rows, L3 all six); Implementation steps and Deviations marked only-if-applies; Completion evidence keeps the independent-review line for L3; the intro replaces `N/A - reason` with "delete what does not apply" and states the one-page L2 aim.
- The `spec` and `plan` workflow procedures point to the markers ("keep the sections the template marks required for the level; delete the rest unless they add value") instead of the generic "retain useful sections".
- `docs/manual/03-working-a-change.md` and `docs/development/methodology.md`, only where they describe template sections or `N/A` usage.
- Tests: the templates, left unfilled and copied as accepted or completed records, still fail with the placeholder errors (existing CHG-002 test); a template-structure test that every section heading carries an L2/L3 marker and the spec header contains `Related changes:`.
- CHANGELOG entry.

Does not include:

- Any new `check-docs` rule on section presence, length, level-specific sections, or the failure/boundary AC (decision 3: guidance, no checker rule).
- Rewriting existing change records (CHG-001 to CHG-003, manual example) to the new markers.
- The ADR template.

## Expected behavior

- Someone copying the spec template for an L2 change keeps four sections plus any optional ones that help, and deletes the rest; the result passes `check-docs` once filled.
- Someone copying either template for an L3 change keeps every section (Uncertainties only if any) and the full risk table.
- Non-applicable content is removed; no template asks for `N/A`.
- The markers are plain text that the document gate ignores; an L2 record without optional sections is valid.

## Acceptance criteria

Include at least one failure or boundary AC, or state in one line why there is none.

| ID | Scenario / precondition | Action | Observable outcome |
| --- | --- | --- | --- |
| AC-01 | Updated spec template | Read it | Every section heading has a marker with its L2 and L3 status matching decision 3; the header has `Related changes:`; the AC section has the failure/boundary sentence; the intro says to delete non-applicable sections and gives the one-page L2 aim |
| AC-02 | Updated plan template | Read it | Every section heading has a marker matching decision 3; the risk table says L2 keeps applicable rows and L3 all six; no `N/A - reason` instruction remains |
| AC-03 | Template-structure test | Run `scripts/tests` | Passes; it fails if a section heading lacks an L2/L3 marker or the spec header lacks `Related changes:` |
| AC-04 | Unfilled templates copied as approved, implemented, or completed records | Run the existing CHG-002 template test | Still fails with the rationale, scope acceptance, AC placeholder, acceptance statement, technical acceptance, version/diff, and unresolved result errors |
| AC-05 | Minimal L2 spec and plan built from the templates with only the required sections, filled with concrete values | Run `check-docs` on them | Passes; no new rule rejects missing optional sections |
| AC-06 | Updated `spec` and `plan` workflows | Run `sync_adapters.py --check` and read them | Drift check passes; procedures point to the template markers |
| AC-07 | Repository at the end of this change | Run `scripts/check-docs` and `scripts/verify broad --target framework` | Pass; existing change records are unchanged and keep passing |

AC-04 and AC-05 are the boundaries: the templates still trip the gate when left unfilled, and a lean L2 record is not rejected.

## Constraints and compatibility

- The placeholder forms in the templates (`` `TBD` `` fields, `TBD` AC cells, `Scope acceptance: pending.`, `Verified version or diff: pending.`, `Not run` result cells) stay as they are, because the document gate and its tests rely on them (AC-04).
- Section headings stay the same text, because `docs.py` finds `## Acceptance criteria`, `## Verification plan and traceability`, and `## Completion evidence` by name.
- Existing records written from the 1.0.0 templates remain valid.

## Uncertainties

None open. The template rules are the closed ideation decision 3 (2026-10-19).

## Acceptance and next steps

Scope acceptance: accepted by Idaika Iglesias on 2026-10-19 (in conversation), with AC-01 to AC-07. Next: plan with strategy.

Related plan: [plan.md](plan.md). States and completion rules: [docs/specs/README.md](../README.md).

Upon completion, record evidence and delivery status in the plan. If another change replaces this behavior, reference that change without rewriting history.
