# Architecture decision records

Create an ADR for a durable decision with significant alternatives and consequences. L3 alone does not require one. A local detail that fits in the plan does not need another file.

Use the [template](../templates/adr.md) and names such as `0001-<slug>.md`, `0002-<slug>.md`, and so on. When working in parallel, resolve numbering collisions before merging. Do not renumber decisions already referenced.

## Lifecycle

`proposed`: awaiting a decision. `accepted`: approved decision. `rejected`: formally rejected alternative. `superseded`: replaced by another ADR, which must be linked.

Acceptance does not imply that the system already implements the decision. The plan describes execution, and the [architecture overview](../architecture/overview.md) describes the existing system.

Do not rewrite an accepted decision to erase its tradeoffs. You may explicitly correct a factual error or add a reference to a superseding ADR. A new choice requires a new record.

This starter contains no accepted ADRs or predetermined technology decisions. Do not create an ADR merely to record that these templates exist.
