"""Detailed budgets must reach both PDFs without trusting Excel formula caches."""
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from budget_excel import read_workbook, generate, table
from budget_workbook import load
from check_budget import check
from add_partner import add_partner


class ExcelBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='he excel budget ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / 'part-a/partners', self.root / 'part-a/partners')
        shutil.copy2(ROOT / 'metadata.sty', self.root / 'metadata.sty')
        self.book = self.root / 'budget.xlsx'
        shutil.copy2(ROOT / 'scripts/data/budget-template.xlsx', self.book)

    def edit(self, changes, sheet='partner-1'):
        book = load(self.book)
        for cell, value in changes.items():
            book[sheet][cell] = value
        book.save(self.book)

    def complete(self):
        self.edit({'C6': 100, 'C7': 'yes', 'C24': 350,
                   'C26': 0, 'C27': 0, 'C28': 0,
                   'C34': 'Researcher', 'D34': 1200, 'E34': 1,
                   'B42': 'Service', 'C42': 'WP1', 'D42': 40,
                   'B48': 'Device', 'C48': 'Equipment', 'D48': 60,
                   'E48': 12, 'F48': 6, 'G48': 1,
                   'B54': 'Materials', 'C54': 'WP1', 'D54': 50,
                   'B65': 'Meeting', 'C65': 'WP1', 'D65': 1, 'E65': 2, 'F65': 10,
                   'C16': 60, 'K9': 1, 'K10': 0, 'K11': 0,
                   'L9': 'yes', 'L10': 'yes', 'L11': 'yes'})

    def test_blank_template_is_incomplete_not_zero(self):
        report = check(self.root, workbook=self.book)
        self.assertEqual(report['errors'], [])
        self.assertEqual(report['totals'], {})
        self.assertTrue(report['incomplete'])
        self.assertTrue(check(self.root, strict=True, workbook=self.book)['errors'])

    def test_details_recompute_without_formula_caches(self):
        self.complete()
        report = check(self.root, strict=True, workbook=self.book)
        self.assertEqual(report['errors'], [])
        self.assertEqual(report['totals']['personnel_eur'], '100.00')
        self.assertEqual(report['totals']['indirect_eur'], '50.00')
        self.assertEqual(report['totals']['total_eligible_eur'], '350.00')
        output = self.root / 'generated'
        generate(self.root, self.book, output)
        self.assertIn('350.00', (output / 'overall-budget.tex').read_text())
        self.assertIn(r'\textbf{1}', (output / 'staff-effort.tex').read_text())

    def test_missing_effort_and_partial_detail_do_not_become_zero(self):
        self.complete()
        self.edit({'K10': None, 'F48': None})
        report = check(self.root, workbook=self.book)
        self.assertNotIn('personnel_eur', report['totals'])
        self.assertNotIn('equipment_eur', report['totals'])
        self.assertTrue(report['incomplete'])
        generate(self.root, self.book, self.root / 'generated')
        self.assertIn(r'\HEPlaceholder{pending}',
                      (self.root / 'generated/staff-effort.tex').read_text())

    def test_invalid_input_formulas_and_numbers_fail(self):
        self.complete()
        for address, value in [('D34', '=1+2'), ('D42', -1), ('D54', 'NaN'),
                               ('F65', 0.001), ('E48', 0), ('G48', 1.1)]:
            with self.subTest(address=address):
                original = load(self.book)['partner-1'][address].value
                self.edit({address: value})
                with self.assertRaises(ValueError):
                    read_workbook(self.book, self.root)
                self.edit({address: original})

    def test_manifest_and_tex_conflicts_fail(self):
        self.edit({'C3': 'OTHER'})
        with self.assertRaisesRegex(ValueError, 'manifest'):
            read_workbook(self.book, self.root)
        self.edit({'C3': 'UNIBO'})
        self.complete()
        partner = self.root / 'part-a/partners/partner-1-UNIBO-admin-form.tex'
        partner.write_text(partner.read_text().replace(
            r'\AField{budget.personnel_eur}{}', r'\AField{budget.personnel_eur}{999}'))
        self.assertTrue(any('conflicts' in e for e in check(self.root, workbook=self.book)['errors']))

    def test_lump_sum_requires_explicit_indirect_and_request(self):
        self.complete()
        self.edit({'C2': 'lump-sum'}, sheet='total')
        with self.assertRaisesRegex(ValueError, 'funding'):
            read_workbook(self.book, self.root)
        with self.assertRaisesRegex(ValueError, 'C21'):
            read_workbook(self.book, self.root, funding='lump-sum')
        self.edit({'C21': 10, 'C24': 400})
        report = check(self.root, strict=True, funding='lump-sum', workbook=self.book)
        self.assertEqual(report['errors'], [])
        self.assertEqual(report['totals']['total_eligible_eur'], '310.00')
        self.assertNotIn('maximum_eu_for_eligible_eur', report['totals'])

    def test_add_partner_updates_all_summaries_using_pristine_inputs(self):
        self.complete()
        add_partner(35, 'LATE', root=self.root)
        add_partner(2, 'NEXT', root=self.root)
        book = load(self.book)
        self.assertEqual(book['partner-1']['D34'].value, 1200)
        for name in ('partner-2', 'partner-35'):
            sheet = book[name]
            self.assertIsNone(sheet['D34'].value)
            self.assertIsNone(sheet['C7'].value)
            self.assertIsNone(sheet['K9'].value)
            self.assertIn('Staff_' + name.split('-')[1], sheet.tables)
        self.assertIn('partner-35', book['total']['B7'].value)
        self.assertIn('5:B7', book['total']['B8'].value)
        self.assertIn('5:B7', book['effort']['B8'].value)
        self.assertEqual(check(self.root, workbook=self.book)['errors'], [])

    def test_failed_workbook_save_does_not_leave_half_added_partner(self):
        from openpyxl.workbook.workbook import Workbook
        manifest = self.root / 'part-a/partners/participants.tex'
        before = manifest.read_bytes(), self.book.read_bytes()
        with patch.object(Workbook, 'save', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                add_partner(2, 'NEXT', root=self.root)
        self.assertEqual(before, (manifest.read_bytes(), self.book.read_bytes()))
        self.assertFalse((self.root / 'part-a/partners/partner-2-NEXT-admin-form.tex').exists())

    def test_extra_wp_columns_reach_new_partner_and_export(self):
        self.complete()
        book = load(self.book)
        sheet = book['partner-1']
        for cell, value in zip(('J12', 'K12', 'L12'), ('WP12', 0, 'yes')):
            sheet[cell] = value
        sheet.tables['Effort_1'].ref = 'J8:L12'
        book.save(self.book)
        add_partner(2, 'NEXT', root=self.root)
        book = load(self.book)
        self.assertEqual(book['effort']['E4'].value, 'WP12')
        self.assertEqual(book['partner-2']['J12'].value, 'WP12')
        self.assertIsNone(book['partner-2']['K12'].value)
        self.assertIn(r'A\&B\_1', table(['Partner', 'WP1'], [['A&B_1', '1']], [None]))

    def test_effort_mismatch_and_duplicate_leaders_fail(self):
        self.complete()
        self.edit({'K9': 2})
        with self.assertRaisesRegex(ValueError, 'differs'):
            read_workbook(self.book, self.root)
        self.edit({'K9': 1})
        add_partner(2, 'NEXT', root=self.root)
        self.edit({'L9': 'yes'}, sheet='partner-2')
        with self.assertRaisesRegex(ValueError, 'multiple'):
            read_workbook(self.book, self.root)

    def test_extra_categories_are_added_without_increasing_indirect_base(self):
        self.complete()
        self.edit({'C17': 100, 'C18': 50, 'C19': 20, 'C20': 10, 'C24': 530})
        report = check(self.root, strict=True, workbook=self.book)
        self.assertEqual(report['errors'], [])
        self.assertEqual(report['totals']['total_eligible_eur'], '530.00')
        self.assertEqual(report['totals']['indirect_eur'], '50.00')

    def test_matching_tex_calculated_amount_is_accepted(self):
        self.complete()
        path = self.root / 'part-a/partners/partner-1-UNIBO-admin-form.tex'
        path.write_text(path.read_text().replace(
            r'\AField{budget.indirect_eur}{}', r'\AField{budget.indirect_eur}{50.00}'))
        self.assertEqual(check(self.root, workbook=self.book)['errors'], [])

    def test_new_lump_sum_partner_has_blank_indirect_input(self):
        self.complete()
        self.edit({'C2': 'lump-sum'}, sheet='total')
        self.edit({'C21': 10, 'C24': 310})
        add_partner(2, 'NEXT', root=self.root)
        self.assertIsNone(load(self.book)['partner-2']['C21'].value)
        self.assertEqual(check(self.root, funding='lump-sum', workbook=self.book)['errors'], [])


if __name__ == '__main__':
    unittest.main()
