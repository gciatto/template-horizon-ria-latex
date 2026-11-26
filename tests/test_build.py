"""Check document selection and profile isolation at the build-process boundary."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BuildTests(unittest.TestCase):
    def test_only_document_roots_are_tex_files_at_project_root(self):
        self.assertEqual({path.name for path in ROOT.glob("*.tex")},
                         {"part-a.tex", "part-b.tex"})
        self.assertTrue((ROOT / "metadata.sty").is_file())

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="horizon build with spaces ")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        (self.project / "scripts").mkdir()
        shutil.copy2(ROOT / "scripts/build.py", self.project / "scripts/build.py")
        for document in ("part-a", "part-b"):
            (self.project / f"{document}.tex").write_text("source", encoding="utf-8")
        self.bin = self.project / "bin"
        self.bin.mkdir()
        compiler = self.bin / "latexmk"
        compiler.write_text(
            "#!" + sys.executable + "\n"
            "import json, os, pathlib, sys\n"
            "p=pathlib.Path(sys.argv[-1])\n"
            "record={'args':sys.argv[1:], 'cwd':os.getcwd(), 'driver':p.read_text()}\n"
            "pathlib.Path(os.environ['COMPILER_RECORD']).write_text(json.dumps(record))\n"
            "sys.exit(int(os.environ.get('COMPILER_EXIT', '0')))\n", encoding="utf-8")
        compiler.chmod(0o755)
        self.record = self.project / "compiler-record.json"

    def build(self, mode="submission", document="part-b", **overrides):
        env = os.environ.copy()
        for key in ("FUNDING", "PAGE_LIMIT", "COMPILER_EXIT", "BUDGET_XLSX"):
            env.pop(key, None)
        env.update(overrides)
        env["PATH"] = str(self.bin) + os.pathsep + env["PATH"]
        env["COMPILER_RECORD"] = str(self.record)
        return subprocess.run(
            [sys.executable, str(self.project / "scripts/build.py"), mode,
             "--document", document], env=env, text=True, capture_output=True)

    def test_profiles_reset_without_reusing_other_document_driver(self):
        self.assertEqual(self.build(FUNDING="lump-sum", PAGE_LIMIT="35").returncode, 0)
        original = json.loads(self.record.read_text())
        self.assertIn(r"\def\HEFunding{lump-sum}", original["driver"])
        self.assertIn(r"\def\HEPageLimit{35}", original["driver"])
        b_driver = self.project / original["args"][-1]
        self.assertEqual(self.build(document="part-a").returncode, 0)
        admin = json.loads(self.record.read_text())
        self.assertIn(r"\input{part-a.tex}", admin["driver"])
        self.assertNotEqual(admin["args"][-1], original["args"][-1])
        self.assertEqual(b_driver.read_text(), original["driver"])
        self.assertEqual(self.build().returncode, 0)
        reset = json.loads(self.record.read_text())
        self.assertIn(r"\def\HEFunding{standard}", reset["driver"])
        self.assertNotIn(r"\def\HEPageLimit", reset["driver"])
        self.assertEqual(reset["cwd"], str(self.project.resolve()))

    def test_empty_funding_and_part_b_limit_do_not_cap_part_a(self):
        self.assertEqual(self.build(document="part-a", FUNDING="", PAGE_LIMIT="1").returncode, 0)
        record = json.loads(self.record.read_text())
        self.assertIn(r"\def\HEFunding{standard}", record["driver"])
        self.assertNotIn(r"\def\HEPageLimit", record["driver"])
        self.assertIn("-jobname=part-a", record["args"])

    def test_modes_keep_separate_auxiliary_files_and_failures_propagate(self):
        self.assertEqual(self.build(mode="guidance", document="part-a").returncode, 0)
        guidance = json.loads(self.record.read_text())
        self.assertIn("-outdir=build/guidance", guidance["args"])
        self.assertIn("-jobname=part-a-guidance", guidance["args"])
        self.assertEqual(self.build(document="part-a", COMPILER_EXIT="7").returncode, 7)
        clean = json.loads(self.record.read_text())
        self.assertIn("-outdir=build/submission", clean["args"])
        self.assertNotEqual(guidance["args"][-1], clean["args"][-1])

    def test_invalid_profile_is_rejected_before_starting_compiler(self):
        self.assertEqual(self.build(FUNDING="unexpected").returncode, 2)
        self.assertFalse(self.record.exists())
        self.assertEqual(self.build(PAGE_LIMIT="0").returncode, 2)
        self.assertFalse(self.record.exists())

    def test_excel_generation_and_disabling_do_not_reuse_stale_tables(self):
        shutil.copytree(ROOT / 'scripts', self.project / 'scripts', dirs_exist_ok=True)
        shutil.copytree(ROOT / 'part-a/partners', self.project / 'part-a/partners')
        shutil.copy2(ROOT / 'metadata.sty', self.project / 'metadata.sty')
        shutil.copy2(ROOT / 'budget.xlsx', self.project / 'budget.xlsx')
        self.assertEqual(self.build(BUDGET_XLSX='budget.xlsx').returncode, 0)
        enabled = json.loads(self.record.read_text())['driver']
        self.assertIn(r'\def\HEExcelBudgetDirectory{build/submission/part-b-budget}', enabled)
        self.assertTrue((self.project / 'build/submission/part-b-budget/staff-effort.tex').exists())
        self.assertEqual(self.build(BUDGET_XLSX='').returncode, 0)
        self.assertNotIn('HEExcelBudgetDirectory', json.loads(self.record.read_text())['driver'])
        self.record.unlink()
        self.assertEqual(self.build(BUDGET_XLSX='missing.xlsx').returncode, 2)
        self.assertFalse(self.record.exists())


if __name__ == "__main__":
    unittest.main()
