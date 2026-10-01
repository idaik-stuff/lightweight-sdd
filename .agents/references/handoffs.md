# Handoffs and evidence

Use this reference for a phase handoff, a resumed session, or final verification.
Do not load it merely because a session started. Do not create `handoff.md` by default.
Artifact states remain defined in `docs/specs/README.md`; this file does not add states.

## Minimal handoff

Return a compact block; omit genuinely irrelevant fields for L0/L1:

```text
Change: identifier or bounded request; level and rationale.
Workspace: repository root, branch/worktree if known, and exact change boundary.
Phase result: produced, unresolved, failed, or blocked; explain what this means.
Artifacts: spec/plan and only the relevant source paths.
Authorization: what was actually accepted, by whom or where evidenced; what is missing.
Evidence: observed facts/check results, not unsupported implementation claims.
Open items: blocking questions, risks, missing checks/review, and owner when known.
Next action: the smallest permitted next phase or the exact missing decision.
```

These are response labels, not a new workflow engine. Keep an accepted plan as the
execution record. A resumed session reads current artifacts and checks the worktree;
it does not trust a stale handoff over changed files. Do not send the whole conversation.
Do not replace a supplied existing identifier or ask again for facts already available.

## Verification evidence

Record target version/snapshot, environment, requested and actual scope, then:

| AC / risk / check | Command or manual procedure | Result | Evidence / limitation |
| --- | --- | --- | --- |
| Actual identifier | Exact command and working directory, or repeatable steps | passed / failed / blocked / not run | Observable result and durable reference when available |

Record required and optional coverage distinctly. Missing required infrastructure is
blocked, not N/A. Optional omissions have a reason. Keep `verification outcome`,
`independent-review gate`, and `deployment state` separate. A passing test command
cannot establish all three.

For a working snapshot, identify relevant staged, unstaged, and untracked files. A
commit identifier alone is insufficient for uncommitted work. A manifest of paths and
content hashes can bind evidence to such a snapshot; refresh it after any relevant edit.
Do not treat a hash as proof that a check executed or that the boundary was complete.
For a committed range, identify both base and target; do not assume `main` or `HEAD~1`.

Retain concise evidence in `plan.md` for L2/L3. For L0/L1, prepare a durable summary in
an existing record or proposed commit message. Do not make commits without permission.
Transient logs/patches may live outside tracked product files with permission. Redact
sensitive content and retain a reproducible summary when a temporary reference expires.

## Approval and continuation

Use actual acceptance of the current contents, not a fabricated approver or date. A
user may already have accepted both scope and approach. Do not ask again unless a
material deviation invalidates that acceptance. Do not interpret a request to plan
as permission to implement a plan the user has not seen.

Stop only the affected work when an input blocks it. Continue safe independent work
within authorization where useful. Do not execute the next phase merely because it
appears in the route. Respect the integration's manual-only entrypoints.
