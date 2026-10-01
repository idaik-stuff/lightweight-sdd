# Changes: specs and plans

For a change that requires them, create:

```text
docs/specs/<change-id>/
    spec.md
    plan.md
```

Reuse the issue identifier if one exists; otherwise, use a stable, descriptive local identifier such as `CHG-001-<slug>`. There is no need to maintain another manual catalog: the folders are the index.

[AGENTS.md](../../AGENTS.md) defines when these artifacts are required. The [spec](../templates/spec.md) defines what and why; the [plan](../templates/plan.md) defines how and its evidence. Adjust context links for the destination when copying them; `spec.md` and `plan.md` link to each other within the same folder.

## States

| Artifact | States | Meaning of completion |
| --- | --- | --- |
| Spec | `draft`, `approved`, `implemented`, `superseded`, `cancelled` | `implemented`: AC satisfied and applicable gates complete. Does not prove deployment. |
| Plan | `draft`, `approved`, `in-progress`, `completed`, `cancelled` | `completed`: execution and evidence finalized, without hiding blocking outstanding items. |

An approved spec may return to `draft` if it changes materially; record renewed acceptance before continuing. Minor wording changes do not require a new process.

## After implementation

Update affected living documents. Do not keep every old spec synchronized with the whole product: preserve what that change agreed to and delivered. A historical correction may be noted explicitly.

Use `superseded` when another decision genuinely replaces the entire scope, identifying the replacement. For a partial modification, it is enough for the new change to reference the earlier one; there is no need to reclassify the entire historical file.

Do not generate an example folder as though it were a real feature. This starter begins with no recorded product changes.
