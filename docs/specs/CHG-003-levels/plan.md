# Plan: CHG-003-levels | L1 as the default level, L2 by explicit triggers

Status: `approved` | Technical owner: Idaika Iglesias | Accepted by / date: Idaika Iglesias, 2026-10-19 (in conversation).
Spec: [spec.md](spec.md) | Verification scope: `broad`.

## System inspection

Inspected at base `381748f` (main after CHG-002):

- `AGENTS.md` "Classification and routing": one order sentence, a four-row table (L0-L3 criteria and minimum workflow), and two follow-up lines. It is the canonical source; the methodology says "Classification and routes are defined only there".
- `.sdd/ci.json` `scopes`: `L0 focused, L1 standard, L2 standard, L3 broad`. `scripts/sdd/ci.py ci_configuration()` only enforces minimums (focused, focused, standard, broad), so `L0: standard` is valid for 1.0.0 and 2.0.0 bases alike.
- `scripts/sdd/changes.py assess()`: local minimum scope is focused for L0/L1, standard for L2, broad for L3, which already matches decision A; no code change needed.
- `scripts/tests/test_ci.py` `test_doc_typo_focused` copies the shipped `.sdd/ci.json` and asserts that an L0 README change selects `focused`; it will assert `standard` now. No test pins the whole shipped `scopes` map.
- Text that restates the 1.0.0 levels: `docs/development/methodology.md` section 1 (an L1 example line, compatible); `docs/development/ci-enforcement.md` scope table (L0 focused) and the explanatory sentence after it, and the "Valid documentation typo | Focused framework checks" scenario row; `docs/manual/01-concepts.md` levels table; `docs/manual/03-working-a-change.md` "Classifying" list and the L2 example's justification; `docs/manual/04-verification-ci.md` minimum-scope sentence; `docs/manual/06-practices.md` "The L1/L2 boundary is intent"; `.github/pull_request_template.md` "Explain the level".
- `.agents/evals/scenarios.md` E01-E18: E04 expects an L2 spec for "bounded feature requirements"; no scenario covers L2 triggers, owner-forced L2, or the no-downgrade rule.
- Generated wrappers copy only workflow descriptions; no workflow description mentions L2 criteria, so `sync_adapters.py --check` is unaffected.

## Technical approach

1. `AGENTS.md`: replace the order sentence and the table rows. Rows keep the four levels and routes, add names (Mechanical, Quick, Feature, Critical), move "small new capabilities with one to three clear AC" into L1, and define L2 by triggers T1-T5 listed under the table with "the owner can always require L2". Add two rules below the table: declare the level in one line before the first change, citing triggers; escalate on your own, never downgrade unless the owner does. The L1 route becomes "verify focused". Keep the section short; it is loaded at every session start.
2. `.sdd/ci.json`: `"L0": "standard"`. Update `test_doc_typo_focused` to expect standard (renamed accordingly) and add a test that pins the shipped scopes map.
3. Documentation alignment, wording only, pointing to `AGENTS.md` rather than copying the triggers where possible: methodology section 1 (add a one-line L2 declaration example), `ci-enforcement.md` table, sentence, and scenario row, manual pages 01, 03, 04, 06, PR template level guidance.
4. Eval scenarios: rewrite E04 (small capability with two AC is L1, no feature package); add E19 (T2 new user-visible flow, L2 with trigger named), E20 (T1 ambiguity, L2 spec with questions), E21 (T3/T4 multi-area or multi-PR work, L2), E22 (T5 durable decision, L2 and ADR only if justified), E23 (owner asks for L2 on an L1-sized change, L2 without argument), E24 (agent finds a trigger mid-change, raises the level and stops for spec/plan; never lowers on its own).
5. CHANGELOG: breaking entry.

Rejected alternatives:

- A checker for the declaration line or triggers: judgement cannot be checked deterministically, and a string check would be prose-gating, which CHG-002 removed.
- Keeping L0 at focused in CI: decision A sets standard for L0-L2 in CI, so a mislabelled L0 still gets regression checks on the server.

## Affected components and contracts

| Area / path | Proposed change | Impact / consumer |
| --- | --- | --- |
| `AGENTS.md` | New L1/L2 criteria, triggers, order, declaration and escalation rules | Every client, every session |
| `.sdd/ci.json` | `scopes.L0` = `standard` | Adopters' CI once this is their base |
| `scripts/tests/test_ci.py` | Typo test expects standard; new shipped-scopes test | Framework tests |
| Methodology, `ci-enforcement.md`, manual 01/03/04/06, PR template | Wording aligned with `AGENTS.md` | Readers |
| `.agents/evals/scenarios.md` | E04 rewritten; E19-E24 added | Client qualification |
| `CHANGELOG.md` | Breaking entry | Adopters |

## Risk-proportionate strategy

| Area | Decision, check, or reason for non-applicability |
| --- | --- |
| Compatibility and consumers | Existing L2 specs stay valid (docs.py still accepts L2/L3 records). New work may be lighter; L3 floors are unchanged and still enforced (AC-05 test). CI only gets stricter for L0. |
| Data, integrity, and migration | N/A - no persistent data. |
| Permissions, security, and privacy | L3 criteria and path floors untouched; downgrading below a floor stays impossible because floors only raise levels. |
| Failures, load, and availability | Main risk is misclassification by judgement (L2 work done as L1). Mitigations: explicit triggers, one-line declaration visible in the PR, escalation rule, owner override, eval scenarios E19-E24. Residual risk accepted by decision A. |
| Change observability | The declaration line and the PR's `Change-Level` make the chosen level and triggers visible to the owner before merge. |
| Rollout and feasible recovery | Ships with 2.0.0 through this PR. Recovery: revert the squash commit. |

## Implementation steps

1. `.sdd/ci.json` and tests (AC-03, AC-04, AC-05, AC-06).
2. `AGENTS.md` (AC-01, AC-02).
3. Documentation alignment and PR template (AC-07).
4. Eval scenarios (AC-08) and CHANGELOG.
5. Broad verification (AC-09) and independent review.

## Verification plan and traceability

Environment: Windows 11 with Python 3; Linux via WSL Ubuntu for the full suites.

| AC / risk | Test, check, or manual procedure | Command / location / environment | Expected result |
| --- | --- | --- | --- |
| AC-01, AC-02 | Inspection of `AGENTS.md` against the spec's decision list | Diff review and independent review | All elements present |
| AC-03 | Shipped scopes test | `scripts/tests/test_ci.py` | L0-L2 standard, L3 broad |
| AC-04 | CI assessment of an L0 README change with the shipped policy | `test_ci.py` (renamed typo test) | Scope `standard` |
| AC-05 | Existing floor tests plus a CI case declaring L1 on an L3 path | `test_changes.py`, `test_ci.py` | Fails as in 1.0.0 |
| AC-06 | Existing local scope behaviour | `test_changes.py` (L1 focused accepted) | Passes |
| AC-07 | Inspection; search for "however small", "everything else is L2", "Intentionally new" | `rg` over `docs/`, `AGENTS.md`, `.github/` + review | No contradicting statement remains |
| AC-08 | Inspection of `.agents/evals/scenarios.md` | Diff review and independent review | E04 and E19-E24 present as planned |
| AC-09 | Full framework verification | `python3 scripts/check-docs`; `python3 scripts/verify broad --target framework --base main --level L3 --change CHG-003-levels` | Passed |
| Level floor | Change-level check | `python3 scripts/check-change-level --base main --level L3 --change CHG-003-levels --scope broad` | Passed |
| L3 review | Independent review in a fresh session | `sdd-independent-review` agent with `.agents/review/independent-review.md` | Findings recorded and resolved |

Known limitation: the eval scenarios define expected agent behaviour; running them in each client is a separate qualification activity (`docs/development/agent-compatibility.md`) and is not part of this change's evidence.

## Affected documentation

`AGENTS.md`, `docs/development/methodology.md`, `docs/development/ci-enforcement.md`, `docs/manual/01-concepts.md`, `03-working-a-change.md`, `04-verification-ci.md`, `06-practices.md`, `.github/pull_request_template.md`, `.agents/evals/scenarios.md`, `CHANGELOG.md`.

## Deviations and decisions during execution

None recorded yet.

## Completion evidence

Verified version or diff: pending. Relevant environment: pending.

| AC / check | Result | Evidence summary / reference |
| --- | --- | --- |
| AC-01 to AC-09 | Not run | Pending implementation. |

Independent review: pending; required for L3.

Outstanding items / exceptions: `sdd-gate` is skipped in this repository by design; eval scenarios are not run in clients by this change.

Delivery: not merged; not released.
