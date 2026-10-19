# Plan: CHG-004-templates | Spec and plan templates sized by level

Status: `approved` | Technical owner: Idaika Iglesias | Accepted by / date: Idaika Iglesias, 2026-10-19 (in conversation), including one-line reasons for unaffected L3 risk areas.
Spec: [spec.md](spec.md) | Verification scope: `broad`.

## System inspection

Inspected at base `381748f` (main after CHG-002; CHG-003 is in a separate open PR):

- `docs/templates/spec.md` (8 sections) and `docs/templates/plan.md` (9 sections) as listed in the spec's Context. The plan intro asks for `N/A - reason`; the Affected documentation placeholder repeats it.
- `scripts/sdd/docs.py` finds `## Acceptance criteria`, `## Verification plan and traceability`, and `## Completion evidence` by exact heading, reads header fields with `FIELD`, and treats only AC cells and named fields as placeholder carriers. A plain-text marker line under a heading does not interact with these checks.
- `scripts/tests/test_docs.py` `test_unchanged_templates_as_accepted_records_fail` copies both templates as approved and as implemented/completed records and expects the placeholder errors.
- `.agents/workflows/spec/SKILL.md` step 3 and Output ("retain useful sections only") and `.agents/workflows/plan/SKILL.md` step 3 (read the template) are the only workflow references; wrappers copy only frontmatter descriptions, which do not change.
- Other `N/A` guidance: `docs/README.md` (meaning of `N/A - reason`), `docs/manual/01-concepts.md`, `03-working-a-change.md` (L3 risk areas), and the manual example. These describe evaluated, non-applicable risk areas, which remain valid for the L3 risk table; they are not template instructions.

## Technical approach

1. Marker format: an italic line directly under each `##` heading, `*L2: <status> · L3: <status>*`, where status is `required`, `optional`, or `only if <condition>`, with a short qualifier in parentheses when the decision gives one (for example `required, brief`). A legend line in each template's intro explains it and says to delete sections whose marker does not apply to the change's level.
2. Spec template markers: Problem and goal `required · required`; Context and current behavior `optional · required`; Scope and non-goals `required · required`; Expected behavior `optional · required`; Acceptance criteria `required · required`; Constraints and compatibility `optional · required`; Uncertainties `only if any · only if any`; Acceptance and next steps `required · required`. Header gains `Related changes: none or links`. The AC section gains the decision's sentence on failure or boundary AC. Intro: delete non-applicable sections; an L2 spec aims at about one page.
3. Plan template markers: System inspection `required, brief · required`; Technical approach `required · required`; Affected components and contracts `optional · required`; Risk-proportionate strategy `only applicable rows · required, all six areas`; Implementation steps `only if more than one · required`; Verification plan and traceability `required · required`; Affected documentation `required, one line · required`; Deviations and decisions during execution `only if any · required`; Completion evidence `required · required, with independent review`. The risk table guidance says an L3 area that is not affected states why in one line; the intro and the Affected documentation placeholder drop the `N/A - reason` instruction. Intro: an L2 plan aims at about one page.
4. Workflows: `spec` step 3 and Output, and `plan` step 3, say to keep the sections the template marks required for the change's level, add optional ones only when they help, and delete the rest.
5. Docs: `docs/manual/03-working-a-change.md` gets one sentence on the markers where it introduces the templates. `docs/README.md` and the L3 risk-area wording stay, because `N/A - reason` there describes an evaluated risk area, not a template section.
6. Tests in `test_docs.py`: a template-structure test (every `##` heading in both templates is followed by a marker line with valid L2 and L3 statuses; the spec header contains `Related changes:`; no `N/A - reason` instruction in either template); a lean L2 record test (spec with only the four required sections and plan with only its required sections, filled with concrete values, approved and completed, produces no errors). The existing template-placeholder test stays unchanged.
7. CHANGELOG entry.

Rejected alternatives:

- Two templates per artifact (L2 and L3): duplicates structure and drifts; the decision keeps one structure.
- HTML comments as markers: invisible when rendered, so authors miss them; italics are visible and harmless to the gate.

## Affected components and contracts

| Area / path | Proposed change | Impact / consumer |
| --- | --- | --- |
| `docs/templates/spec.md`, `plan.md` | Markers, legend, `Related changes:`, AC sentence, no `N/A` instruction | Authors and the `spec`/`plan` workflows in every client; adopters' new records |
| `.agents/workflows/spec/SKILL.md`, `plan/SKILL.md` | Point to the markers | All clients (thin wrappers unchanged) |
| `docs/manual/03-working-a-change.md` | One sentence on markers | Readers |
| `scripts/tests/test_docs.py` | Template-structure and lean-L2 tests | Framework tests |
| `CHANGELOG.md` | Entry | Adopters |

## Risk-proportionate strategy

| Area | Decision, check, or reason for non-applicability |
| --- | --- |
| Compatibility and consumers | Headings and placeholder forms unchanged, so `docs.py` and its tests behave the same (AC-04); existing records stay valid; the lean-L2 test proves optional sections are not required (AC-05). |
| Data, integrity, and migration | Not affected: no persistent data; existing records are not rewritten. |
| Permissions, security, and privacy | Not affected: documentation and tests only. |
| Failures, load, and availability | Risk: a marker accidentally matches a field or placeholder pattern and changes gate results; covered by the unchanged template test and the lean-L2 test. |
| Change observability | Markers are visible in rendered Markdown. |
| Rollout and feasible recovery | Ships with 2.0.0 through this PR; revert the squash commit to recover. |

## Implementation steps

1. Spec and plan templates (AC-01, AC-02).
2. Tests (AC-03, AC-04, AC-05).
3. Workflows and manual sentence (AC-06); CHANGELOG.
4. Broad verification (AC-07) and independent review.

## Verification plan and traceability

Environment: Windows 11 with Python 3; Linux via WSL Ubuntu for the full suites.

| AC / risk | Test, check, or manual procedure | Command / location / environment | Expected result |
| --- | --- | --- | --- |
| AC-01, AC-02 | Inspection against decision 3, plus the structure test | Diff review, independent review, `test_docs.py` | Markers and wording as planned |
| AC-03 | Template-structure test | `scripts/tests/test_docs.py` | Passes; a removed marker or header line makes it fail (checked by reasoning in review) |
| AC-04 | Existing template-placeholder test | `test_docs.py` `test_unchanged_templates_as_accepted_records_fail` | Same errors as before |
| AC-05 | Lean L2 record test | `test_docs.py` | No errors |
| AC-06 | Adapter drift check and inspection | `python3 .agents/tools/sync_adapters.py --check` | 0 stale; workflows point to markers |
| AC-07 | Full framework verification | `python3 scripts/check-docs`; `python3 scripts/verify broad --target framework --base main --level L3 --change CHG-004-templates` | Passed |
| Level floor | Change-level check | `python3 scripts/check-change-level --base main --level L3 --change CHG-004-templates --scope broad` | Passed |
| L3 review | Independent review in a fresh session | `sdd-independent-review` agent with `.agents/review/independent-review.md` | Findings recorded and resolved |

## Affected documentation

`docs/templates/spec.md`, `docs/templates/plan.md`, `.agents/workflows/spec/SKILL.md`, `.agents/workflows/plan/SKILL.md`, `docs/manual/03-working-a-change.md`, `CHANGELOG.md`.

## Deviations and decisions during execution

None recorded yet.

## Completion evidence

Verified version or diff: pending. Relevant environment: pending.

| AC / check | Result | Evidence summary / reference |
| --- | --- | --- |
| AC-01 to AC-07 | Not run | Pending implementation. |

Independent review: pending; required for L3.

Outstanding items / exceptions: `sdd-gate` is skipped in this repository by design. `CHANGELOG.md` will conflict with CHG-003 (PR #5) and is resolved after that merge.

Delivery: not merged; not released.
