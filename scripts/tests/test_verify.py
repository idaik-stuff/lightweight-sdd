import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest import mock

from support import Fixture, ROOT, command, manifest
from sdd.common import ConfigError
from sdd.verify import EXIT, aggregate, configuration, execute, run, save_report, select


class VerificationTests(Fixture):
    def quiet_run(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return run(self.root, **{"mode": "focused", "target": "framework", **kwargs})

    def test_shipped_configuration_is_valid(self):
        configuration(ROOT)

    def test_unknown_field_rejected(self):
        data = manifest()
        data["shell"] = True
        self.config(data)
        with self.assertRaises(ConfigError):
            configuration(self.root)

    def test_duplicate_check_id_rejected(self):
        self.config(manifest([command(), command()]))
        with self.assertRaises(ConfigError):
            configuration(self.root)

    def test_shell_string_rejected(self):
        check = command()
        check["argv"] = "echo success && dangerous-command"
        self.config(manifest([check]))
        with self.assertRaises(ConfigError):
            configuration(self.root)

    def test_bad_timeout_rejected(self):
        for timeout in (0, -1, True, "30", 100000):
            with self.subTest(timeout=timeout):
                self.config(manifest([command(timeout_seconds=timeout)]))
                with self.assertRaises(ConfigError):
                    configuration(self.root)

    def test_cwd_escape_rejected(self):
        self.config(manifest([command(cwd="../escape")]))
        with self.assertRaises(ConfigError):
            configuration(self.root)

    def test_unknown_profile_check_rejected(self):
        data = manifest()
        data["profiles"]["framework"]["focused"] = ["missing"]
        self.config(data)
        with self.assertRaises(ConfigError):
            configuration(self.root)

    def test_wrong_kind_cannot_count_as_product(self):
        data = manifest()
        data["profiles"]["product"]["focused"] = ["ok"]
        self.config(data)
        with self.assertRaises(ConfigError):
            configuration(self.root)

    def test_modes_inherit_cumulatively(self):
        data = manifest([command("one"), command("two"), command("three")])
        data["profiles"]["framework"] = {"focused": ["one"], "standard": ["two"], "broad": ["three"]}
        self.config(data)
        self.assertEqual([c["id"] for c in select(configuration(self.root), "framework", "broad")], ["one", "two", "three"])

    def test_product_includes_framework_checks(self):
        data = manifest([command(), command("product-test", "product")])
        self.config(data)
        self.assertEqual([c["kind"] for c in select(configuration(self.root), "product", "standard")], ["framework", "product"])

    def test_zero_checks_blocked(self):
        self.config(manifest([]))
        self.assertEqual(self.quiet_run()["status"], "blocked")

    def test_empty_product_profile_blocks(self):
        report = self.quiet_run(target="product")
        self.assertEqual(report["status"], "blocked")
        self.assertIn("No product checks", " ".join(report["reasons"]))
        self.assertTrue(all(c["status"] == "not_run" for c in report["checks"]))

    def test_product_needs_explicit_base_and_level(self):
        self.config(manifest([command("product-test", "product")]))
        self.init_git()
        self.write("change.txt", "change")
        report = self.quiet_run(target="product")
        self.assertEqual(report["status"], "blocked")
        self.assertIn("--base and --level", " ".join(report["reasons"]))

    def test_configured_product_fixture_executes(self):
        self.config(manifest([command(), command("product-test", "product")]))
        base = self.init_git()
        self.write("change.txt", "change")
        report = self.quiet_run(target="product", base=base, level="L1")
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["change_gate"]["status"], "passed")
        self.assertEqual(report["independent_review"], "not-assessed")

    def test_failed_change_gate_prevents_command_execution(self):
        self.config(manifest([command(code="from pathlib import Path; Path('should-not-exist').touch()")]))
        base = self.init_git()
        self.write("api/new.txt", "contract")
        report = self.quiet_run(base=base, level="L1")
        self.assertEqual(report["status"], "failed")
        self.assertFalse((self.root / "should-not-exist").exists())

    def test_passed_process(self):
        report = self.quiet_run()
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["checks"][0]["exit_code"], 0)

    def test_failed_process(self):
        self.config(manifest([command(code="raise SystemExit(7)")]))
        report = self.quiet_run()
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["checks"][0]["exit_code"], 7)

    def test_missing_executable_blocked(self):
        check = command()
        check["argv"] = ["sdd-deliberately-nonexistent-executable"]
        result = execute(self.root, check)
        self.assertEqual(result["status"], "blocked")

    def test_missing_environment_blocked_without_values(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            result = execute(self.root, command(requires_env=["SDD_REQUIRED_FIXTURE"]))
        self.assertEqual(result["status"], "blocked")
        self.assertIn("SDD_REQUIRED_FIXTURE", result["reason"])

    def test_timeout_blocked(self):
        result = execute(self.root, command(code="import time; time.sleep(5)", timeout_seconds=0.1))
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["exit_code"])

    def test_timeout_kills_posix_child_group(self):
        if os.name != "posix":
            self.skipTest("POSIX process-group behavior")
        child_code = "import time; from pathlib import Path; time.sleep(0.8); Path('orphan-marker').touch()"
        code = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c'," + repr(child_code) + "]); time.sleep(5)"
        result = execute(self.root, command(code=code, timeout_seconds=0.2))
        self.assertEqual(result["status"], "blocked")
        time.sleep(1.0)
        self.assertFalse((self.root / "orphan-marker").exists())

    def test_failed_dominates_blocked(self):
        self.assertEqual(aggregate([{"status": "blocked"}, {"status": "failed"}], ["missing"]), "failed")

    def test_source_mutation_invalidates_pass(self):
        self.config(manifest([command(code="from pathlib import Path; Path('README.md').write_text('mutated')")]))
        report = self.quiet_run()
        self.assertEqual(report["status"], "blocked")
        self.assertIn("changed during", " ".join(report["reasons"]))

    def test_failed_check_not_hidden_by_source_change(self):
        self.config(manifest([command(code="from pathlib import Path; Path('README.md').write_text('mutated'); raise SystemExit(1)")]))
        self.assertEqual(self.quiet_run()["status"], "failed")

    def test_dry_run_does_not_execute(self):
        self.config(manifest([command(code="from pathlib import Path; Path('marker').touch()")]))
        report = self.quiet_run(dry_run=True)
        self.assertEqual(report["status"], "not_run")
        self.assertEqual(EXIT[report["status"]], 3)
        self.assertFalse((self.root / "marker").exists())

    def test_reports_are_unique_and_parseable(self):
        report = self.quiet_run()
        first, second = save_report(self.root, report), save_report(self.root, report)
        self.assertNotEqual(first, second)
        self.assertEqual(json.loads(first.read_text())["status"], "passed")

    def test_reports_exclude_environment_values(self):
        with mock.patch.dict(os.environ, {"SDD_SECRET_FIXTURE": "secret-value-not-for-report"}):
            report = self.quiet_run()
        self.assertNotIn("secret-value-not-for-report", json.dumps(report))
        self.assertNotIn("stdout", json.dumps(report))

    def test_results_symlink_blocks_before_execution(self):
        (self.root / ".sdd/results").symlink_to(self.root / "docs", target_is_directory=True)
        self.write("docs/README.md", "# Docs")
        report = self.quiet_run()
        self.assertEqual(report["status"], "error")
        self.assertEqual(report["checks"], [])

    def test_interrupt_is_not_pass(self):
        self.assertEqual(aggregate([{"status": "interrupted"}], []), "interrupted")
        self.assertEqual(EXIT["interrupted"], 130)

    def test_cli_defaults_to_product_and_blocks(self):
        process = subprocess.run([sys.executable, str(ROOT / "scripts/verify"), "focused", "--root", str(self.root)],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(process.returncode, 3, process.stdout + process.stderr)
        self.assertIn("target=product", process.stdout)

    def test_cli_help_all_entrypoints(self):
        for name in ("verify", "check-docs", "check-change-level"):
            with self.subTest(name=name):
                process = subprocess.run([sys.executable, str(ROOT / "scripts" / name), "--help"],
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                self.assertEqual(process.returncode, 0, process.stderr)

    def test_invalid_kind_type_rejected_cleanly(self):
        data = manifest()
        data["checks"][0]["kind"] = []
        self.config(data)
        self.assertEqual(self.quiet_run()["status"], "error")

    def test_failed_and_blocked_commands_preserve_failure(self):
        missing = command("missing")
        missing["argv"] = ["sdd-no-such-executable"]
        self.config(manifest([command("fail", code="raise SystemExit(1)"), missing]))
        report = self.quiet_run()
        self.assertEqual(report["status"], "failed")
        self.assertEqual([item["status"] for item in report["checks"]], ["failed", "blocked"])

    def test_bad_root_is_not_created_for_report(self):
        missing = self.root / "missing-root"
        with self.assertRaises(ConfigError):
            save_report(missing, {"status": "error"})
        self.assertFalse(missing.exists())

    def test_interrupt_requests_process_cleanup(self):
        with mock.patch("sdd.verify.subprocess.Popen") as popen, mock.patch("sdd.verify.stop_process") as stop:
            popen.return_value.wait.side_effect = KeyboardInterrupt
            report = execute(self.root, command())
            self.assertEqual(report["status"], "interrupted")
            stop.assert_called_once_with(popen.return_value)
