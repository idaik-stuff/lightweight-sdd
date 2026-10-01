# Agent workflow layer

Five canonical workflows, one review contract, and generated client adapters.
`AGENTS.md` owns permanent rules; the methodology owns gates; templates own document
structures. Adapters translate invocation and reviewer configuration, not product policy.

## Sources and generated files

| Location | Responsibility | Load when |
| --- | --- | --- |
| `workflows/<phase>/SKILL.md` | Canonical two-field metadata and procedure. | The selected phase needs it. |
| `workflows/<phase>/agents/openai.yaml` | Canonical display text. | Generating UI metadata. |
| [Client mapping](adapters/clients.json) | Five names, manual implementation policy, reviewer identity. | Generating or checking adapters. |
| `skills/sdd-*/` | Generated shared discovery entrypoints and Codex metadata. | Discovered by a qualified client. |
| [Handoffs](references/handoffs.md) | Compact continuation/evidence format. | Handoff or resumption. |
| [Risk checks](references/risk-checks.md) | Conditional risk questions. | The risk applies. |
| [Review contract](review/independent-review.md) | Common reviewer procedure. | Preparing or conducting separate review. |
| `tools/` | Deterministic generation and static compatibility tests. | Maintenance or verification. |
| [Behavior scenarios](evals/scenarios.md) | Original workflow trial cases. | Live evaluation, not assumed passed. |
| [Compatibility trials](evals/compatibility.md) | Cross-client discovery and control checks. | Qualifying an installed client. |

Canonical sources live in `workflows/<phase>/`, outside every discovered directory:
a raw source in a discovered directory would expose an unnamespaced copy with no
client-specific invocation controls. Shared wrappers and Claude compatibility
wrappers deliberately use the same five `sdd-` names and source links. Their metadata
is generated, never maintained independently.

## Client interfaces

Codex, Cursor, and Copilot VS Code read shared Skills under `.agents/skills/`.
Claude Code uses `.claude/skills/`. Each supported client has a native reviewer
configuration. The [compatibility guide](../docs/development/agent-compatibility.md)
explains overlapping discovery, effective restrictions, and unqualified surfaces.

Regenerate/check using the root README. The generator validates all input and target
paths before writing, rejects symlinks and unowned files, and refuses reserved-name
collisions. It never deletes files, grants global permissions,
installs clients, edits user settings, or claims live behavior. Individual replacement
is atomic; generation is not a cross-file transaction. Rerun after an interrupted write.

## Authorization and review

Only implementation is manual-only. Investigation, specification, planning, and
verification may be selected by matching intent, within the user's requested task.
Explicit Skill selection is not approval of new scope, a missing plan, destructive
actions, publishing, or deployment. Do not bypass invocation controls through source paths.

Use a fresh reviewer, not a mode switch retaining implementation context. Codex/Cursor
read-only settings are weaker than the Claude/Copilot read/search tool allowlists:
confirm external write tools are absent or use a human/read-only alternative. Record
limitations; keep the L3 gate pending when the required review cannot be performed.

## Distribution

Install the complete repository. Canonical individual `skill.zip` bundles depend on
shared templates, references, and repository context; they are not hosted-chat installs.
Use generated entrypoints, not source bundles, for automatic discovery in this release.
Local automation stays in `scripts/` and `.sdd/`; CI activation remains a separate
platform operation. No additional workflow, feature artifact, or application stack is added.
