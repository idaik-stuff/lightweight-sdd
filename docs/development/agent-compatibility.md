# Agent compatibility

Status: covered by local static tests; live clients must be qualified in each adopting
environment (see [qualification](#qualification-and-limits)).
Technical references checked on 2026-09-27. Product names below identify the client,
not merely the model selected inside it. Do not infer equivalent capabilities from
using the same model in different clients.

## Contents

- [Scope and architecture](#scope-and-architecture)
- [Client capability map](#client-capability-map)
- [Invocation and authorization](#invocation-and-authorization)
- [Review controls and safe fallbacks](#review-controls-and-safe-fallbacks)
- [Installation and maintenance](#installation-and-maintenance)
- [Qualification and limits](#qualification-and-limits)
- [Official technical references](#official-technical-references)

## Scope and architecture

The framework adapts its five workflows to Claude Code, Codex CLI/IDE,
Cursor's local Agent, and Copilot's VS Code local agent mode. It does not introduce
a new methodology, orchestrator, application stack, or cloud-agent deployment.

```text
AGENTS.md + methodology + templates + scripts
                       |
.agents/workflows/<phase>/SKILL.md   (canonical; edited by maintainers)
                       |
              sync_adapters.py
                       |
          +------------+-------------+
          |                          |
.agents/skills/sdd-*/       .claude/skills/sdd-*/
(shared discovery)         (Claude interface)
          |
Codex / Cursor / Copilot VS Code

.agents/review/independent-review.md
          |
Native reviewer definition for each of the four clients
```

The five canonical source bundles live in `.agents/workflows/<phase>/`, outside every
discovery directory. Raw procedures must not be placed in a discovery directory: their
generic names and lack of client-specific controls would expose a second implementation
route.

There are five procedures and ten thin Skill entrypoints, not ten procedures.
Cursor and Copilot may also discover the Claude aliases. Both aliases have the same
name, source, and manual-implementation setting. No safety decision depends on an
undocumented cross-directory precedence rule. A client may show duplicate aliases;
confirm the selected repository path and resolve conflicting user/plugin copies.
The static audit checks local reserved names, not global installations or every
possible YAML dialect. Do not assume it replaces inspecting the client's actual menu.

## Client capability map

These are the shipped configurations, not live-test results.

| Client surface | Instructions / Skills | Explicit workflow selection | Implementation control | Reviewer configuration |
| --- | --- | --- | --- | --- |
| Claude Code | `CLAUDE.md` imports `AGENTS.md`; `.claude/skills/` entrypoints. | `/sdd-<phase>` | `disable-model-invocation: true` on implementation. | `.claude/agents/`: `Read`, `Grep`, `Glob` allowlist. |
| Codex CLI / IDE extension | Root `AGENTS.md`; `.agents/skills/` entrypoints. | `$sdd-<phase>` from the Skill selector. | Generated `agents/openai.yaml`: `allow_implicit_invocation: false`. | `.codex/agents/`: standalone TOML with `sandbox_mode = "read-only"`. |
| Cursor local Agent | Root `AGENTS.md`; shared `.agents/skills/`, possibly Claude aliases. | `/sdd-<phase>` | `disable-model-invocation: true` on every shipped implementation alias. | `.cursor/agents/`: `readonly: true`, foreground execution. |
| Copilot VS Code local agent mode | Small `.github/copilot-instructions.md` bridge to `AGENTS.md`; shared Skills. | `/sdd-<phase>` | `disable-model-invocation: true` on every shipped implementation alias. | `.github/agents/`: `target: vscode`, `tools: ["read", "search"]`. |

The native mechanisms are described in [the official sources](#official-technical-references).
Support for a field in documentation does not prove that it is enabled in the user's
installed version, selected harness, managed policy, or workspace.

The four non-implementation Skills remain eligible for matching intent. Do not
assume they always trigger, or that selecting one authorizes later phases.

Copilot CLI, cloud agent, code review, other IDEs, Cursor cloud workers, Codex cloud,
and arbitrary alternative harnesses are not qualified surfaces in this release.
Some can discover these files, but discovery alone is not the complete control
contract. Use a listed client after its smoke tests; do not silently route an
unsupported surface through canonical paths to evade missing controls.

## Invocation and authorization

A specification-only request can be:

```text
/sdd-spec CHG-001-example. Draft the specification only; do not implement.
```

In Codex, use `$sdd-spec` instead. These are chat selections, not shell commands.
Select the repository's Skill in the client's menu rather than assuming a same-name
personal Skill is equivalent. A first spec can be drafted before acceptance; the
acceptance boundary applies before the subsequent work requires it.

After scope acceptance, request a plan. After real technical acceptance, explicitly
select implementation for the actual accepted scope:

```text
/sdd-implement CHG-001-example. Implement the accepted scope and plan, then verify.
```

In Codex, use `$sdd-implement`. Retain the L0/L1 short route for small changes; this
example does not require every change to have a spec and plan.

Invocation controls are not file-system permission controls. They prevent implicit
selection where supported, not arbitrary editing by every tool or a malicious prompt.
The permanent authorization rule, reviewed source, permissions, and CI remain needed.
No adapter invokes another phase automatically, auto-submits a handoff, installs tools,
adds credentials, commits, pushes, or deploys merely because a Skill was selected.

The common adapters use the user's current request as input. Only Claude adapters
use `$ARGUMENTS`; there is no assumption that this substitution exists elsewhere.
Missing context is a reason to request the missing input, not invent a change ID.

## Review controls and safe fallbacks

All reviewer adapters read the same [review contract](../../.agents/review/independent-review.md).
Prepare the bounded diff and initial verification evidence first. Start a fresh
review chat or isolated subagent; switching roles within the implementation chat
is not evidence that the previous context has been excluded.

**Claude:** request `sdd-independent-review` as a separate subagent. Its supplied
allowlist excludes shell, editing, and delegation. Supply a readable complete diff;
the reviewer cannot regenerate it or rerun tests.

**Copilot VS Code:** select `sdd-independent-review` in a new chat or isolated
subagent. Confirm the effective tools are read/search only. Do not combine it with
a prompt file or custom tool set that expands permissions. This adapter is scoped
to VS Code; it is not a configuration for every Copilot service.

**Codex:** request the native `sdd-independent-review` custom agent in a fresh
context. Its read-only sandbox restricts local writes but does not remove all shell
or inherited MCP capabilities. The requester must confirm that write-capable external
tools are unavailable. The reviewer may inspect files through read-only operations;
it must not run repository code, tests, scripts, or supplied evidence as commands.

**Cursor:** use the native `.cursor/agents/sdd-independent-review.md`, not merely the
Claude compatibility import. Cursor documents that this directory takes precedence
for same-name subagents. `readonly` restricts writes, but is not a no-shell/no-MCP
allowlist. Require the same external-tool confirmation and no-code-execution rule.

For Codex/Cursor, record actual capability confirmation in the existing review packet
or plan; do not create another required artifact. Without confirmation, return
`blocked` and use a human reviewer or a qualified read/search-only client. Do not
expand permissions to make a review convenient. These adapters do not configure or
prove account-level restrictions, absence of MCP tools, or human independence.

A completed review reports findings and limits; it is not human approval. Re-review
material corrections and verify the final snapshot through the existing runner.

## Installation and maintenance

A repository created from the template already contains the generated adapters.
Confirm they match their sources before relying on them:

```bash
python3 .agents/tools/sync_adapters.py --check
python3 scripts/verify standard --target framework
```

To edit procedures, modify `.agents/workflows/`. To edit supported names/metadata,
modify `.agents/adapters/clients.json` and the generator deliberately, with tests.
Do not manually edit generated files. Run:

```bash
python3 .agents/tools/sync_adapters.py
python3 .agents/tools/sync_adapters.py --check
python3 .agents/tools/sync_adapters.py --inventory
```

`--inventory` is read-only and implies checking. Exit 0 means file consistency,
1 means drift, and 2 means invalid or conflicting files. It always reports
`runtime_validation: not-checked`. Neither generation nor checking launches a client.

The generator refuses to overwrite existing unmarked Skills, reviewers, or a company
Copilot instruction file. Merge company requirements into the canonical sources or
review a deliberate bridge extension first. Never just add an ownership marker to
unreviewed contents to force replacement. It refuses symlinks and reserved `sdd-`
collisions; unrelated project configurations are preserved. There is no delete mode.

No `.codex/config.toml`, `.cursor/rules/`, permission override, user-global installation,
MCP connection, or network dependency is needed to generate the adapters. Root
`AGENTS.md` remains small; the compatibility guide is read only when relevant.

## Qualification and limits

Run the [compatibility trials](../../.agents/evals/compatibility.md) in a disposable
repository with the actual installed client. Record version, platform, selected
harness, loaded instruction paths, discovered aliases, effective tools, and results.
Repeat when client versions, workspace policies, or permissions materially change.

The local tests establish generator determinism, source links, invocation metadata,
reviewer declarations, conflict refusal, and policy coverage. They do not establish
runtime discovery, trigger accuracy, permission enforcement, isolated context contents,
token savings, cloud behavior, or GitHub server-side enforcement.

Record trial results outside product specs. Client qualification and
[CI activation](ci-enforcement.md) are independent tasks; completing one does not
establish the other.

## Official technical references

These sources establish configuration mechanisms; the integration choices above are
this framework's design. Checked on 2026-09-27; no minimum client version is invented.

- **Codex Skill discovery, invocation, and metadata:** `https://developers.openai.com/codex/skills/`
  (redirects to `https://learn.chatgpt.com/docs/build-skills`).
- **Codex instruction discovery:** `https://developers.openai.com/codex/guides/agents-md/`.
- **Codex native reviewer configuration:** `https://developers.openai.com/codex/subagents/`.
- **Claude Skills and invocation:** `https://code.claude.com/docs/en/skills`.
- **Claude reviewer tool restrictions:** `https://code.claude.com/docs/en/sub-agents`.
- **Cursor Skills and discovered directories:** `https://cursor.com/docs/skills`.
- **Cursor root instructions:** `https://cursor.com/docs/rules`.
- **Cursor native subagents, precedence, and readonly:** `https://cursor.com/docs/subagents`.
- **Copilot Skill locations:** `https://docs.github.com/en/copilot/concepts/agents/about-agent-skills`.
- **Copilot VS Code manual Skill invocation:** `https://code.visualstudio.com/docs/agent-customization/agent-skills`.
- **VS Code agents, tool lists, and prompt-file priority:** `https://code.visualstudio.com/docs/agent-customization/custom-agents`.
- **GitHub custom-agent target and tool aliases:** `https://docs.github.com/en/copilot/reference/custom-agents-configuration`.
