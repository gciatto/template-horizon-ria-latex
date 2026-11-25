"""Budget arithmetic must reject invalid numbers without inventing missing data."""
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from admin_data import group,args_of,strip_comments
from check_budget import check,INPUTS


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='he budget ')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        shutil.copy2(ROOT/'metadata.tex',self.root/'metadata.tex')
        shutil.copytree(ROOT/'partners',self.root/'partners')
        self.path=self.root/'partners/partner-1-UNIBO-admin-form.tex'

    def set_values(self,**values):
        source=self.path.read_text()
        for name,value in values.items():
            clean=strip_comments(source)
            for (key,_),start in args_of(source,'AField',2):
                if key=='budget.'+name:
                    _,cursor=group(clean,start+len('\\AField'))
                    _,end=group(clean,cursor)
                    source=source[:start]+f'\\AField{{{key}}}{{{value}}}'+source[end:]
                    break
            else:
                self.fail(name)
        self.path.write_text(source)

    def complete_inputs(self):
        self.set_values(personnel_eur='100.00',subcontracting_eur='40.00',
                        travel_subsistence_eur='20.00',equipment_eur='30.00',
                        other_goods_works_services_eur='50.00',internally_invoiced_eur='60.00',
                        funding_rate_pct='100',requested_eu_eur='350.00',income_generated_eur='0',
                        financial_contributions_eur='0',own_resources_eur='0')

    def test_empty_budget_is_draft_not_zero_budget(self):
        draft=check(self.root)
        self.assertEqual(draft['errors'],[])
        self.assertEqual(draft['totals'],{})
        self.assertTrue(draft['incomplete'])
        self.assertTrue(check(self.root,strict=True)['errors'])

    def test_standard_indirect_base_excludes_subcontracting_and_internal_invoices(self):
        self.complete_inputs()
        report=check(self.root,strict=True)
        self.assertEqual(report['errors'],[])
        self.assertEqual(report['rows'][0]['calculated']['indirect_eur'],'50.00')
        self.assertEqual(report['totals']['total_eligible_eur'],'350.00')
        self.assertEqual(report['totals']['requested_eu_eur'],'350.00')
        self.assertEqual(report['totals']['total_estimated_income_eur'],'350.00')
        self.assertNotIn('funding_rate_pct',report['totals'])

    def test_wrong_derived_amount_and_excess_request_fail(self):
        self.complete_inputs()
        self.set_values(indirect_eur='75.00',requested_eu_eur='351.00')
        errors=check(self.root)['errors']
        self.assertTrue(any('indirect_eur' in e for e in errors))
        self.assertTrue(any('exceeds calculated' in e for e in errors))

    def test_negative_nonfinite_and_overprecise_values_fail_in_every_column(self):
        for key,value in [('income_generated_eur','-1'),('max_grant_amount_eur','NaN'),
                          ('own_resources_eur','Infinity'),('financial_contributions_eur','0.001')]:
            with self.subTest(key=key):
                self.set_values(**{key:value})
                self.assertTrue(any(key in e for e in check(self.root)['errors']))
                self.set_values(**{key:''})

    def test_estimated_income_includes_request_and_all_three_other_sources(self):
        self.complete_inputs()
        self.set_values(requested_eu_eur='300',income_generated_eur='10',
                        financial_contributions_eur='20',own_resources_eur='20',
                        total_estimated_income_eur='349')
        report=check(self.root)
        self.assertEqual(report['totals']['total_estimated_income_eur'],'350.00')
        self.assertTrue(any('total_estimated_income_eur' in e for e in report['errors']))

    def test_lump_sum_does_not_apply_standard_indirect_or_reimbursement_formula(self):
        self.complete_inputs()
        self.set_values(indirect_eur='10',total_eligible_eur='310',
                        maximum_eu_for_eligible_eur='900',requested_eu_eur='400')
        report=check(self.root,funding='lump-sum')
        self.assertEqual(report['errors'],[])
        self.assertNotIn('indirect_eur',report['rows'][0]['calculated'])
        self.assertNotIn('maximum_eu_for_eligible_eur',report['rows'][0]['calculated'])
        self.assertEqual(report['rows'][0]['calculated']['total_eligible_eur'],'310.00')
        self.assertTrue(check(self.root,funding='standard')['errors'])


if __name__=='__main__':
    unittest.main()
