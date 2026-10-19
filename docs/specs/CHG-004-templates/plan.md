# Plan: CHG-004-templates | Spec and plan templates sized by level

Status: `in-progress` | Technical owner: Idaika Iglesias | Accepted by / date: Idaika Iglesias, 2026-10-19 (in conversation), including one-line reasons for unaffected L3 risk areas.
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
| `docs/manual/03-working-a-change.md` | One sentence on markers; L3 risk-area wording (one-line reason) | Readers |
| `docs/manual/example/README.md` | Note that the example predates the 2.0.0 templates | Readers |
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

`docs/templates/spec.md`, `docs/templates/plan.md`, `.agents/workflows/spec/SKILL.md`, `.agents/workflows/plan/SKILL.md`, `docs/manual/03-working-a-change.md`, `docs/manual/example/README.md`, `CHANGELOG.md`.

## Deviations and decisions during execution

- Independent review round 1 (owner accepted the corrections, 2026-10-19, in conversation):
  - F1: `docs/manual/03-working-a-change.md` now says an unaffected L3 risk area states in one line why; the manual example README notes that the example predates the 2.0.0 templates. Plan step 5's reason for keeping the old wording did not hold, because the owner's decision concerns exactly those risk areas.
  - F2: interpretation recorded: "Acceptance and next steps" is marked required for L2 as well, although decision 3's L2 list does not name it, because it holds the scope-acceptance statement and the plan link. Owner confirmed.
  - F3: the template legends and the `spec`/`plan` workflows say to keep required sections and conditional ones whose condition holds; workflow step 4 in both now depends on the level.
  - F4: the legends say to delete the italic marker lines when filling a record; the lean L2 test runs through `check_docs` with the markers deleted and with them kept.
  - F5: long lines rewrapped in the plan workflow and manual 03.
- Integration with CHG-003 (merged to `main` as `ac518a8` while this PR was open): `main` was merged into this branch; the only conflict was `CHANGELOG.md`, resolved by keeping both entries. Re-verified on the merged snapshot `0c474e5fd99e0949` (base `main` `ac518a8`): Windows 218 + 57 tests, Linux native ext4 copy 218 (1 skip) + 57, `check-change-level` L3 broad and `verify broad --target framework` passed, report `.sdd/results/verify-20261019T142347672098Z-02fb9787.json`.

## Completion evidence

Verified version or diff: working snapshot on branch `chg-004-templates` (HEAD `99ed5c2` plus uncommitted changes; snapshot in the Broad gate row), base `main` (`381748f`).
Relevant environment: Windows 11, Git for Windows, Python 3.14.7; Linux via WSL Ubuntu (native ext4 copy written from the index), Python 3.14.4.

| AC / check | Result | Evidence summary / reference |
| --- | --- | --- |
| AC-01, AC-02 | Passed (review) | Templates carry a legend and a marker under every heading as listed in Technical approach steps 2 and 3; spec header has `Related changes:`; AC sentence present; no `N/A` instruction. |
| AC-03 | Passed | `test_docs.py` `test_template_sections_carry_level_markers`. Mutation check: deleting one spec marker, or renaming `Related changes:`, made it fail; restoring made it pass. |
| AC-04 | Passed | `test_unchanged_templates_as_accepted_records_fail` unchanged and passing. |
| AC-05 | Passed | `test_lean_l2_record_with_required_sections_passes`: implemented L2 spec with only its required sections and completed plan with only its required sections, checked through `check_docs`, with marker lines deleted and kept; no errors. |
| AC-06 | Passed | `python3 .agents/tools/sync_adapters.py --check`: 20 generated files, 0 stale; `spec` and `plan` workflows point to the markers, including conditional sections. |
| AC-07 | Passed | `python3 scripts/check-docs`: passed; existing change records unchanged; broad gate below. |
| Full suites | Passed | Windows: 216 automation tests (6 platform skips) and 57 adapter tests. Linux native ext4 copy: 216 (1 skip) and 57. |
| Level floor | Passed | `python3 scripts/check-change-level --base main --level L3 --change CHG-004-templates --scope broad`: floor L3 (`agent-integration-controls`). |
| Broad gate | Passed | `python3 scripts/verify broad --target framework --base main --level L3 --change CHG-004-templates`: docs, adapters, adapter-tests, automation-tests passed on snapshot `ecb1213373948854` (after both review rounds; earlier runs `08dc55772c666339`, `bd66eb42e05ccd5d`); report `.sdd/results/verify-20261019T141249436574Z-01fad395.json` (local, untracked); only this line changed afterwards. |

Independent review: automated reviewer (`sdd-independent-review`, Claude sub-agent), fresh context without the implementation conversation (a different reviewer from CHG-001 to CHG-003), read-only tools; it ran no code, and every count, hash, and result it cites is requester-supplied. Round 2 resumed the same reviewer context. Not a human review or approval.

| Round | Target | Result | Resolution |
| --- | --- | --- | --- |
| 1 | Full patch vs `main`, snapshot `08dc55772c666339` | No blocking findings. Non-blocking: F1 (manual 03 still asked for `N/A - reason` in L3 risk areas), F2 (L2 status of Acceptance and next steps is an interpretation; question), F3 ("delete the rest" ambiguous for conditional sections; workflow step 4 not level-aware), F4 (lean test without markers and not through `check_docs`; legend silent on marker lines), F5 (long lines) | All fixed; F2 confirmed by the owner; see Deviations |
| 2 | Full patch vs `main`, snapshot `bd66eb42e05ccd5d` | No blocking findings. Non-blocking: R2-1 (new long line in the plan workflow), R2-2 (Affected documentation and components omitted the example README) | Both fixed (wording only); no re-review required |

Review limitations: an isolated session of the same model is not human independence; round 2 was not a fresh context. Not exercised: CI (`sdd-gate` skipped in this repository).

Outstanding items / exceptions: `sdd-gate` is skipped in this repository by design. `CHANGELOG.md` will conflict with CHG-003 (PR #5) and is resolved after that merge.

Delivery: not merged; not released.
