from support import Fixture, ROOT
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

    def accepted(self, cell="Deterministic result"):
        # change() rewrites the same fixture files, so each call starts from a clean record.
        ident = self.change(spec_state="approved", plan_state="approved")
        self.replace(f"docs/specs/{ident}/spec.md", "Deterministic result |", f"{cell} |")
        return ident

    def placeholder_errors(self, ident):
        return [e for e in validate_change(self.root, ident) if "placeholder" in e or "acceptance" in e or "rationale" in e]

    def test_domain_vocabulary_in_criteria_is_not_a_placeholder(self):
        for cell in ("The list shows `Changes pending`", "The order shows as pending",
                     "A pending payment is refunded", "Retry when TODO items remain"):
            with self.subTest(cell=cell):
                self.assertEqual(self.placeholder_errors(self.accepted(cell)), [])

    def test_prose_outside_the_criteria_table_is_not_checked(self):
        ident = self.accepted()
        self.replace(f"docs/specs/{ident}/spec.md", "## Acceptance and next steps",
                     "Rows marked pending in the product stay visible.\n\n## Acceptance and next steps")
        self.assertEqual(self.placeholder_errors(ident), [])

    def test_placeholder_criteria_cells_rejected(self):
        for cell in ("TBD", "`TBD`", "TODO", "pending", "Pending", "not run", "Not run", "TBD - What is observed",
                     "TBD – guidance", "tbd", "TBD.", "Pending.", "TBD: what is observed", "TBD?", "(TBD)",
                     "*TBD*", "**TBD**", "_TBD_", "<TBD>", "`TBD` - guidance", "not  run", "not run",
                     "- TBD", "\"TBD\""):
            with self.subTest(cell=cell):
                errors = self.placeholder_errors(self.accepted(cell))
                self.assertTrue(any("pending placeholders" in e for e in errors), errors)

    def test_placeholder_in_any_criteria_column_rejected(self):
        ident = self.change(spec_state="approved")
        self.replace(f"docs/specs/{ident}/spec.md", "| AC-01 | A fixture | Run |", "| AC-01 | A fixture | `TBD` |")
        self.assertTrue(any("pending placeholders" in e for e in validate_change(self.root, ident)))

    def test_acceptance_fields_starting_with_placeholder_rejected(self):
        # Replace the whole backticked value so `TBD` reaches clean(), not the missing-value path.
        cases = {"spec": ("`Fixture approver / 2026-01-01`", "scope acceptance"),
                 "plan": ("`Fixture / 2026-01-01`", "technical acceptance")}
        for name, (old, message) in cases.items():
            for value in ("pending", "`TBD`", "pending owner review", "TODO: ask the owner", "(pending)",
                          "*TBD*", "- pending", "_TODO_", '"TBD"'):
                with self.subTest(file=name, value=value):
                    ident = self.change(spec_state="approved", plan_state="approved")
                    self.replace(f"docs/specs/{ident}/{name}.md", old, value)
                    self.assertTrue(any(message in e for e in validate_change(self.root, ident)))

    def test_concrete_fields_with_later_placeholder_word_pass(self):
        ident = self.change(spec_state="approved", plan_state="approved")
        self.replace(f"docs/specs/{ident}/spec.md", "Fixture approver / 2026-01-01",
                     "Owner, 2026-10-19, after the pending items were resolved")
        self.replace(f"docs/specs/{ident}/spec.md", "Intentional behavior change", "Changes how pending orders are shown")
        self.replace(f"docs/specs/{ident}/plan.md", "Fixture / 2026-01-01", "Owner / 2026-10-19, TBD items closed")
        self.assertEqual(validate_change(self.root, ident), [])

    def test_draft_records_are_not_checked_for_placeholders(self):
        ident = self.change()
        self.replace(f"docs/specs/{ident}/spec.md", "Deterministic result |", "TBD |")
        self.replace(f"docs/specs/{ident}/spec.md", "Fixture approver / 2026-01-01", "pending")
        self.replace(f"docs/specs/{ident}/plan.md", "Fixture / 2026-01-01", "TBD")
        self.assertEqual(validate_change(self.root, ident), [])

    def test_targeted_sentences_fail_unless_quoted(self):
        ident = self.change(spec_state="approved")
        spec = f"docs/specs/{ident}/spec.md"
        self.replace(spec, "Related plan: [plan](plan.md).", "Related plan: [plan](plan.md).\nScope acceptance: pending.")
        self.assertTrue(any("still pending" in e for e in validate_change(self.root, ident)))
        self.replace(spec, "\nScope acceptance: pending.", "\nThe check rejects `Scope acceptance: pending`.")
        self.assertEqual(validate_change(self.root, ident), [])

    def test_completed_plan_verified_sentence_fails_unless_quoted(self):
        ident = self.change(spec_state="implemented", plan_state="completed")
        plan = f"docs/specs/{ident}/plan.md"
        self.replace(plan, "Verified version or diff: synthetic fixture only.", "Verified version or diff: pending.")
        self.assertTrue(any("version/diff" in e for e in validate_change(self.root, ident)))
        self.replace(plan, "Verified version or diff: pending.",
                     "Verified version or diff: abc1234. The template line `Verified version or diff: pending` was replaced.")
        self.assertEqual(validate_change(self.root, ident), [])

    def test_unresolved_result_cells_keep_the_1_0_rule(self):
        # Unchanged from 1.0.0 on purpose: a stricter rule would fail historical records in every PR.
        for cell, fails in (("Not run", True), ("blocked", True), ("Failed", True), ("pending", True),
                            ("`not run`", False), ("Passed (not run on macOS)", False)):
            with self.subTest(cell=cell):
                ident = self.change(spec_state="implemented", plan_state="completed")
                self.replace(f"docs/specs/{ident}/plan.md", "| AC-01 | Passed |", f"| AC-01 | {cell} |")
                errors = validate_change(self.root, ident)
                self.assertEqual(any("unresolved result" in e for e in errors), fails, errors)

    def test_exact_state_name_cell_is_a_placeholder(self):
        # Accepted trade-off: a whole outcome cell of only `pending` reads as a placeholder.
        for cell in ("pending", "`pending`", "Pending - awaiting payment"):
            with self.subTest(cell=cell):
                self.assertTrue(self.placeholder_errors(self.accepted(cell)))
        self.assertEqual(self.placeholder_errors(self.accepted("The order is `pending`")), [])

    def test_sentence_quoted_in_closed_fence_passes(self):
        ident = self.change(spec_state="approved")
        self.replace(f"docs/specs/{ident}/spec.md", "## Acceptance and next steps",
                     "```text\nScope acceptance: pending.\n```\n\n## Acceptance and next steps")
        self.assertEqual(validate_change(self.root, ident), [])

    def test_unclosed_fence_does_not_hide_open_sentences(self):
        ident = self.change(spec_state="approved")
        self.replace(f"docs/specs/{ident}/spec.md", "## Acceptance and next steps",
                     "```text\nan example left open\n\n## Acceptance and next steps\n\nScope acceptance: pending.")
        self.assertTrue(any("still pending" in e for e in validate_change(self.root, ident)))

    def test_rationale_starting_with_placeholder_rejected(self):
        for value in ("pending migration review", "TBD - why", "*TODO*"):
            with self.subTest(value=value):
                ident = self.change()
                self.replace(f"docs/specs/{ident}/spec.md", "`Intentional behavior change`", value)
                self.assertTrue(any("rationale" in e for e in validate_change(self.root, ident)))

    def test_unchanged_templates_as_accepted_records_fail(self):
        ident = "CHG-900-template"
        expected = {("approved", "approved"): ("Level rationale", "scope acceptance", "pending placeholders",
                                               "still pending", "technical acceptance"),
                    ("implemented", "completed"): ("version/diff", "unresolved result")}
        for (spec_state, plan_state), messages in expected.items():
            for name, state in (("spec", spec_state), ("plan", plan_state)):
                text = (ROOT / f"docs/templates/{name}.md").read_text(encoding="utf-8")
                self.write(f"docs/specs/{ident}/{name}.md", text.replace("Status: `draft`", f"Status: `{state}`"))
            errors = validate_change(self.root, ident)
            for message in messages:
                with self.subTest(state=spec_state, message=message):
                    self.assertTrue(any(message in e for e in errors), errors)

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
