# Recipe: adding continuous deployment as an L3 change

The framework deliberately ships no publishing or deployment workflow: deployment
targets vary too much, and the verification workflow must never hold deployment
credentials. This recipe shows how to add continuous deployment (CD) to your
repository as an ordinary L3 change, and which design rules keep it from weakening
the gates you already have.

It is a guide, not a tested component. Adapt it to your platform and verify it
through the change itself.

## Why it is L3

A deployment workflow is an irreversible operation that touches production,
secrets, and availability. The default risk rules agree: anything under
`.github/workflows/` (rule `delivery-policy`) and under `deploy/` or `ops/` (rule
`production-delivery`) has an L3 floor. So adding CD means:

- a spec and a plan, with the full risk-proportionate strategy;
- usually an ADR for the delivery model (where to deploy, push or pull, who may
  trigger it);
- broad verification, independent review, and code-owner review of `.github/`.

## Spec: what to agree on

Questions the spec should settle with the product owner:

- **What triggers a deployment?** Every merge to the default branch, a tag, or a
  manual dispatch.
- **What exactly is deployed?** The merged commit, or the newest commit that passed
  its checks. Can production ever move backwards?
- **Who can deploy outside the normal path,** and is that acceptable?
- **How is a deployment confirmed?** A health check, a version endpoint, a smoke test.
- **How are automatic deployments paused** (during an incident, a migration, or a
  holiday) without blocking manual deployment and rollback?
- **What does recovery look like?** Redeploying a previous version, and what about
  data migrations that already ran?

Example acceptance criteria:

| ID | Scenario / precondition | Action | Observable outcome |
| --- | --- | --- | --- |
| AC-01 | A PR is merged to the default branch with all checks passing. | The pipeline runs. | That commit is running in production, confirmed by its version endpoint. |
| AC-02 | A PR is opened or updated. | Any workflow runs. | No job has access to deployment credentials or write permissions. |
| AC-03 | Two merges finish their pipelines out of order. | Both deployment runs complete. | Production runs the newer commit. |
| AC-04 | The product checks fail on the default branch. | The pipeline runs. | Nothing is published or deployed. |
| AC-05 | A deployment fails its health check. | The pipeline finishes. | The run fails visibly; recovery follows the documented procedure. |
| AC-06 | Automatic deployment is paused. | A PR is merged. | Its artifact is published; nothing is deployed; a manual deployment still works. |

## A private repository on GitHub Free: what is missing and why it matters

Check your plan before designing the pipeline: on a **private** repository, several
of the controls a safe pipeline relies on depend on the GitHub plan. According to
GitHub's documentation (checked on 2026-09-30; verify the current
[plans](https://docs.github.com/en/get-started/learning-about-github/githubs-plans)
and [environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
pages before relying on this):

| Control | Public repository | Private repository on Free |
| --- | --- | --- |
| Rulesets / branch protection that block merges (required `sdd-gate`, required approvals) | Available | Not enforced |
| Deployment environments with their own secrets, limited to a branch | Available | Not available |
| Required reviewers on an environment ("approve this deployment") | Available | Not available (not on Pro or Team either) |

The ideal design is: merge only through a protected pull request, then deploy from a
`production` environment whose secret only the default branch can use, after a
person clicks **Approve**. On a private repository on Free, none of those three
pieces exists. That has three consequences:

1. **There is no approval step before deploying.** You must choose between deploying
   by hand every time, or deploying automatically with no human approval. If you
   choose automatic deployment, every merge goes to production.
2. **The deployment secret must be a repository secret,** readable by any workflow on
   any branch. Anyone with write access can push a branch whose workflow uses it, and
   so deploy code that never went through a pull request. This cannot be closed on
   this plan: record it as an accepted residual risk, keep write access to trusted
   people, and rotate the secret when access changes.
3. **Nothing forces a merge to pass `sdd-gate`.** The CD workflow must run the product
   checks again before publishing (see
   [do not trust the merge gate blindly](#do-not-trust-the-merge-gate-blindly)).

The first consequence is why you need a [pause switch](#provide-a-pause-switch).
With automatic deployment and no approval button, the owner has no way to say "not
now" for a while (during an incident, before a risky migration, on holiday) other
than editing the workflow, which is itself a reviewed change. A repository variable
gives that control back without touching code. It is a plain on/off switch, not an
approval per deployment and not a security control.

On a public repository, or on a plan where environment protection is available, use
a protected environment with required reviewers instead: it closes the second
consequence and gives you real approval. A pause switch remains useful even then.

## Plan: design rules

### Keep delivery separate from the gate

- Put CD in **its own workflow file**. Never add publishing, deployment, or secrets to
  `sdd.yml`; the gate runs untrusted pull-request code.
- Trigger CD on `push` to the default branch (or tags, or manual dispatch), **never on
  `pull_request`**, so pull-request code never runs with delivery permissions.
- If you chain workflows with `workflow_run`, remember it always executes the workflow
  file from the default branch. Check `conclusion == success` and the triggering event
  explicitly before doing anything.
- Do not use `pull_request_target` for anything in this pipeline.

### Least privilege

- Set `permissions: {}` at the top of the workflow and grant each job only what it
  needs (for example `packages: write` only in the publishing job).
- Pin every action to a full commit SHA, as `sdd.yml` does.
- Use `persist-credentials: false` on checkout. Avoid caches in jobs that hold secrets.

### Do not trust the merge gate blindly

If your platform does not enforce the `sdd-gate` requirement (see
[when the platform cannot enforce the rules](../../development/ci-enforcement.md#when-the-platform-cannot-enforce-the-rules)),
a commit can reach the default branch without passing its checks. In that case the CD
workflow must **run the product checks again** before publishing. It costs minutes and
removes a direct path from an unchecked push to production.

### Protect the deployment secret

This is the part most often underestimated:

- A repository-level secret is readable by **any workflow on any branch** that someone
  with write access pushes. Such a branch can deploy code that never went through a
  pull request.
- Use a protected deployment **environment** limited to the default branch, ideally
  with required reviewers. Where your plan does not offer protected environments
  (see [above](#a-private-repository-on-github-free-what-is-missing-and-why-it-matters)),
  record the residual risk explicitly in the plan, have the owner accept it, keep
  write access to trusted people, and rotate the secret when access changes.
- Prefer credentials that can only do one thing (trigger a specific deployment) over
  broad cloud credentials.

### Deploy deterministically

- Build once, tag the artifact with the full commit SHA, and deploy that exact artifact.
- To prevent out-of-order runs from moving production backwards, deploy "the newest
  commit on the default branch whose artifact is published", not "the commit that
  triggered this run", or serialize runs with a `concurrency` group.
- Expose the running version (for example `/version.json`) and confirm it after
  deploying, together with a health check. A deployment is complete only when that
  confirmation succeeds.

### Provide a pause switch

Sooner or later you need to stop automatic deployments for a while without losing the
ability to deploy or roll back by hand. When there is no approval step (see the
[private repository on GitHub Free](#a-private-repository-on-github-free-what-is-missing-and-why-it-matters)),
this switch is the owner's only brake. A GitHub Actions **repository variable** works
well, for example `AUTO_DEPLOY`:

```yaml
jobs:
  deploy:
    # Automatic runs are skipped while AUTO_DEPLOY is "false"; manual runs always proceed.
    if: >-
      github.event_name == 'workflow_dispatch' ||
      vars.AUTO_DEPLOY != 'false'
```

Set it under **Settings → Secrets and variables → Actions → Variables**. Design notes:

- **Default to deploying.** If the variable does not exist, automatic deployment is on.
  Document the exact pausing value (`false`); expression comparisons in the job `if`
  are case-insensitive, but other values such as `0` or `off` do not pause unless the
  deployment script also checks them.
- **Pause only the automatic path.** Manual dispatch (deploying a chosen commit or
  rolling back) must keep working while paused. That is why disabling the whole
  workflow, or the deployment target's webhook, is a worse pause: it also blocks
  recovery.
- **Resuming deploys nothing by itself.** Commits merged while paused reach production
  with the next automatic run or a manual run of the newest commit. Say so in the
  runbook.
- **A re-run reads the current value.** Re-running an old automatic run while paused
  is skipped too, so a re-run is not a way around the pause.
- **The variable is not a secret** and anyone with write access can change it. It is an
  operational switch, not a security control; record that in the plan.

### Risk-proportionate strategy

Address every row explicitly in the plan:

| Area | Typical content |
| --- | --- |
| Compatibility and consumers | What users see during a deployment; zero-downtime or a maintenance window. |
| Data, integrity, and migration | When migrations run, and whether the previous version can run against the migrated database. |
| Permissions, security, and privacy | Trigger isolation, job permissions, secret scope, and who can bypass the normal path. |
| Failures, load, and availability | Failed health check, partial rollout, and the platform being unavailable. |
| Change observability | Where each deployment is visible: run log, deployed version, alerts. |
| Rollout and feasible recovery | Redeploying a previous artifact; rehearsed before relying on it. Pausing automatic deployment. |

## Verification

Most CD behavior can only be verified on the real platform, so plan for it:

- Static review of the workflow: triggers, permissions, pins, secret usage. This is
  the independent reviewer's main focus.
- A first deployment observed end to end, with the version confirmation recorded.
- At least one negative scenario: a failing check on the default branch publishes
  nothing (AC-04); a pull request cannot read the secret (AC-02).
- A rehearsed recovery: deploy a previous version and confirm it.
- The pause switch: with it set, a merge publishes but does not deploy, and a manual
  deployment still works (AC-06). Then resume it.

Record what was observed, and keep anything not yet observed as pending. "The workflow
exists" is not "deployment works".

## After CD is in place

- **Delivery is now automatic.** Plans can record delivery as "deployed automatically
  on merge" with the run reference, instead of a manual entry.
- **Every merge is now a release.** The PR process (`sdd-gate`, human review, and for
  L3 the independent review) has become your release gate. If the platform does not
  enforce it, your written operating policy is all that stands between a mistake and
  production; say so in the CI enforcement status.
- **Update the README and architecture.** Document the pipeline, the secret's scope,
  the pause switch and its exact value, the recovery procedure, and the accepted
  residual risks. Repository variables and secrets live outside Git: list them by name
  (never their secret values) so that the configuration can be reproduced.
