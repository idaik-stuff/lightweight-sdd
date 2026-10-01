# Agent workflow usage

Framework version `1.0.0`. This guide covers the agent workflow layer; [local
automation](automation.md) and the optional [CI adapter](ci-enforcement.md) are described
separately. It does not claim measured token savings or validated agent behavior.

Contents: [scope](#scope), [install](#install-or-upgrade),
[commands](#commands-and-activation), [examples](#working-examples),
[review](#independent-review), [maintenance](#maintenance-and-evolution),
[references](#technical-basis-and-runtime-limits).

## Scope

Five canonical Skills, two conditional references, one review contract, generated
`sdd-*` entrypoints, and one reviewer configuration per supported client are included.
There is no strategy Skill, extra artifact type, or automatic all-phases command.
`AGENTS.md` and the methodology remain the policy sources; the workflows do not add
classification levels or change the spec/plan/ADR templates and their lifecycles.

Verification connects to the deterministic commands described in
[automation](automation.md), without adding workflow stages or product assumptions.

## Install or upgrade

For a new repository, create it from this template, or copy the complete framework,
including `.agents/`, the generated client folders, `.github/`, `.sdd/`, `scripts/`,
and `.gitignore`. Do not nest it as another framework inside an existing one. When
upgrading, compare against the new release and merge deliberately; preserve local edits
and do not overwrite the repository. See [CI activation](ci-enforcement.md#activation-sequence).

Keep existing organization instructions and permissions. Review filename collisions,
especially pre-existing `.claude/skills/sdd-*` or reviewer definitions. Do not overwrite
an unrelated adapter merely because it has the same name.

Run the root README's adapter check. Start a fresh client session at the repository
root after installation, inspect its command menu and agent list, and confirm that
project instructions and the custom reviewer are available. Local policy or client
version may affect discovery; until this check is done, discovery is unverified.

## Commands and activation

| Phase | Entrypoint | Activation | Expected result |
| --- | --- | --- | --- |
| investigate | `/sdd-investigate` | Explicit or matched intent. | Evidence, cause confidence, and bounded next action. |
| spec | `/sdd-spec` | Explicit or matched L2/L3 specification intent. | Active change's `spec.md`; actual acceptance status. |
| plan | `/sdd-plan` | Explicit or matched planning intent. | Inspected, risk-proportionate `plan.md`. |
| implement | `/sdd-implement` | Explicit command only in this Claude integration. | Authorized diff, tests, documentation, and verification handoff. |
| verify | `/sdd-verify` | Explicit or matched verification intent, including after authorized implementation. | Scope, executed evidence, result, pending gates. |

Natural-language activation is a request-routing aid, not guaranteed enforcement.
Use the explicit command when deliberate phase selection matters. The other four
commands may still modify their permitted documentation or execute permitted checks;
none may infer implementation authority from a design-only request.

The `sdd-` prefix distinguishes these workflows from built-ins such as `/plan` or
`/verify`. Do not create aliases under generic built-in names. Command metadata points
to the existing canonical phase names; there are not ten separate workflows.

`/sdd-implement` does not mean "approve everything the agent invents". Existing L2/L3
scope and technical acceptance must be real. The adapter's manual-only setting stops
automatic Skill invocation; repository permissions remain separate controls.

## Working examples

The identifiers below illustrate invocation; they are not real product changes in the
starter. Execute only the next authorized phase, not every line as a single batch.

### Mechanical correction

```text
/sdd-implement Correct the misspelled heading in README.md; change nothing else.
```

Expected route: L0 if the heading has no behavioral or operational effect, then focused
verification. No spec, plan, or reviewer is needed. Operationally meaningful text still
requires risk classification; a `.md` extension alone does not establish L0.

### Bug with an unknown cause

```text
/sdd-investigate Diagnose the reported calculation mismatch. Do not modify code yet.
```

After diagnosis and authorization of the bounded fix:

```text
/sdd-implement Apply the bounded fix established in the investigation, add a regression
check where feasible, and verify the affected behavior. Do not expand the scope.
```

A genuinely local bug remains L1; a discovered permission/contract/data risk elevates
it before the affected implementation, regardless of diff size.

### Feature

```text
/sdd-spec Define CHG-001-<slug> from the supplied requirements. Draft the spec only.
```

After actual scope acceptance:

```text
/sdd-plan CHG-001-<slug>. Inspect the repository and produce the plan; do not implement.
```

After actual technical acceptance:

```text
/sdd-implement CHG-001-<slug>. Implement the accepted scope and plan, then verify it.
```

The user may already have accepted both artifacts. Reuse that acceptance rather than
repeating ceremonies. A changed requirement or material deviation may require renewal.

### Public API or architectural boundary

Use the same commands, with L3 strategy in the plan, an ADR only when justified,
broad verification, and the independent-review gate. A schema-only change is not
low-risk merely because it contains little code. A separate final check can be requested:

```text
/sdd-verify broad CHG-001-<slug>. Report evidence for the final change and pending gates.
```

No application verification command is bundled. Until the chosen stack has real
checks, the workflow must report required checks as blocked, not manufacture a pass.

## Independent review

Ask the main agent to use `sdd-independent-review` in a fresh context after initial
verification. This is a subagent name, not a `/sdd-independent-review` slash command.
The verifier may make the same delegation within an authorized L3 workflow.

```text
Use sdd-independent-review in a fresh context for this L3 change. Supply the packet
required by .agents/review/independent-review.md, including the complete scoped patch
and initial verification evidence. Do not pass the implementation conversation.
Return findings only; do not modify code or claim human approval.
```

The configured tools are `Read`, `Grep`, and `Glob`; the requester supplies the diff
and test evidence because this reviewer cannot run shell commands or tests. Its result
records that limitation. Do not grant shell access simply to make review convenient.

Resolve blocking findings through authorized implementation, rerun affected checks,
and review material corrections. Retain the concise result in the plan. A missing
reviewer leaves the L3 gate pending. A fresh session can be a fallback, but its actual
read-only controls and isolation must be verified and recorded, not merely assumed.

## Maintenance and evolution

Edit `.agents/workflows/` for procedures and `.agents/references/` for shared conditional
detail. Edit `.agents/adapters/clients.json` only for adapter metadata. Regenerate and
check using the root README commands; do not edit generated entrypoints manually.

The dependency-free generator deliberately reads this release's narrow frontmatter:
unquoted `name` and a single-line JSON-quoted `description`, both valid YAML. It fails
on unsupported forms rather than guessing. Keep these fields in that form or update
and test the parser deliberately. It generates 20 integration files, never deletes other files,
and rejects symlinked input/output paths. Old command names require deliberate cleanup
if the mapping is renamed; unrelated project files are never automatically removed.

[Behavior scenarios](../../.agents/evals/scenarios.md) are ready for later live trials.
Their results are not inferred from static tests. Use real failures to adjust triggers,
stopping rules, and evidence requirements without multiplying the workflow count.

The local runner supplies mechanical checks; product check commands require the
actual application stack. The CI adapter supplies base-policy enforcement once
[activated](ci-enforcement.md). Codex, Cursor, and Copilot VS Code adapters share these
workflows; see the [compatibility guide](agent-compatibility.md). The adapter generator
remains a separate maintenance utility.

## Technical basis and runtime limits

Official sources consulted on 2026-09-27 (external documentation, not project policy):

- Agent Skills format: `https://agentskills.io/specification`.
- Claude Code Skills, invocation fields, and name resolution:
  `https://code.claude.com/docs/en/skills`.
- Claude Code subagent definitions and tool allowlists:
  `https://code.claude.com/docs/en/sub-agents`.
- Claude Code project instruction imports:
  `https://code.claude.com/docs/en/memory`.

These establish the configuration mechanisms, not that this generated release ran in
a user's environment. Skills are not permission boundaries. Read-only reviewer tools
are configured separately; no broad `allowed-tools` grants or settings overrides are
added. What actually ran in a given environment must be recorded by whoever runs the
[behavior scenarios](../../.agents/evals/scenarios.md) and
[compatibility trials](../../.agents/evals/compatibility.md).

## Client entrypoints

The examples above use Claude's slash syntax. Cursor and Copilot VS Code local agent
mode use the same `/sdd-*` entrypoints. Codex CLI/IDE uses `$sdd-*` via its Skill selector.
Do not type these as shell commands. Sources live in `.agents/workflows/`;
`.agents/skills/` contains generated discovery files, not editable procedures.

Reviewer tool names and guarantees differ. The Claude example's no-shell allowlist
does not describe Codex/Cursor sandboxing. Follow the [client-specific controls](agent-compatibility.md#review-controls-and-safe-fallbacks)
and [live trials](../../.agents/evals/compatibility.md) before counting an L3 review.
