"""Compile real proposals to check page transitions and guidance/citations."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_TOOLS = ("latexmk", "pdflatex", "bibtex", "pdfinfo", "pdftotext")
MISSING_TOOLS = [name for name in REQUIRED_TOOLS if shutil.which(name) is None]
POINTS_PER_MM = 72 / 25.4

FIXTURE = r"""\documentclass[a4paper,11pt]{article}
\usepackage[MODE]{he-ria26}
\usepackage{metadata}
\begin{document}
\section{First portrait page\HEBudget{GUIDANCEBUDGETPROBE}}
AUTHOREDPORTRAITFIRST
TABLEFONTPROBE
\begin{tblr}{colspec={l}}
TABLEFONTPROBE
\end{tblr}
\begin{heguidance}
GUIDANCEENVPROBE
\label{hidden-guidance-label}
CITATIONPROBE \citep{SumersYNG2024}.
\end{heguidance}
\HEGuide{GUIDANCEINLINEPROBE \cite{SumersYNG2024}.}
\HECriterion{GUIDANCECRITERIONPROBE}{\cite{SumersYNG2024}.}
\begin{HELandscape}
\section*{Landscape page}
AUTHOREDLANDSCAPE
\end{HELandscape}
\section{Last portrait page}
AUTHOREDPORTRAITLAST
\HEPrintBibliography
\end{document}
"""


def run_checked(command):
    """Keep a failed compile useful without dumping every loaded package."""
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                            timeout=120, check=False)
    if result.returncode:
        detail = (result.stdout + result.stderr)[-12000:]
        raise AssertionError(f"Command failed ({result.returncode}): {command!r}\n{detail}")
    return result.stdout


def read_pages(pdf):
    """Read actual PDF page sizes and word coordinates using Poppler."""
    document = ET.fromstring(run_checked(["pdftotext", "-bbox", str(pdf), "-"]))
    pages = []
    for page in document.iter():
        if page.tag.rsplit("}", 1)[-1] != "page":
            continue
        words = [word for word in page.iter()
                 if word.tag.rsplit("}", 1)[-1] == "word"]
        pages.append({
            "width": float(page.attrib["width"]),
            "height": float(page.attrib["height"]),
            "words": words,
            "text": " ".join("".join(word.itertext()) for word in words),
        })
    return pages


@unittest.skipIf(MISSING_TOOLS, "Missing integration tools: " + ", ".join(MISSING_TOOLS))
class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="he-ria26-layout-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.directory = Path(cls.temp.name)
        cls.fixtures = {}
        for mode in ("final", "draft"):
            source = cls.directory / f"layout-{mode}.tex"
            source.write_text(FIXTURE.replace("MODE", mode), encoding="utf-8")
            output = cls.directory / mode
            output.mkdir()
            run_checked([
                "latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error",
                f"-outdir={output}", str(source),
            ])
            pdf = output / f"layout-{mode}.pdf"
            info = run_checked(["pdfinfo", str(pdf)])
            if not re.search(r"^Pages:\s+3\s*$", info, re.MULTILINE):
                raise AssertionError(f"The {mode} fixture should contain three pages:\n{info}")
            cls.fixtures[mode] = {
                "pdf": pdf,
                "pages": read_pages(pdf),
                "aux": pdf.with_suffix(".aux").read_text(encoding="utf-8"),
                "log": pdf.with_suffix(".log").read_text(encoding="utf-8"),
            }

    def test_landscape_restores_portrait_page_and_footer(self):
        """A portrait MediaBox alone does not prove output height was restored."""
        expected_mm = ((210, 297), (297, 210), (210, 297))
        for mode, fixture in self.fixtures.items():
            with self.subTest(mode=mode):
                pages = fixture["pages"]
                self.assertEqual(len(pages), 3)
                footer_positions = []
                for index, (page, (width, height)) in enumerate(zip(pages, expected_mm)):
                    self.assertAlmostEqual(page["width"], width * POINTS_PER_MM, delta=0.2)
                    self.assertAlmostEqual(page["height"], height * POINTS_PER_MM, delta=0.2)
                    footers = [word for word in page["words"] if word.text == "Part"]
                    self.assertEqual(len(footers), 1, f"Missing footer on {mode} page {index + 1}")
                    footer = footers[0]
                    top = float(footer.attrib["yMin"])
                    bottom = float(footer.attrib["yMax"])
                    self.assertGreaterEqual(top, page["height"] - 15 * POINTS_PER_MM)
                    self.assertLess(bottom, page["height"])
                    footer_positions.append(top)
                self.assertAlmostEqual(footer_positions[0], footer_positions[2], delta=0.5,
                                       msg="Portrait footer retains the landscape output height")

    def test_hidden_guidance_keeps_author_text_without_citation_side_effects(self):
        fixture = self.fixtures["final"]
        text = " ".join(page["text"] for page in fixture["pages"])
        for marker in ("AUTHOREDPORTRAITFIRST", "AUTHOREDLANDSCAPE", "AUTHOREDPORTRAITLAST"):
            self.assertIn(marker, text)
        for marker in ("GUIDANCEENVPROBE", "GUIDANCEINLINEPROBE",
                       "GUIDANCECRITERIONPROBE", "GUIDANCEBUDGETPROBE", "CITATIONPROBE"):
            self.assertNotIn(marker, text)
        self.assertNotIn("References", text)
        self.assertNotIn("hidden-guidance-label", fixture["aux"])
        self.assertNotIn(r"\citation", fixture["aux"])
        self.assertNotIn(r"\bibdata", fixture["aux"])
        self.assertFalse(fixture["pdf"].with_suffix(".bbl").exists())

    def test_table_text_retains_body_font_metrics(self):
        for mode, fixture in self.fixtures.items():
            with self.subTest(mode=mode):
                probes = [word for word in fixture["pages"][0]["words"]
                          if word.text == "TABLEFONTPROBE"]
                self.assertEqual(len(probes), 2)
                for start, end in (("xMin", "xMax"), ("yMin", "yMax")):
                    sizes = [float(word.attrib[end]) - float(word.attrib[start])
                             for word in probes]
                    self.assertAlmostEqual(*sizes, delta=0.01)

    def test_visible_guidance_resolves_numeric_example_citation(self):
        fixture = self.fixtures["draft"]
        text = " ".join(page["text"] for page in fixture["pages"])
        for marker in ("GUIDANCEENVPROBE", "GUIDANCEINLINEPROBE",
                       "GUIDANCECRITERIONPROBE", "GUIDANCEBUDGETPROBE"):
            self.assertIn(marker, text)
        self.assertRegex(text, r"CITATIONPROBE\s+\[\s*1\s*\]")
        self.assertIn("References", text)
        references = text.split("References", 1)[1]
        self.assertRegex(references, r"Sumers.*?2024")
        self.assertNotRegex(fixture["log"], r"Citation[^\n]*undefined")
        self.assertNotIn("There were undefined references", fixture["log"])


if __name__ == "__main__":
    unittest.main()
