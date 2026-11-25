"""Compile shared partner sources to verify administrative rendering boundaries."""
from pathlib import Path
import json
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ('latexmk', 'pdflatex', 'pdftotext')
MISSING = [name for name in TOOLS if shutil.which(name) is None]
PARTNER = r"""\begin{ARecord}{participant}
\AField{participant.number}{1}
\AField{participant.role}{coordinator}
\AField{organisation.legal_name}{UNIQUEPARTNERNAME}
\AField{organisation.short_name}{UNI}
\AField{organisation.country}{Italy}
\begin{ARecord}{main_contact}
\AField{contact.first_name}{Private}
\AField{contact.last_name}{Contact}
\AField{contact.email}{private_contact@example.org}
\AField{contact.phone}{PRIVATECONTACTMARKER}
\end{ARecord}
\AField{participant.project_roles}{research_performer,education_training}
\AField{researcher.project_role}{team_member}
\end{ARecord}
\begin{ARecord}{budget_row}
\AField{budget.participant_number}{1}
\AField{budget.personnel_eur}{100.00}
\AField{budget.total_eligible_eur}{125.00}
\end{ARecord}
"""


@unittest.skipIf(MISSING, 'Missing LaTeX integration tools: ' + ', '.join(MISSING))
class AdminLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='he-admin-layout-')
        cls.addClassCleanup(cls.temp.cleanup)
        root = Path(cls.temp.name)
        for path in ROOT.glob('*.sty'):
            shutil.copy2(path, root / path.name)
        for path in ROOT.glob('*.def'):
            shutil.copy2(path, root / path.name)
        shutil.copy2(ROOT / '.latexmkrc', root / '.latexmkrc')
        (root / 'partners').mkdir()
        (root / 'partners/partner-1-UNI-admin-form.tex').write_text(PARTNER)
        (root / 'partners/participants.tex').write_text(
            r'\input{partners/partner-1-UNI-admin-form.tex}' + '\n')
        cls.results = {}
        for part, funding in [('B', 'standard'), ('A', 'standard'), ('A', 'lump-sum')]:
            name = f'part-{part}-{funding}'
            options = 'part-a,final' if part == 'A' else 'final'
            contents = r'\HEPrintPartners\HEPrintBudget' if part == 'A' else r'\HEPrintParticipantList'
            source = (r'\documentclass[a4paper,11pt]{article}' + '\n'
                      + r'\def\HEFunding{' + funding + '}\n'
                      + r'\usepackage[' + options + r']{he-ria26}' + '\n'
                      + r'\usepackage{he-admin26}' + '\n'
                      + r'\begin{document}' + '\n' + contents + '\n'
                      + (r'\ADeclaration{10}{LUMPSUMONLYMARKER}{yes}' if part == 'A' else '')
                      + '\n' + r'\end{document}' + '\n')
            (root / (name + '.tex')).write_text(source)
            result = subprocess.run(['latexmk', '-pdf', '-interaction=nonstopmode',
                                     '-halt-on-error', f'-outdir=build/{name}', name + '.tex'],
                                    cwd=root, capture_output=True, text=True, timeout=120)
            if result.returncode:
                raise AssertionError((result.stdout + result.stderr)[-10000:])
            pdf = root / 'build' / name / (name + '.pdf')
            text = subprocess.check_output(['pdftotext', str(pdf), '-'], text=True)
            metadata = json.loads(pdf.with_suffix('.hemeta').read_text())
            cls.results[(part, funding)] = (text, metadata)

    def test_shared_participant_list_excludes_administrative_details(self):
        text, metadata = self.results[('B', 'standard')]
        self.assertEqual(text.count('UNIQUEPARTNERNAME'), 1)
        self.assertNotIn('PRIVATECONTACTMARKER', text)
        self.assertNotIn('125.00', text)
        self.assertEqual(metadata['document_part'], 'B')
        self.assertEqual(metadata['page_limit'], 40)

    def test_administrative_content_and_enum_values_render_once(self):
        text, metadata = self.results[('A', 'standard')]
        self.assertEqual(text.count('PRIVATECONTACTMARKER'), 1)
        self.assertIn('125.00', text)
        self.assertIn('team member', text)
        self.assertIn('research performer', text)
        self.assertIsNone(metadata['page_limit'])
        self.assertEqual(metadata['document_part'], 'A')
        self.assertNotRegex(text, r'Part A\s*[–-]\s*Page\s+\d+\s+of\s+40')

    def test_lump_sum_declaration_is_profile_specific(self):
        standard, _ = self.results[('A', 'standard')]
        lump_sum, metadata = self.results[('A', 'lump-sum')]
        self.assertNotIn('LUMPSUMONLYMARKER', standard)
        self.assertIn('LUMPSUMONLYMARKER', lump_sum)
        self.assertEqual(metadata['funding'], 'lump-sum')
        self.assertIsNone(metadata['page_limit'])


if __name__ == '__main__':
    unittest.main()
