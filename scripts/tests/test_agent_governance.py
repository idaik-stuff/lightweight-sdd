"""Policy integration for new agent paths; no live GitHub/client assertions."""
import json
from pathlib import Path

from support import Fixture, ROOT
from sdd.changes import load_rules, matches
from sdd.ci import ci_configuration
from sdd.ci_setup import PROTECTED, owners
from sdd.docs import check_docs


class AgentGovernanceTests(Fixture):
    def test_new_client_paths_are_framework_paths_in_shipped_policy(self):
        policy = ci_configuration(ROOT)
        for path in ('.cursor/agents/sdd-independent-review.md', '.codex/agents/sdd-independent-review.toml'):
            with self.subTest(path=path):
                self.assertTrue(any(matches(path, pattern) for pattern in policy['framework_paths']))

    def test_every_invocation_and_reviewer_surface_has_l3_floor(self):
        rules = load_rules(ROOT)
        for path in ('.agents/workflows/implement/SKILL.md', '.agents/skills/sdd-implement/SKILL.md',
                     '.agents/skills/sdd-implement/agents/openai.yaml', '.agents/review/independent-review.md',
                     '.claude/skills/sdd-implement/SKILL.md', '.claude/agents/sdd-independent-review.md',
                     '.cursor/agents/sdd-independent-review.md', '.codex/agents/sdd-independent-review.toml',
                     '.github/agents/sdd-independent-review.agent.md', '.github/copilot-instructions.md'):
            with self.subTest(path=path):
                self.assertTrue(any(rule['minimum_level']=='L3' and any(matches(path,g) for g in rule['paths'])
                                    for rule in rules))

    def test_current_ownership_includes_new_roots(self):
        self.assertIn('/.cursor/', PROTECTED)
        self.assertIn('/.codex/', PROTECTED)
        actual = (ROOT/'.github/CODEOWNERS.example').read_text().replace('@REPLACE-WITH-OWNER','@fixture-owner')
        self.assertEqual(owners(actual), [])

    def test_old_ownership_shape_does_not_count_as_ready(self):
        text = '\n'.join(p+' @fixture-owner' for p in PROTECTED if p not in ('/.cursor/','/.codex/'))
        self.assertTrue(owners(text))

    def test_new_cursor_markdown_is_checked(self):
        self.write('.cursor/agents/custom.md', '[missing](not-present.md)\n')
        self.assertTrue(any('not-present.md' in e for e in check_docs(self.root)['errors']))

    def test_new_codex_markdown_is_checked(self):
        self.write('.codex/README.md', '[missing](not-present.md)\n')
        self.assertTrue(any('not-present.md' in e for e in check_docs(self.root)['errors']))
