"""CI must retain useful evidence when independent checks or builds fail."""
from pathlib import Path
import json
import re
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ci import Check, render_summary, run_checks


class CITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="horizon ci with spaces ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.results = self.root / "build/ci/results.json"

    def python_check(self, identifier, source, *, name=None, depends_on=()):
        return Check(identifier, name or identifier, (sys.executable, "-c", source), depends_on)

    def read_results(self):
        report = json.loads(self.results.read_text(encoding="utf-8"))
        self.assertIn("completed", report)
        return report, {item["id"]: item for item in report["checks"]}

    def write_results(self, report):
        self.results.parent.mkdir(parents=True, exist_ok=True)
        self.results.write_text(json.dumps(report), encoding="utf-8")

    def assert_incomplete_summary(self, summary):
        plain = re.sub(r"[*_`]+", "", summary).lower()
        self.assertNotRegex(plain, r"\ball checks (?:have )?passed\b")
        self.assertNotRegex(plain, r"\boverall(?: result| status)?\s*[:—-]?\s*(?:success|passed)\b")
        self.assertRegex(plain, r"missing|unavailable|incomplete|unfinished|not complete|not run|pending|running|interrupted|partial|unknown|could not")

    def test_failure_keeps_independent_checks_running_and_skips_dependents(self):
        checks = [
            self.python_check("fails", "import sys; print('FAILED CHECK'); sys.exit(3)"),
            self.python_check("dependent", "from pathlib import Path; Path('wrong.txt').write_text('ran')",
                              depends_on=("fails",)),
            self.python_check("independent", "from pathlib import Path; Path('continued.txt').write_text('ran')"),
        ]
        self.assertNotEqual(run_checks(self.root, checks), 0)
        report, records = self.read_results()
        self.assertTrue(report["completed"])
        self.assertEqual(records["fails"]["status"], "failed")
        self.assertEqual(records["fails"]["returncode"], 3)
        self.assertEqual(records["dependent"]["status"], "skipped")
        self.assertEqual(records["independent"]["status"], "passed")
        self.assertFalse((self.root / "wrong.txt").exists())
        self.assertEqual((self.root / "continued.txt").read_text(), "ran")

    def test_stdout_stderr_and_duration_are_retained_in_per_check_log(self):
        check = self.python_check(
            "compiler", "import sys; print('STDOUT SENTINEL', flush=True); "
            "print('STDERR SENTINEL', file=sys.stderr, flush=True); sys.exit(9)")
        self.assertNotEqual(run_checks(self.root, [check]), 0)
        _, records = self.read_results()
        record = records["compiler"]
        log = Path(record["log"])
        if not log.is_absolute():
            log = self.root / log
        text = log.read_text(encoding="utf-8")
        self.assertIn("STDOUT SENTINEL", text)
        self.assertIn("STDERR SENTINEL", text)
        self.assertEqual(record["returncode"], 9)
        self.assertIsInstance(record["duration_seconds"], (int, float))
        self.assertGreaterEqual(record["duration_seconds"], 0)

    def test_missing_executable_is_recorded_and_does_not_abort_other_checks(self):
        missing = Check("missing", "Missing executable", (str(self.root / "does-not-exist"),))
        independent = self.python_check("next", "print('still runs')")
        self.assertNotEqual(run_checks(self.root, [missing, independent]), 0)
        report, records = self.read_results()
        self.assertTrue(report["completed"])
        self.assertEqual(records["missing"]["status"], "failed")
        self.assertEqual(records["next"]["status"], "passed")
        log = Path(records["missing"]["log"])
        if not log.is_absolute():
            log = self.root / log
        self.assertIn("does-not-exist", log.read_text(encoding="utf-8"))

    def test_successful_summary_contains_artifact_links_and_check_status(self):
        check = self.python_check("ok", "print('done')", name="Administrative validation")
        self.assertEqual(run_checks(self.root, [check]), 0)
        env = {
            "CI_PDF_URL": "https://github.com/example/repo/actions/runs/42/artifacts/7",
            "CI_LOGS_URL": "https://github.com/example/repo/actions/runs/42/artifacts/8",
            "CI_RELEASE_URL": "https://github.com/example/repo/releases/tag/2026.11.25-14-07",
        }
        summary = render_summary(self.root, env=env)
        self.assertIn("Administrative validation", summary)
        self.assertRegex(summary.lower(), r"pass")
        for url in env.values():
            self.assertIn(url, summary)

    def test_missing_and_corrupt_results_do_not_claim_success(self):
        self.assert_incomplete_summary(render_summary(self.root, env={}))
        self.results.parent.mkdir(parents=True, exist_ok=True)
        self.results.write_text('{"completed": true, "checks": [', encoding="utf-8")
        self.assert_incomplete_summary(render_summary(self.root, env={}))

    def test_continue_on_error_does_not_turn_a_failed_workflow_stage_into_success(self):
        self.assertEqual(run_checks(self.root, [self.python_check("ok", "print('done')")]), 0)
        summary = render_summary(self.root, steps={
            "checks": {"outcome": "failure", "conclusion": "success"}
        }, env={})
        plain = re.sub(r"[*_`]+", "", summary).lower()
        self.assertNotIn("all checks passed", plain)
        workflow_stage = next(line for line in summary.splitlines()
                              if "Build and validation checks" in line)
        self.assertRegex(workflow_stage.lower(), r"fail")

    def test_partial_results_and_unfinished_checks_do_not_claim_success(self):
        self.write_results({"completed": False, "checks": [
            {"id": "finished", "name": "Finished check", "status": "passed",
             "returncode": 0, "duration_seconds": 0.1, "log": "build/ci/finished.log"}
        ]})
        self.assert_incomplete_summary(render_summary(self.root, env={}))
        self.write_results({"completed": True, "checks": [
            {"id": "finished", "name": "Finished check", "status": "passed",
             "returncode": 0, "duration_seconds": 0.1, "log": "build/ci/finished.log"},
            None,
        ]})
        self.assert_incomplete_summary(render_summary(self.root, env={}))
        for status in ("pending", "running", "unexpected", None):
            with self.subTest(status=status):
                entry = {"id": "unfinished", "name": "Unfinished check"}
                if status is not None:
                    entry["status"] = status
                self.write_results({"completed": True, "checks": [entry]})
                self.assert_incomplete_summary(render_summary(self.root, env={}))

    def test_failure_excerpt_preserves_tex_and_escapes_html_and_markdown(self):
        payload = "\\begin{tabular}{ll}\n```\n</pre></details><script>alert('x')</script>\nBAD & FAILED"
        check = self.python_check(
            "unsafe-log", "import sys; print(" + repr(payload) + "); sys.exit(1)",
            name="Compiler <script>alert('name')</script> | injected column")
        self.assertNotEqual(run_checks(self.root, [check]), 0)
        summary = render_summary(self.root, env={})
        self.assertIn("<details>", summary)
        self.assertIn("<pre>", summary)
        self.assertIn(r"\begin{tabular}{ll}", summary)
        self.assertIn("&lt;script&gt;", summary)
        self.assertIn("BAD &amp; FAILED", summary)
        self.assertNotIn("<script>", summary)
        self.assertNotIn("</pre></details><script>", summary)
        table_rows = "\n".join(line for line in summary.splitlines() if line.startswith("|"))
        self.assertNotIn(" | injected column", table_rows)


if __name__ == "__main__":
    unittest.main()
