from support import Fixture
from sdd.common import ConfigError
from sdd.docs import anchors, check_docs, validate_change


class DocumentationTests(Fixture):
    def test_valid_local_link(self):
        self.write("README.md", "# Fixture\n[Page](docs/page.md#hello-world)\n")
        self.write("docs/page.md", "# Hello World\n")
        result = check_docs(self.root)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["local_links_checked"], 1)

    def test_missing_target(self):
        self.write("README.md", "[Page](missing.md)\n")
        self.assertEqual(check_docs(self.root)["status"], "failed")

    def test_missing_anchor(self):
        self.write("README.md", "# Fixture\n[Missing](#absent)\n")
        self.assertIn("missing heading", check_docs(self.root)["errors"][0])

    def test_fenced_and_inline_code_ignored(self):
        self.write("README.md", "# Fixture\n```text\n[x](missing.md)\n```\n`[x](missing.md)`\n~~~\n[x](missing.md)\n~~~\n")
        self.assertEqual(check_docs(self.root)["local_links_checked"], 0)

    def test_external_links_not_fetched(self):
        self.write("README.md", "[Web](https://example.invalid)\n[Mail](mailto:test@example.invalid)\n")
        self.assertEqual(check_docs(self.root)["local_links_checked"], 0)

    def test_encoded_space_and_reference_link(self):
        self.write("README.md", "[Page][ref]\n[ref]: docs/a%20b.md\n")
        self.write("docs/a b.md", "# Title\n")
        self.assertEqual(check_docs(self.root)["status"], "passed")

    def test_root_relative_link(self):
        self.write("docs/sub/page.md", "[Root](/README.md#fixture)\n")
        self.assertEqual(check_docs(self.root)["status"], "passed")

    def test_escape_link_fails(self):
        self.write("README.md", "[Escape](../README.md)\n")
        self.assertIn("escapes repository", check_docs(self.root)["errors"][0])

    def test_symlink_link_outside_fails(self):
        (self.root / "link").symlink_to(self.root.parent, target_is_directory=True)
        self.write("README.md", "[Escape](link/README.md)\n")
        self.assertIn("escapes repository", check_docs(self.root)["errors"][0])

    def test_duplicate_headings_have_distinct_anchors(self):
        self.assertEqual(anchors("# A\n# A\n# A\n"), {"a", "a-1", "a-2"})

    def test_code_in_heading_preserved(self):
        self.assertIn("use-scriptsverify", anchors("# Use `scripts/verify`\n"))

    def test_subset_does_not_scan_unselected_broken_doc(self):
        self.write("docs/bad.md", "[Missing](missing.md)\n")
        self.assertEqual(check_docs(self.root, ["README.md"])["status"], "passed")

    def test_draft_change_valid(self):
        ident = self.change()
        self.assertEqual(validate_change(self.root, ident), [])

    def test_missing_counterpart(self):
        ident = self.change()
        (self.root / f"docs/specs/{ident}/plan.md").unlink()
        self.assertIn("missing plan.md", validate_change(self.root, ident, require_pair=True)[0])

    def test_bad_change_id_rejected(self):
        with self.assertRaises(ConfigError):
            validate_change(self.root, "../escape")

    def test_invalid_status(self):
        ident = self.change(spec_state="invented")
        self.assertTrue(any("Status" in error for error in validate_change(self.root, ident)))

    def test_pending_rationale_rejected(self):
        ident = self.change()
        self.replace(f"docs/specs/{ident}/spec.md", "Intentional behavior change", "TBD")
        self.assertTrue(any("rationale" in error for error in validate_change(self.root, ident)))

    def test_duplicate_ac_rejected(self):
        ident = self.change()
        self.replace(f"docs/specs/{ident}/spec.md", "| AC-01 | A fixture | Run | Deterministic result |", "| AC-01 | One | Run | Result |\n| AC-01 | Two | Run | Result |")
        self.assertTrue(any("duplicate" in error for error in validate_change(self.root, ident)))

    def test_approved_spec_requires_recorded_acceptance(self):
        ident = self.change(spec_state="approved")
        self.replace(f"docs/specs/{ident}/spec.md", "Fixture approver / 2026-01-01", "TBD")
        self.assertTrue(any("scope acceptance" in error for error in validate_change(self.root, ident)))

    def test_approved_spec_rejects_pending_criteria(self):
        ident = self.change(spec_state="approved")
        self.replace(f"docs/specs/{ident}/spec.md", "Deterministic result", "TBD")
        self.assertTrue(any("pending placeholders" in error for error in validate_change(self.root, ident)))

    def test_approved_plan_requires_recorded_acceptance(self):
        ident = self.change(plan_state="approved")
        self.replace(f"docs/specs/{ident}/plan.md", "Fixture / 2026-01-01", "TBD")
        self.assertTrue(any("technical acceptance" in error for error in validate_change(self.root, ident)))

    def test_approved_plan_requires_ac_mapping(self):
        ident = self.change(plan_state="approved")
        self.replace(f"docs/specs/{ident}/plan.md", "| AC-01 | Fixture check", "| AC-99 | Fixture check")
        self.assertTrue(any("mapping for AC-01" in error for error in validate_change(self.root, ident)))

    def test_l3_plan_requires_broad(self):
        ident = self.change(level="L3", plan_state="approved")
        self.replace(f"docs/specs/{ident}/plan.md", "scope: `broad`", "scope: `standard`")
        self.assertTrue(any("L3 requires broad" in error for error in validate_change(self.root, ident)))

    def test_completed_plan_rejects_unresolved_result(self):
        ident = self.change(spec_state="implemented", plan_state="completed")
        self.replace(f"docs/specs/{ident}/plan.md", "| AC-01 | Passed |", "| AC-01 | Not run |")
        self.assertTrue(any("unresolved result" in error for error in validate_change(self.root, ident)))

    def test_implemented_spec_requires_completed_plan(self):
        ident = self.change(spec_state="implemented", plan_state="approved")
        self.assertTrue(any("requires completed plan" in error for error in validate_change(self.root, ident)))

    def test_structurally_complete_fixture_passes_without_authenticating_it(self):
        ident = self.change(spec_state="implemented", plan_state="completed")
        report = check_docs(self.root)
        self.assertEqual(report["errors"], [])
        self.assertIn("not authenticated", " ".join(report["limitations"]))

    def test_spec_can_exist_before_plan(self):
        ident = self.change()
        (self.root / f"docs/specs/{ident}/plan.md").unlink()
        self.assertEqual(validate_change(self.root, ident), [])

    def test_approved_spec_can_precede_planning(self):
        ident = self.change(spec_state="approved")
        (self.root / f"docs/specs/{ident}/plan.md").unlink()
        self.assertEqual(validate_change(self.root, ident), [])

    def test_spec_only_with_pending_plaintext_plan_reference_passes(self):
        ident = self.change()
        (self.root / f"docs/specs/{ident}/plan.md").unlink()
        self.replace(f"docs/specs/{ident}/spec.md", "Related plan: [plan](plan.md).", "Related plan: pending, not yet created.")
        self.assertEqual(check_docs(self.root)["status"], "passed")
