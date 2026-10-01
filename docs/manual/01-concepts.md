# 1. Concepts

This chapter explains the ideas behind Lightweight SDD and why the framework is shaped
the way it is. It does not repeat the rules: [AGENTS.md](../../AGENTS.md) and the
[methodology](../development/methodology.md) are normative. When this manual and those
files disagree, they win.

## The problem it addresses

AI coding agents are fast at producing code and equally fast at producing plausible
claims about that code: that a requirement was understood, that a change is safe, that
tests passed. Two familiar failure modes follow:

- **Too little process.** The agent edits first and explains later. Scope grows
  silently, a "small fix" changes a permission check, and "verified" means "it
  compiled".
- **Too much process.** Every change gets a requirements document, a design, a plan,
  and a checklist. A typo costs as much ceremony as a database migration, so people
  learn to skip the process altogether.

Lightweight SDD (spec-driven development) sits between them. It asks for written
intent and planning **only where risk justifies it**, and it insists on **real
evidence** everywhere.

## Five core ideas

### 1. Risk decides the process, not size

Every change is classified into one of four levels before work starts. The level
depends on what could go wrong, not on how many lines change:

| Level | Intuition | Example in a small library app |
| --- | --- | --- |
| L0 | Nothing behaves differently. | Fix a typo in a help page. |
| L1 | A local fix inside existing behavior. | Due dates are off by one day for loans made at midnight. |
| L2 | Intentionally new or changed behavior. | Members can reserve a book that is currently on loan. |
| L3 | Hard to undo or affecting trust boundaries. | Add sign-in and restrict who can delete a member. |

A one-line change to a permission check is L3. A thousand-line rename with no
behavioral effect can be L0. Labels such as "bug" or "refactor" do not lower the level.
The precise criteria and the order in which to evaluate them are in the
[classification table](../../AGENTS.md#classification-and-routing).

Classification is not a one-time label. If work uncovers a higher risk, the change is
reclassified before the affected work continues.

### 2. Two artifacts, only when needed

For L2 and L3, a change gets a folder `docs/specs/<change-id>/` with exactly two files:

- **`spec.md`** answers *what and why*: scope, exclusions, and testable acceptance
  criteria (AC). The product owner accepts it.
- **`plan.md`** answers *how and how we know*: the approach, risks, steps, and a
  mapping from every AC to the check that proves it. The technical owner accepts it,
  and it later holds the evidence summary.

L0 and L1 need neither. Their level, rationale, and evidence fit in the commit message
or PR. An ADR is added only for a durable decision with real alternatives, never by
default. See the [specs index](../specs/README.md) and the
[templates](../templates/spec.md).

The same person may own product and technical acceptance. What matters is that
acceptance is real and recorded, and that the agent never invents it.

### 3. Five workflows, one at a time

The work is split into five bounded workflows:

```text
investigate -> spec -> plan -> implement -> verify
```

Each workflow has a clear input, a minimum output, and a stopping point. Only the steps
the level requires are used: an L0 typo goes straight to `implement -> verify`.
Workflows are never chained automatically. Each step runs when it is authorized, and
**implementation is always an explicit, manual choice**: asking an agent to design or
investigate never authorizes it to write code.

The workflows are agent Skills (`/sdd-spec`, `$sdd-plan`, and so on) generated for
Claude Code, Codex, Cursor, and Copilot VS Code from one canonical source. See
[workflow usage](../development/workflows.md).

### 4. Evidence, not assertions

"Verified" means a named check actually ran against the final change and its result is
recorded. The framework is strict about the difference between:

- **passed**: the check ran and succeeded;
- **failed**: it ran and did not succeed;
- **blocked / not run**: a tool, environment, or credential was missing.

A blocked check is never reported as a pass, and a framework-only check is never
reported as product coverage. Verification has three cumulative scopes (focused,
standard, broad) chosen by level. Real commands are registered in
`.sdd/verification.json` and run by `scripts/verify`, which stores a local report.
See [verification scopes](../development/methodology.md#6-verification-scopes) and
[automation](../development/automation.md).

### 5. Independent review for the riskiest changes

An L3 change is reviewed by someone who did not write it: a different person, or a
fresh agent session with read-only tools and no access to the implementation
conversation. The reviewer receives a defined packet (spec, plan, diff, evidence) and
returns findings; it does not edit or approve. An isolated session of the same model is
weaker than a human reviewer, so its limitations are recorded. See the
[review contract](../../.agents/review/independent-review.md).

## Supporting principles

**One source per concept.** Every rule, command, and structure has exactly one
canonical home, and everything else links to it. The [documentation map](../README.md)
lists them. This manual follows the same rule: it explains and points; it does not
restate.

**Context on demand.** Agents load the small `AGENTS.md` permanently and read
everything else only when the current task needs it. This keeps context focused and
reduces the risk of following stale or irrelevant guidance.

**Humans own decisions.** Agents draft, inspect, run checks, and report. Accepting
scope, accepting residual risk, approving destructive or production actions, and
granting exceptions remain human responsibilities.

**Living documents versus records.** Product documents (brief, MVP, PRD) and the
architecture overview describe the current truth and are kept up to date. Specs,
plans, and ADRs record a change or decision at a point in time and are not rewritten
later.

**Honest gaps.** `TBD` means unknown. `N/A - reason` means evaluated and not
applicable. A gap is never disguised as a decision to make a document look complete.

## The parts of the framework

| Part | Where | Role |
| --- | --- | --- |
| Policy | `AGENTS.md`, `docs/development/` | Permanent rules, levels, gates, and procedures. |
| Product and architecture | `docs/product/`, `docs/architecture/`, `docs/adr/` | What is being built, what exists, and why. |
| Changes | `docs/specs/<change-id>/` | Spec and plan for each L2/L3 change. |
| Agent workflows | `.agents/` and generated client folders | Five procedures, review contract, and per-client adapters. |
| Local automation | `scripts/`, `.sdd/` | Document checks, risk floors, and the verification runner. |
| CI adapter | `.github/` | Optional GitHub Actions gate evaluated from the trusted base. |

## What it deliberately does not do

- It does not choose a stack, a deployment target, or a test framework.
- It does not create documents for their own sake: no mandatory design file,
  verification report, or traceability matrix.
- It does not make agents autonomous: no command runs all workflows end to end.
- It does not turn local scripts into a security boundary. Real enforcement needs
  server-side rules and independent owners; see [CI enforcement](../development/ci-enforcement.md).
- It does not claim that agent behavior has been validated in your environment. That
  is established by running the [compatibility trials](../../.agents/evals/compatibility.md).

## Next

The next chapter explains how to adopt the framework in a new or existing repository.
