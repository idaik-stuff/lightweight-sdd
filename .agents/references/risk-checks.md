# Conditional risk checks

Read only the applicable rows during planning, verification, or independent review.
`AGENTS.md` owns classification; the methodology owns gates. This reference supplies
questions and evidence examples, not new mandatory artifacts or numerical thresholds.

| Trigger | Design questions | Useful evidence when applicable |
| --- | --- | --- |
| External/public contract | Who consumes it? What remains compatible? How are changes introduced and retired? | Schema/contract diff, consumer examples, compatibility and error-behavior checks. |
| Persistent data or migration | What can be lost, duplicated, reordered, or partially applied? Can old/new versions coexist? | Representative migration rehearsal, invariant/count checks, restart/retry and restore or roll-forward exercise. |
| Permissions/security boundary | What authorizes each operation? Is isolation preserved on all paths? | Negative-access tests, boundary/tenant tests, sensitive-data handling checks. |
| Failure/availability | What happens during timeout, dependency loss, retry, partial completion, or overload? | Failure-injection/integration checks, idempotency evidence, bounded timeout and recovery behavior. |
| Scale/performance | Which workload and threshold are actually required? Where can state or cost grow without bound? | Representative workload, stated environment, measurements against accepted limits. |
| Rollout/recovery | Can the change be limited or stopped? Is rollback actually possible? Who accepts residual risk? | Staging/canary procedure when available, compatible-version checks, feasible restoration or roll-forward plan. |
| Observability/operations | How will operators detect success, failure, and unintended effects without exposing secrets? | Observable signal definitions, failure-path inspection, operational procedure review. |
| Architectural boundary | Which dependency/ownership constraints change? Why is the tradeoff durable? | Boundary/integration tests, ADR when justified, architecture updated after implementation. |

Do not invent a latency target, load profile, compliance claim, rollback guarantee, or
security control to fill a row. Link to accepted requirements. When evidence requires
an environment or authorization that is unavailable, record the missing dependency.

For irreversible actions, prevention, backups with demonstrated restoration, or a
viable roll-forward may be the relevant strategy; do not promise an inverse command.
A unit test proves only the behavior it exercises. A checklist is not executed evidence.

For a low-risk feature, omit irrelevant detail. For an L3 risk, retain the reasoning
that explains scope and meaningful non-applicability. Do not copy this whole table
into every plan.
