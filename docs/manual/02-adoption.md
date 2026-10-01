# 2. Adoption

This chapter walks through adopting the framework, either by starting a new repository
from the template or by adding it to an existing one. Each step links to the normative
source that defines it.

Requirements: Git, Python 3.10 or later (standard library only), and GitHub if you
want the optional CI gate. No other tools are installed or assumed.

## Choose your path

| Situation | Path | Main difference |
| --- | --- | --- |
| New project, no code yet | [From the template](#path-a-new-repository-from-the-template) | The framework is in the first commit, so the CI trusted base exists from day one. |
| Existing project | [Into an existing repository](#path-b-adding-the-framework-to-an-existing-repository) | You merge files deliberately, resolve collisions, and handle a one-time CI bootstrap. |

Both paths end in the same [first-week checklist](#first-week-checklist).

## Path A: new repository from the template

### 1. Create the repository

On GitHub, choose **Use this template** and create your repository, then clone it.
Without GitHub, copy the complete framework, including the hidden directories
(`.agents/`, `.claude/`, `.codex/`, `.cursor/`, `.github/`, `.sdd/`) and the
`.gitattributes` and `.gitignore` files.

Remove or replace anything that describes the framework rather than your project:

- `README.md`: keep the **Commands** section and its tables, because `AGENTS.md` points
  agents there; rewrite the introduction for your project.
- `LICENSE`: choose your own project's license.
- `docs/manual/`: optional. Keep it as onboarding material, or delete it and link to
  the upstream manual instead. Nothing else depends on it.

### 2. Check the framework is healthy

```bash
python3 scripts/verify standard --target framework
```

This runs the document checks, the adapter drift check, and both maintenance test
suites. A pass says only that the framework files are consistent; it says nothing
about your product. See [automation](../development/automation.md#run-now).

### 3. Name the owners

The framework assumes real people behind three roles. The same person may hold all of
them in a small team:

| Role | Accepts | Where it is recorded |
| --- | --- | --- |
| Product owner | Scope and acceptance criteria in specs; product documents. | Each spec's acceptance field; product document headers. |
| Technical owner | Plans, architecture, and ADRs. | Each plan's acceptance field; architecture header. |
| Adoption owner | The working method itself and changes to it. | The [methodology](../development/methodology.md) header. |

Replace the `TBD` adoption owner in the methodology header now. The other owners are
filled in as the documents are written.

### 4. Define the product before the stack

Complete the [brief](../product/brief.md) and the [MVP scope](../product/mvp.md) first,
then only the cross-cutting requirements you already need in the [PRD](../product/prd.md).
The README's **First product session** prompt is a good start with an agent: it keeps
the agent in drafting mode, separates facts from hypotheses, and stops it from filling
the PRD or architecture with guesses.

Keep [architecture](../architecture/overview.md) as it is ("no system exists yet")
until something is implemented. Product documents need enough depth to start the first
release, not a complete vision. The [documentation map](../README.md#proportionate-requirements)
explains how much is enough.

### 5. Choose the stack as a change

The first implementation is usually L3: it fixes an architectural boundary and often
a public contract or data model. Treat it like any other L3 change:

1. `/sdd-spec` for the first increment of the MVP (what and why).
2. `/sdd-plan` with the proposed stack and structure; write an ADR for the stack
   decision when there are real alternatives.
3. Explicit `/sdd-implement` after the plan is accepted.
4. `/sdd-verify broad` plus independent review.

Do not write the proposed architecture into `architecture/overview.md` before it
exists. It belongs in the plan and ADR; the overview is updated after implementation.
See [starting a product](../development/methodology.md#2-starting-a-product).

### 6. Register the product checks

As soon as the stack has real lint, type, test, or build commands, register them:

1. Add each command to `.sdd/verification.json` with `kind: product`.
2. Assign it to the cumulative `focused`, `standard`, or `broad` product profile.
3. Document it in the README **Commands** table.
4. Run `python3 scripts/verify standard --base BASE --level LEVEL` and inspect the
   result.

Until then, product verification reports `blocked`. That is intended: it prevents an
empty suite from passing. Never register a placeholder command just to make it green.
The rules are in [connecting the product](../development/automation.md#connecting-the-product).

Changing `.sdd/verification.json` is itself an L3 change under the default risk rules,
because it changes what produces evidence. This includes adding the first product
check.

### 7. Adjust the risk rules to your layout

`.sdd/risk-rules.json` raises the minimum level for paths that usually carry L3 risk:
public contracts, `auth`/`permissions` directories, migrations, workflows, deployment,
and the framework's own controls. They are generic patterns. Once the code layout
exists, review them:

- Add the real locations of your contracts, schemas, migrations, and security code.
- Remove patterns that cannot occur in your project only if you are sure; extra
  patterns cost little.
- Check the floors themselves. The template is conservative: for example, it raises
  every change under `migrations/` to L3, while `AGENTS.md` makes a migration L3 only
  when it carries material risk. If most of your migrations are additive, you may
  lower that floor to L2 and keep classifying risky migrations as L3 by judgment.
  The [worked example](example/README.md#adoption-decisions) does exactly that.

The rules can only raise a floor. A path that matches nothing is not proven low risk.
See [risk floors](../development/automation.md#risk-floors-and-git-scope).

### 8. Activate the CI gate (optional)

The GitHub Actions gate is optional and not active until you configure it. In order:

1. Copy `.github/CODEOWNERS.example` to `.github/CODEOWNERS` with real owners, and run
   `python3 scripts/check-ci-setup`.
2. Open a small controlled PR and inspect the three jobs.
3. Import `.github/sdd-ruleset.template.json` as a ruleset and set it to Active.
4. Run the negative scenarios that prove merges are actually blocked.

Each step is detailed in the [activation sequence](../development/ci-enforcement.md#activation-sequence).
If your GitHub plan cannot enforce rulesets on your repository, follow
[the operating policy for that case](../development/ci-enforcement.md#when-the-platform-cannot-enforce-the-rules)
and record the state honestly.

Chapter 4 explains the CI gate in more depth.

### 9. Qualify your agent clients

The repository ships adapters for Claude Code, Codex, Cursor, and Copilot VS Code. The
generator always produces all four; adapters for clients you do not use are inert files.

For each client you actually use, start a fresh session at the repository root and run
the [compatibility trials](../../.agents/evals/compatibility.md): the `sdd-*` entries
appear, implementation is not selected automatically, and the reviewer has the
expected restrictions. Record the client version and results. Until then, treat the
client as unqualified. Chapter 5 covers each client.

## Path B: adding the framework to an existing repository

The steps are the same as path A from step 2 onward, with three differences: merging,
describing the existing system, and the CI bootstrap.

### Merge, do not overwrite

Copy the framework into a branch and resolve each collision by hand:

| Existing file | What to do |
| --- | --- |
| `AGENTS.md`, `CLAUDE.md` | Merge your existing agent rules into the framework's `AGENTS.md`. Keep it short and keep the classification table intact. `CLAUDE.md` should remain the one-line import. |
| `.github/copilot-instructions.md` | The generator refuses to overwrite an unmarked file. Merge your instructions into `AGENTS.md`, then remove the old file and regenerate. |
| `.claude/`, `.cursor/`, `.codex/`, `.agents/skills/` | Keep unrelated settings. Any existing entry whose name starts with `sdd-` is a collision that the generator rejects; rename yours. |
| `.github/workflows/` | Keep your workflows. Add `sdd.yml` alongside them. |
| `.github/pull_request_template.md` | Merge yours in, but keep the `sdd:metadata` block exactly as shipped. |
| `README.md` | Add the framework rows to your existing **Commands** section (create one if missing). |
| `.gitignore`, `.gitattributes` | Append the framework entries. |
| `docs/` | Move existing documents into the framework layout where they fit, or link to them; do not keep two versions of the same truth. |

Then run `python3 .agents/tools/sync_adapters.py --check` and the standard framework
verification.

### Describe what exists

In an existing repository, `architecture/overview.md` must describe the real system,
not "no system exists". Inspect the code first, and write only what you can confirm.
Mark everything else `TBD`. The same applies to product documents: record what the
product does today and leave gaps visible.

Register the existing test commands as product checks early (step 6), so that every
change after adoption has real evidence.

Do not create retroactive specs for features that already exist. The process applies
to changes from adoption onward.

### Handle the CI bootstrap once

The CI gate evaluates every PR with the policy from the **base** commit. The PR that
adds the framework has no framework in its base, so it cannot validate itself. Review
that PR under your existing rules, merge it, and only then follow the activation
sequence. Do not add a permanent bypass. See
[establishing the initial trusted version](../development/ci-enforcement.md#3-establish-the-initial-trusted-version).

## Things that surprise adopters

**Documentation is framework territory.** In `.sdd/ci.json`, `docs/**` and `README.md`
are framework paths. A PR that changes only Markdown documents is routed as
documentation and does not run product checks. This lets you merge a draft brief, spec,
or ADR without inventing an implementation. It also means that anything executable
placed under `docs/` escapes product checks: keep code out of `docs/`.

**`scripts/` is owned by the framework.** The protected CODEOWNERS block covers all of
`/scripts/`, so changes there need the framework owners' review. Put product scripts
in another directory (for example `tools/` or inside each component) unless the same
people own both.

**Everything in `.github/` is L3.** Workflows, templates, and ownership files control
the gate itself, so the risk rules classify them as L3. Adding an unrelated product
workflow is still an L3 change with independent review. This is deliberate.

**Framework-only passes are not product evidence.** `--target framework` checks the
framework files. It never stands in for product verification, even on a change that
looks documentation-only.

## First-week checklist

- [ ] Standard framework verification passes.
- [ ] Adoption owner recorded in the methodology header.
- [ ] Brief and MVP drafted; no invented facts.
- [ ] Architecture overview states the real current system (or its absence).
- [ ] First stack or feature change has an accepted spec and plan.
- [ ] Real product checks registered in `.sdd/verification.json` and the README.
- [ ] Risk rules reviewed against the real code layout.
- [ ] Each client in use has passed its compatibility trials.
- [ ] CI gate either activated and proven, or its unenforced state recorded.

## Next

The next chapter follows changes from request to completion, one level at a time.
