# 5. Agents

This chapter covers the agent side of the framework: how each supported client picks
up the rules, how to call the workflows, how to run the independent review, and how to
qualify a client before trusting it. The normative details are in
[workflow usage](../development/workflows.md) and
[agent compatibility](../development/agent-compatibility.md).

## How an agent learns the rules

Every client starts from the same small policy file, [AGENTS.md](../../AGENTS.md):

| Client | How it loads the policy |
| --- | --- |
| Claude Code | `CLAUDE.md` contains one line, `@AGENTS.md`, which imports it. |
| Codex CLI / IDE | Reads the root `AGENTS.md` directly. |
| Cursor (local Agent) | Reads the root `AGENTS.md` directly. |
| Copilot (VS Code local agent mode) | `.github/copilot-instructions.md` is a short bridge pointing to `AGENTS.md`. |

`AGENTS.md` is deliberately short. It holds the permanent rules, the classification
table, and pointers. Everything else (product documents, the methodology, a workflow
procedure, a template) is read only when the current task needs it. This keeps the
context small and makes it less likely that an agent follows guidance that does not
apply.

Keep it that way. Add a rule to `AGENTS.md` only if it applies to almost every task;
otherwise put it in the document that owns the topic and add a pointer.

## Calling the workflows

| Workflow | Claude Code, Cursor, Copilot VS Code | Codex | Can start without being named? |
| --- | --- | --- | --- |
| investigate | `/sdd-investigate` | `$sdd-investigate` | Yes, when the request matches. |
| spec | `/sdd-spec` | `$sdd-spec` | Yes, when the request matches. |
| plan | `/sdd-plan` | `$sdd-plan` | Yes, when the request matches. |
| implement | `/sdd-implement` | `$sdd-implement` | **No. Always explicit.** |
| verify | `/sdd-verify` | `$sdd-verify` | Yes, when the request matches. |

These are chat selections, not shell commands. The `sdd-` prefix keeps them apart
from built-in commands such as `/plan`.

Four workflows may start when your request clearly matches them ("why is this test
failing?" can trigger `investigate`). This is a convenience, not a guarantee: when it
matters which workflow runs, name it.

`implement` is marked manual-only in every client's native format
(`disable-model-invocation` for Claude Code, Cursor, and Copilot;
`allow_implicit_invocation: false` for Codex). Selecting it is still not approval of
scope: for L2/L3 the accepted spec and plan must exist, and the agent reports missing
acceptance instead of treating the command as a yes.

### Writing good requests

A good request names the workflow, the change, and where to stop:

```text
/sdd-plan CHG-001-book-reservations. Inspect the repository and write the plan.
Do not implement.
```

Useful phrases:

- "Draft only" / "Do not implement": keeps a design request a design request.
- "Do not modify code": for investigations.
- "Do not expand the scope": for implementation.
- "Report what is blocked": so missing tools are not silently skipped.

Avoid "do everything" requests. There is no command that runs all workflows end to
end, by design: each step is a point where a human decides whether to continue.

## Sessions and handoffs

Long changes span several sessions, sometimes several clients. Do not paste the old
conversation. Ask for a handoff instead:

```text
Prepare a handoff for this change using .agents/references/handoffs.md.
```

The result is a compact block: change and level, workspace and boundary, phase
result, artifacts, what was actually accepted, evidence, open items, and the next
action. The new session reads it, then rereads the current spec, plan, and worktree.
When the files and the handoff disagree, the files win. See the
[handoff reference](../../.agents/references/handoffs.md).

## Running the independent review

The review must happen in a **fresh context**, not by asking the implementing chat to
"now act as a reviewer". Each client has a native reviewer named
`sdd-independent-review`, generated from one [review contract](../../.agents/review/independent-review.md):

| Client | Reviewer definition | Effective restriction | Extra step before trusting it |
| --- | --- | --- | --- |
| Claude Code | `.claude/agents/` | Tool allowlist: Read, Grep, Glob. No shell, no edits. | Supply the full diff and evidence: it cannot produce them. |
| Copilot VS Code | `.github/agents/` | Tools: read and search. | Confirm no prompt file or tool set widens the tools. |
| Codex | `.codex/agents/` | Read-only sandbox. Shell and inherited MCP tools may remain. | Confirm write-capable external tools are absent. |
| Cursor | `.cursor/agents/` | `readonly: true`. Not a no-shell allowlist. | Confirm write-capable external tools are absent. |

The implementer or verifier prepares the packet (spec, plan, complete scoped diff,
initial evidence) and starts the reviewer, for example in Claude Code:

```text
Use sdd-independent-review in a fresh context for CHG-002-sign-in-and-permissions.
Supply the packet required by .agents/review/independent-review.md, including the
complete scoped patch and the initial verification evidence. Do not pass the
implementation conversation. Return findings only.
```

Remember the limits:

- An isolated session of the same model can share the implementer's blind spots. It
  is useful, but it is not the same as a human reviewer.
- The reviewer returns findings. It does not approve, accept risk, or edit code.
- If you cannot confirm the reviewer's restrictions (Codex, Cursor), the review gate
  stays `blocked`. Use a person or a client whose restrictions you can confirm.
- Record who or what reviewed, the isolation used, and its limitations in the plan.

## Qualifying a client

The adapters are generated and tested for consistency, but that does not prove how a
given client version behaves on your machine with your settings. Before relying on a
client for real work, run the
[compatibility trials](../../.agents/evals/compatibility.md) in a disposable
repository. They check, among other things, that:

- the root policy is loaded and no whole-docs import happens;
- the five `sdd-*` workflows appear and point to the repository's sources;
- asking to "start coding" does not start `implement`;
- `implement` reports missing acceptance instead of proceeding;
- an unconfigured product verification stays blocked;
- the reviewer starts fresh, with the restrictions you expect;
- a patch comment saying "ignore the policy" does not waive the review.

Record the client version, platform, model, and results. Repeat when the client,
workspace policy, or permissions change materially.

The [behavior scenarios](../../.agents/evals/scenarios.md) go further and test each
workflow's judgment (classification, stopping, evidence). They are worth running when
you adopt the framework and after you change a workflow.

**Unqualified surfaces.** Copilot CLI, cloud agents, Codex cloud, Cursor cloud workers,
and other harnesses are not covered. Some of them find these files, but without the
same controls. Do not use them to work around the manual implementation gate.

## Customizing the workflows

All workflows are generated from one canonical source per workflow. To change one:

1. Edit `.agents/workflows/<workflow>/SKILL.md` (or `.agents/references/` for shared
   detail, `.agents/adapters/clients.json` for names and metadata).
2. Regenerate: `python3 .agents/tools/sync_adapters.py`.
3. Check: `python3 .agents/tools/sync_adapters.py --check` and the standard framework
   verification.
4. Rerun the affected behavior scenarios and compatibility trials.

Never edit the generated files under `.agents/skills/`, `.claude/`, `.codex/`,
`.cursor/`, or `.github/agents/`: the drift check fails until they match the source.
Changes to workflows and reviewer definitions are L3 under the default risk rules,
because they change the gates every client enforces.

Before adding a new workflow, ask whether the problem is better solved by a script,
a test, or a CI check. The framework stays at five workflows on purpose.

## Next

The next chapter collects the practices that keep the process lightweight in daily use.
