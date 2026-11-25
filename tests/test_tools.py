"""Behavioural checks for proposal accounting and release packaging."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def pdf_fixture(path, dimensions):
    """Write valid, small PDFs without a third-party test dependency."""
    count = len(dimensions)
    font_id = 3 + 2 * count
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>"]
    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(count))
    objects.append(f"<< /Type /Pages /Count {count} /Kids [{kids}] >>".encode())
    for index, (width, height) in enumerate(dimensions):
        content_id = 4 + 2 * index
        objects.append((f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] "
                        f"/Resources << /Font << /F1 {font_id} 0 R >> >> "
                        f"/Contents {content_id} 0 R >>").encode())
        content = b"BT /F1 11 Tf 60 700 Td (Proposal text.) Tj ET"
        objects.append(f"<< /Length {len(content)} >>\nstream\n".encode() + content + b"\nendstream")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend((f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
                   f"startxref\n{xref}\n%%EOF\n").encode())
    path.write_bytes(output)


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="he ria tools ")
        self.directory = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def run_tool(self, name, *args, env=None):
        environment = os.environ.copy()
        environment.pop("VERSION", None)
        if env:
            environment.update(env)
        return subprocess.run([sys.executable, str(ROOT / "scripts" / name), *map(str, args)],
                              text=True, capture_output=True, env=environment)

    def proposal(self, count=2, limit=2, funding="standard", guidance=0, dimensions=None):
        path = self.directory / "proposal with spaces.pdf"
        pdf_fixture(path, dimensions or [(595.276, 841.89)] * count)
        path.with_suffix(".hemeta").write_text(json.dumps({
            "funding": funding, "page_limit": limit, "guidance": guidance
        }), encoding="utf-8")
        return path

    def test_page_boundary_and_json_counts(self):
        path = self.proposal()
        output = self.directory / "counts.json"
        result = self.run_tool("count_pdf.py", path, "--check", "--json", output)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(output.read_text())
        self.assertEqual(report["pages"], 2)
        self.assertEqual(report["page_limit"], 2)
        self.assertGreater(report["characters_with_whitespace"], report["characters_without_whitespace"])

    def test_over_limit_has_nonzero_status(self):
        result = self.run_tool("count_pdf.py", self.proposal(limit=1), "--check")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("exceeds", result.stdout)

    def test_call_specific_profile_overrides_are_observed(self):
        result = self.run_tool("count_pdf.py", self.proposal(limit=3, funding="lump-sum"), "--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("2 / 3", result.stdout)
        self.assertIn("lump-sum", result.stdout)

    def test_mixed_page_sizes_fail(self):
        result = self.run_tool("count_pdf.py", self.proposal(dimensions=[(595.276, 841.89), (612, 792)]), "--check")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("A4", result.stdout)

    def test_portrait_and_landscape_a4_pages_are_accepted(self):
        result = self.run_tool("count_pdf.py", self.proposal(dimensions=[(595.276, 841.89), (841.89, 595.276)]), "--check")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_guidance_pdf_is_not_accepted_by_submission_check(self):
        result = self.run_tool("count_pdf.py", self.proposal(guidance=1), "--check")
        self.assertEqual(result.returncode, 1, result.stderr)

    def test_part_a_is_uncapped_but_still_checks_size_and_guidance(self):
        path = self.proposal(count=41)
        metadata = {"document_part": "A", "funding": "standard",
                    "page_limit": None, "guidance": 0}
        path.with_suffix(".hemeta").write_text(json.dumps(metadata))
        result = self.run_tool("count_pdf.py", path, "--check")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Part A", result.stdout)
        self.assertIn("no page cap", result.stdout)
        metadata["guidance"] = 1
        path.with_suffix(".hemeta").write_text(json.dumps(metadata))
        self.assertEqual(self.run_tool("count_pdf.py", path, "--check").returncode, 1)

    def test_document_parts_cannot_bypass_metadata_validation(self):
        path = self.proposal()
        for part, limit in (("B", None), ("A", 40), ("C", None)):
            with self.subTest(part=part, limit=limit):
                path.with_suffix(".hemeta").write_text(json.dumps({
                    "document_part": part, "funding": "standard",
                    "page_limit": limit, "guidance": 0}))
                self.assertEqual(self.run_tool("count_pdf.py", path, "--check").returncode, 2)

    def test_missing_invalid_pdf_and_metadata_fail(self):
        path = self.directory / "missing.pdf"
        self.assertEqual(self.run_tool("count_pdf.py", path).returncode, 2)
        path.write_text("not a PDF", encoding="utf-8")
        self.assertEqual(self.run_tool("count_pdf.py", path).returncode, 2)
        path = self.proposal()
        path.with_suffix(".hemeta").unlink()
        self.assertEqual(self.run_tool("count_pdf.py", path).returncode, 2)
        path.with_suffix(".hemeta").write_text('{"funding":"standard","page_limit":-1,"guidance":0}')
        self.assertEqual(self.run_tool("count_pdf.py", path).returncode, 2)

    def test_literal_unicode_count_includes_newlines(self):
        path = self.directory / "field with spaces.txt"
        path.write_bytes("Café 🙂\n".encode("utf-8"))
        equal = self.run_tool("count_chars.py", path, "--limit", "7")
        over = self.run_tool("count_chars.py", path, "--limit", "6")
        self.assertEqual(equal.returncode, 0, equal.stderr)
        self.assertEqual(over.returncode, 1, over.stderr)
        self.assertIn("7", equal.stdout)

    def test_literal_character_count_preserves_crlf(self):
        path = self.directory / "crlf.txt"
        path.write_bytes(b"ab\r\n")
        result = self.run_tool("count_chars.py", path, "--limit", "3")
        self.assertEqual(result.returncode, 1)
        self.assertIn("4", result.stdout)

    def test_invalid_utf8_and_missing_text_fail(self):
        path = self.directory / "invalid.txt"
        self.assertEqual(self.run_tool("count_chars.py", path).returncode, 2)
        path.write_bytes(b"\xff")
        self.assertEqual(self.run_tool("count_chars.py", path).returncode, 2)

    def test_date_version_is_explicit_and_validated(self):
        result = self.run_tool("version.py", env={"VERSION": "2026.11.25-14-07"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "2026.11.25-14-07")
        invalid = self.run_tool("version.py", env={"VERSION": "2026.02.30-14-07"})
        self.assertEqual(invalid.returncode, 2)

    def test_distribution_includes_sources_and_omits_outputs(self):
        project = self.directory / "example project"
        project.mkdir()
        (project / "part-b2.tex").write_text("source")
        (project / "metadata.tex").write_text("metadata")
        (project / "Makefile").write_text("all:")
        (project / ".latexmkrc").write_text("config")
        (project / "figure.pdf").write_bytes(b"source figure")
        (project / "part-a.pdf").write_bytes(b"generated preview")
        (project / "VERSION").write_text("2026.10.01-09-00\n")
        (project / "build").mkdir()
        (project / "build" / "ignore.pdf").write_bytes(b"output")
        (project / ".git").mkdir()
        (project / ".git" / "config").write_text("private")
        (project / "draft.log").write_text("log")
        result = self.run_tool("package.py", "--root", project, "--version", "2026.11.25-14-07")
        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(project / "dist" / "he-ria26-2026.11.25-14-07-source.zip") as archive:
            names = archive.namelist()
        self.assertIn("he-ria26/part-b2.tex", names)
        self.assertIn("he-ria26/.latexmkrc", names)
        self.assertIn("he-ria26/figure.pdf", names)
        self.assertNotIn("he-ria26/part-a.pdf", names)
        self.assertEqual(names.count("he-ria26/VERSION"), 1)
        self.assertFalse(any(".git/" in name or "build/" in name or name.endswith(".log") for name in names))

    def test_distribution_requires_and_packages_all_four_pdfs_and_reports(self):
        project = self.directory / "release project"
        project.mkdir()
        (project / "part-b2.tex").write_text("source")
        version = "2026.11.25-14-07"
        pdfs = {"part-a-guidance": "guidance/part-a-guidance.pdf",
                "part-b2-guidance": "guidance/part-b2-guidance.pdf",
                "part-a": "submission/part-a.pdf", "part-b2": "submission/part-b2.pdf"}
        for index, (name, relative) in enumerate(pdfs.items()):
            path = project / "build" / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"PDF fixture {index}".encode())
        for name in ("counts", "part-a-counts", "admin-checks", "budget-checks"):
            (project / "build" / f"{name}.json").write_text("{}")
        result = self.run_tool("package.py", "--root", project, "--version", version, "--require-pdfs")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        for name, relative in pdfs.items():
            self.assertEqual((project / "dist" / f"he-ria26-{version}-{name}.pdf").read_bytes(),
                             (project / "build" / relative).read_bytes())
        for name in ("part-b2-checks", "part-a-checks", "admin-checks", "budget-checks"):
            self.assertTrue((project / "dist" / f"he-ria26-{version}-{name}.json").is_file())
        (project / "build/guidance/part-a-guidance.pdf").unlink()
        self.assertEqual(self.run_tool("package.py", "--root", project, "--version", version,
                                       "--require-pdfs").returncode, 2)


if __name__ == "__main__":
    unittest.main()
