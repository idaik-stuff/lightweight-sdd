# Lightweight SDD manual

This manual explains how and why to use the framework. It is explanatory: the rules
themselves live in [AGENTS.md](../../AGENTS.md) and [docs/development/](../development/methodology.md),
and this manual links to them rather than restating them.

## Chapters

1. [Concepts](01-concepts.md): the problem, the five core ideas, and the parts of the framework.
2. [Adoption](02-adoption.md): starting a new repository from the template or adding the framework to an existing one.
3. [Working a change](03-working-a-change.md): L0 to L3 from request to completion.
4. [Verification and CI](04-verification-ci.md): registering checks, reading evidence, and activating the gate.
5. [Agents](05-agents.md): using the workflows in each supported client and qualifying a client.
6. [Practices](06-practices.md): lessons and habits that keep the process lightweight.

## Supporting material

- [Worked example](example/README.md): complete artifacts for four changes to a
  fictitious library book-loan app, one per level.
- [Recipe: continuous deployment](recipes/continuous-deployment.md): adding CD as an
  L3 change without weakening the gates.
- [Maintenance](maintenance.md): versions, upgrading an adopting repository, changing
  the framework, and periodic checks.

## Reading paths

- **Evaluating the framework:** chapter 1, then the worked example.
- **Adopting it:** chapters 1, 2, and 4, then 5 for your agent clients.
- **Daily work:** chapter 3, with chapter 6 at hand.
