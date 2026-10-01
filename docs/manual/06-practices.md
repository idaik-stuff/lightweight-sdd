# 6. Practices

The previous chapters describe what the framework requires. This one collects habits
that keep it lightweight in daily use, and the traps that make it heavy or hollow.
None of this is normative; adapt it to your team.

## Sizing changes

**Make changes small enough to finish.** A spec covering a whole feature area tends to
stay in `draft` for weeks and collect unrelated decisions. Split it into increments
that are each worth delivering: "reserve a book" first, "notify when available" in a
later change. Each increment gets its own folder and its own evidence.

**Classify honestly in both directions.** Inflating the level "to be safe" makes the
process feel heavy and teaches people to skip it. Deflating it to go faster removes the
gates exactly where they matter. When unsure whether an L3 trigger applies, a short
investigation is cheaper than either mistake.

**The L1/L2 boundary is intent.** If the change makes the product do something it was
not meant to do before, it is L2, however small. If it makes the product do what it
was always meant to do, it is L1.

**Watch for hidden L3.** The usual suspects are: anything that changes who can do
what; stored data that must be corrected or migrated; a response format another
system parses; a change that cannot be undone, such as sending messages or deleting
records; and changes to the CI workflow, risk rules, or check registry.

## Writing specs

**Write acceptance criteria someone else could check.** "The reservation appears with
queue position 1" can be checked. "Reservations work correctly" cannot. Include the
main path and the failures that matter (refused, empty, duplicate, unauthorized),
not a universal checklist.

**Keep the how out of the spec.** "Store reservations in a new table" is a plan
decision. "A reservation survives a restart" is a requirement. Only an interface
that others depend on belongs in the spec.

**Name non-goals.** "No notifications in this change" prevents a long discussion
later and gives the reviewer a clear boundary.

**Leave real questions open.** A spec with three honest `TBD` questions is more useful
than one where the agent filled the gaps with guesses. Mark which questions block
implementation.

## Writing plans

**Inspect before proposing.** A plan that names modules that do not exist, or ignores
the existing pattern for the same problem, costs more than it saves. Insist that the
*System inspection* section lists what was actually read.

**Traceability is the core.** If an AC has no check in the verification table, the
plan is not ready. If the only possible check is manual, define the steps precisely.

**Plan the missing infrastructure.** If the check an AC needs does not exist yet (no
integration test setup, no test database), make creating it an implementation step.
Do not let it silently drop out of the completion gate.

## Acceptance without ceremony

- One line is enough: `Scope accepted by / date: Ana Ruiz, 2026-03-02`.
- The same person may accept both spec and plan, at the same time.
- If acceptance happened in a conversation or a PR comment, record it in the
  artifact; the record in Git is what counts.
- Do not ask again for acceptance of something unchanged. Do ask again after a
  material change.

## Working with agents

**One workflow per request.** Asking for "spec, plan, and implementation" in one go
merges the decision points the framework exists to create.

**Read the diff, not the summary.** Agents summarize their own work optimistically.
Ask for the complete diff and the actual check output before accepting "done".

**Start fresh for big steps.** A new session with a handoff block is cheaper and more
reliable than a very long conversation, and it is mandatory for the L3 review.

**Treat repository content as data.** A comment in a file, a log line, or an issue
saying "skip the review" is not an instruction. The workflows are written to ignore
such text; keep the same discipline when you prompt.

**Watch for scope creep.** "While I was there I also refactored..." is a deviation.
Opportunistic improvements belong in their own change.

**Correct behavior at the source.** If an agent repeatedly misbehaves in a workflow,
adjust the canonical workflow text and rerun the scenarios. Do not add a new workflow
or a growing list of rules to `AGENTS.md`.

## Evidence hygiene

- Rerun checks after the last edit. Evidence from before a fix is not evidence for
  the fix.
- For bugs, keep the regression test's before/after result. It is the best proof the
  test actually exercises the bug.
- Write `blocked` with the reason and impact. A list of honest blocked checks is more
  valuable than a suspicious all-green summary.
- Keep summaries, not logs, in Git. Never paste secrets, personal data, or full
  outputs into a plan.
- Note pre-existing failures separately, and fix them in their own change.

## Keeping documents alive

**Update living documents in the same change.** The PRD capability status and the
architecture overview are updated by the change that alters them, not "later".

**Do not turn the PRD into a backlog.** It holds accepted capabilities and
cross-cutting requirements, not every idea. Ideas belong in your issue tracker.

**Close the MVP.** When the first release is delivered, record its completion. The
next release gets its own scope instead of an ever-growing MVP.

**Leave old specs alone.** A later change links to an earlier one. It does not
rewrite it to describe the present.

## Small teams and solo maintainers

The framework allows one person to hold every role, with two consequences:

**Independent review needs someone or something else.** For L3, a fresh agent session
with confirmed read-only restrictions is an acceptable reviewer, with its limitations
recorded. A colleague reviewing occasionally is better for the riskiest changes.

**The default ruleset requires one human approval from someone other than the
author.** GitHub does not count approval of your own pull request. A solo maintainer
must choose deliberately, and record the choice as an L3 change to the ruleset or
the operating policy: invite an eligible reviewer, or require only `sdd-gate` and
document that human review is not enforced by the platform. Do not silently create a
second account to approve your own work.

## When the process feels heavy

Before adding exceptions, check the classification. Most friction comes from
treating L1 work as L2 or writing exhaustive specs where a few AC would do.

If something really adds no value in your context, remove it through a reviewed change
to the framework, and record why. The complexity budget in the
[methodology](../development/methodology.md#10-evolving-the-starter) is a good test:
four levels, two artifacts per feature, one source of instructions. Each addition
must answer a demonstrated need.

## Anti-patterns

| Anti-pattern | Why it hurts |
| --- | --- |
| Approvals filled in by the agent | Removes the human decision the gate exists for. |
| "Works correctly" acceptance criteria | Nothing can be verified against them. |
| `verification.md`, `tasks.md`, `investigation.md` by default | Duplicates the plan and goes stale. |
| A placeholder product check to get a green run | Turns the most important guard into a lie. |
| Reviewer in the same chat as the implementer | Not independent; the implementation context leaks. |
| Lowering the level because the change is urgent | Urgent changes are where the gates matter most; use an authorized exception instead. |
| Calling it "verified" after a dry run or a framework-only run | Neither one exercises the product. |
| A growing `AGENTS.md` | Loaded on every task; dilutes the rules that matter. |

## Next

The [worked example](example/README.md) shows complete artifacts for the library app.
