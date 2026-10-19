# Framework commands

This is the human registry of the framework's commands. Product commands live in the
"Commands" section of the repository's own `README.md`. `.sdd/verification.json` is the
machine source for automated check arguments and profile membership.

Run from the repository root. Framework automation requires Python 3.10 or later and
uses only the standard library; Git is required for change checks and product verification.

| Operation | Command | Scope / prerequisites |
| --- | --- | --- |
| Check all framework Markdown | `python3 scripts/check-docs` | Links, anchors, and structural conventions; not semantic approval. |
| Focused framework verification | `python3 scripts/verify focused --target framework` | Documentation, plus generated adapters where the generator is installed. |
| Standard framework verification | `python3 scripts/verify standard --target framework` | Focused checks plus the automation tests. |
| Broad framework verification | `python3 scripts/verify broad --target framework` | Inherits standard; no extra broad framework-only checks are configured. |
| Verification with the CI target | `python3 scripts/verify MODE --target auto --base BASE --level LEVEL` | Picks `framework` or `product` with the same rule and policy files as CI (including `.sdd/product-ci.json`); records the choice. |
| Change-level check | `python3 scripts/check-change-level --base BASE --level LEVEL` | Replace placeholders; add `--change ID` for L2/L3. |
| Product verification | `python3 scripts/verify MODE --base BASE --level LEVEL` | Add `--change ID` for L2/L3. Runs registered framework + product checks; blocked until product checks exist. |
| Check local CI ownership setup | `python3 scripts/check-ci-setup` | Exits 3 until real CODEOWNERS are configured; does not audit GitHub. |
| Test automation | `python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v` | Isolated CLI, configuration, Git, documentation, and runner tests. |
| Refuse pushes to the default branch | `git config core.hooksPath scripts/hooks` | Once per clone; see [CI enforcement](ci-enforcement.md). |

All selected checks are required. `standard` inherits `focused`; `broad` inherits both.
Manual, contract, migration, security, or recovery evidence remains change-specific
until a real deterministic command is added.

Reports are written locally to ignored `.sdd/results/`. Keep reviewed evidence
summaries in the plan or change record; do not commit raw reports or logs by default.
Approval, independent review, and deployment are separate decisions.

The command entrypoints also have executable permissions for POSIX checkouts. The
`python3 scripts/...` form avoids dependence on executable-bit preservation. Substitute
`python` only when it refers to the supported Python 3 interpreter.
