# Documentation map

Each concept has one canonical source. Other documents reference it rather than redefine it.

## Sources and responsibilities

| File | Contents | When to create / update | Who validates |
| --- | --- | --- | --- |
| [Brief](product/brief.md) | Vision, problem, users, value, goals, and high-level exclusions. | At the start; when the problem, user, or purpose changes. | Product owner. |
| [MVP](product/mvp.md) | First-release boundary, journeys, and exit criteria. | At the start; explicit scope changes until completion. | Product owner. |
| [PRD](product/prd.md) | Accepted capabilities and cross-cutting requirements; delivery status of each. | Before features that need them; when those requirements or their delivery status change. | Product owner; technical owner for feasibility. |
| [Architecture](architecture/overview.md) | Implemented system, boundaries, flows, operations, and known limitations. | When inspecting the system; after changes that affect its description. | Technical owner. |
| [Specs and plans](specs/README.md) | Intent, execution, and evidence for a specific change. | As required by the level defined in AGENTS.md; throughout that change. | Product owner accepts what; technical owner accepts how. |
| [ADRs](adr/README.md) | Durable decisions, alternatives, and consequences. | Only for significant decisions. | Technical owner; affected stakeholders when appropriate. |
| [Methodology](development/methodology.md) | Gates, responsibilities, and exception handling. | When adopting or changing the working method. | Team owner. |
| [Workflow usage](development/workflows.md) | Agent commands, installation, upgrade, and usage. | When the workflow interface changes. | Team owner. |
| [Automation](development/automation.md) | Local commands, machine configuration, evidence, and limits. | When automation behavior changes. | Framework maintainer. |
| [CI enforcement](development/ci-enforcement.md) | Base-policy CI, ownership, activation, and operational limits. | When the adapter or platform governance changes. | Framework maintainer and independent owners. |
| [Manual](manual/README.md) | Explanatory guide: concepts, adoption, working a change, verification, agents, and practices. Links to normative sources; never redefines them. | When the framework or its recommended practice changes. | Framework maintainer. |
| [Templates](templates/spec.md) | Reusable structure for specs, plans, and ADRs. | When their use reveals a genuine improvement. | Team owner. |

The agent may draft and propose. It does not replace human approvals or invent approvers' names. The same person may take product and technical responsibility in a small team.

## Living documents and historical records

`brief.md` retains the current purpose. `prd.md` retains accepted requirements, distinguishing planned from implemented capabilities. `architecture/overview.md` describes what exists, not a future architecture presented as reality. They are living documents, but they do not describe exactly the same kind of truth.

`mvp.md` defines a release: record its completion when delivered. Do not expand it indefinitely to mean "the entire product"; a later release can have its own scope when needed.

Specs and plans record changes. While open, they are updated with accepted decisions and deviations. After completion, they are not rewritten to absorb every future feature. New changes link to earlier ones when relevant.

Accepted ADRs preserve their original decision. A factual correction or a superseded status may be noted; a new decision requires another ADR.

## Minimum conventions

`template` means the document does not yet describe the product. `draft` means an unvalidated proposal. `active` means an accepted living document, not necessarily an implemented capability. Specs use their own states, defined in their index.

`TBD` indicates unknown information. `N/A - reason` indicates that something has been evaluated and does not apply. Do not turn a gap into `N/A` to make a document appear complete. Uncertainties that could affect scope, security, contracts, data, or irreversibility block the affected work until resolved.

When validating a document, identify the actual person and date. Use `YYYY-MM-DD` dates. There is no need to maintain a changelog inside every document: Git preserves the changes.

Use stable local identifiers to link requirements: `CAP-01`, `NFR-01`, `CON-01`, `AC-01`. Do not renumber references already in use. There is no need to identify every sentence or create a separate traceability matrix.

## Proportionate requirements

The initial files are provided ready to use, but completing them exhaustively is not mandatory. The brief and first-release scope must be understandable before committing to implementation; complete the PRD and architecture to the depth needed for that release.

A feature does not duplicate the product vision. A local bug does not generate a PRD. Irrelevant template sections may be removed; retain non-applicability decisions that explain why a risk was ruled out.

## When to split out another document

Vocabulary starts in the PRD; create `product/domain.md` only if it needs its own explanation. Data, security, and operations start in the architecture overview. A detailed testing or deployment strategy warrants its own file when its length, maintenance needs, or readership justify it.

Until then, do not create those files. When splitting out a section, move its content and leave a link: do not keep two versions. Local debt is recorded in outstanding work; a systemic limitation is summarized in architecture.

## Client compatibility

[Agent compatibility](development/agent-compatibility.md) describes the four local
client integrations and effective-control checks. The framework maintainer updates
it when discovery, invocation, or review behavior changes. It is on-demand guidance,
not permanently imported policy.
