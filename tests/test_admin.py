"""Behavioral regressions for editable administrative data and partner creation."""
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from admin_data import args_of,read_source,text_value
from check_admin import check
from add_partner import add_partner


class AdminTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='he admin ')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        shutil.copy2(ROOT/'metadata.sty',self.root/'metadata.sty')
        shutil.copytree(ROOT/'part-a',self.root/'part-a')
        self.partner=self.root/'part-a/partners/partner-1-UNIBO-admin-form.tex'

    def replace_field(self,path,key,value):
        source=path.read_text()
        from admin_data import group,strip_comments
        clean=strip_comments(source)
        positions=[pos for (k,_),pos in args_of(source,'AField',2) if k==key]
        self.assertEqual(len(positions),1,key)
        start=positions[0]
        _,cursor=group(clean,start+len('\\AField'))
        _,end=group(clean,cursor)
        path.write_text(source[:start]+f'\\AField{{{key}}}{{{value}}}'+source[end:])

    def test_blank_template_is_valid_draft_but_incomplete_strict(self):
        draft=check(self.root)
        self.assertEqual(draft['errors'],[])
        self.assertGreater(len(draft['incomplete']),0)
        strict=check(self.root,strict=True)
        self.assertTrue(any('not answered' in e for e in strict['errors']))
        self.assertTrue(any('organisation.pic' in e for e in strict['errors']))

    def test_comments_escaped_symbols_and_nested_formatting_have_correct_counts(self):
        value=text_value('Café \\textbf{one \\emph{two}} \\& 50\\%\nwrapped\n\nNext')
        self.assertEqual(value.text,'Café one two & 50% wrapped\n\nNext')
        self.assertEqual(text_value('joined% hidden comment\nword').text,'joinedword')
        self.assertEqual(text_value(r'A\newline B\par C').text,'A\nB\n\nC')
        fake='% \\AField{bad}{value}\n\\AField{proposal.abstract}{A\\%B}'
        parsed=list(args_of(fake,'AField',2))
        self.assertEqual(len(parsed),1)
        self.assertEqual(parsed[0][0][0],'proposal.abstract')
        self.assertEqual(text_value(parsed[0][0][1]).text,'A%B')

    def test_metadata_macro_expands_before_enforcing_current_title_limit(self):
        meta=self.root/'metadata.sty'
        source=meta.read_text()
        source=source.replace(r'\renewcommand{\HEProjectTitle}{[proposal title]}',r'\renewcommand{\HEProjectTitle}{'+('A'*200)+'}')
        meta.write_text(source)
        report=check(self.root)
        title=next(x for x in report['field_counts'] if x['field']=='proposal.title')
        self.assertEqual(title['characters'],200)
        self.assertFalse(any('proposal.title' in e for e in report['errors']))
        meta.write_text(source.replace('A'*200,'A'*201))
        self.assertTrue(any('201 > 200' in e for e in check(self.root)['errors']))

    def test_unresolved_macro_is_not_certified_as_a_character_count(self):
        self.replace_field(self.root/'part-a/part-a-consortium.tex','proposal.abstract',r'\PrivateMacro{content}')
        draft=check(self.root)
        count=next(x for x in draft['field_counts'] if x['field']=='proposal.abstract')
        self.assertIsNone(count['characters'])
        self.assertTrue(count['unresolved_commands'])
        self.assertTrue(any('unresolved' in e for e in check(self.root,strict=True)['errors']))

    def test_partner_required_fields_are_not_satisfied_by_another_partner(self):
        for key,value in {'organisation.pic':'123456789','organisation.legal_name':'Example University','organisation.country':'IT'}.items():
            self.replace_field(self.partner,key,value)
        source=self.partner.read_text().replace(r'\AField{contact.first_name}{}',r'\AField{contact.first_name}{Ada}',1)
        source=source.replace(r'\AField{contact.last_name}{}',r'\AField{contact.last_name}{Example}',1)
        source=source.replace(r'\AField{contact.email}{}',r'\AField{contact.email}{ada@example.org}',1)
        self.partner.write_text(source)
        second=add_partner(2,'UU',root=self.root)
        report=check(self.root,strict=True)
        self.assertTrue(any(second.name in e and 'contact.first_name' in e for e in report['errors']))
        self.assertFalse(any(self.partner.name in e and 'contact.first_name' in e for e in report['errors']))

    def test_invalid_date_and_duplicate_record_field_fail_in_draft(self):
        self.replace_field(self.partner,'organisation.sme_validation_date','31/02/2026')
        source=self.partner.read_text().replace(r'\AField{organisation.pic}{}',r'\AField{organisation.pic}{}'+'\n'+r'\AField{organisation.pic}{123456789}')
        self.partner.write_text(source)
        errors=check(self.root)['errors']
        self.assertTrue(any('invalid date' in e for e in errors))
        self.assertTrue(any('duplicate organisation.pic' in e for e in errors))

    def test_record_limit_and_conditional_role_are_per_partner(self):
        source=self.partner.read_text()
        record='\\begin{ARecord}{achievement}\n\\AField{achievement.description}{}\n\\end{ARecord}\n'
        start=source.index(r'\begin{ARecord}{achievement}')
        self.partner.write_text(source[:start]+record*5+source[start:])
        self.replace_field(self.partner,'participant.project_roles','other')
        draft=check(self.root)
        self.assertTrue(any('6 achievement records' in e for e in draft['errors']))
        self.assertTrue(any('other_role_specification' in e for e in draft['incomplete']))

    def test_ethics_confirmation_does_not_itself_require_self_assessment(self):
        for path in (self.root/'part-a/ethics').glob('*questions.tex'):
            source=path.read_text().replace('{unanswered}{}','{no}{}')
            source=source.replace(r'\AField{ethics.confirmation}{unconfirmed}',r'\AField{ethics.confirmation}{yes}')
            path.write_text(source)
        report=check(self.root,strict=True)
        self.assertFalse(any('ethics.self_assessment' in e for e in report['errors']))
        path=self.root/'part-a/ethics/ethics-questions.tex'
        source=path.read_text()
        source=source.replace('Artificial Intelligence-based systems?}{no}{}','Artificial Intelligence-based systems?}{yes}{}')
        path.write_text(source)
        self.assertTrue(any('ethics.self_assessment.dimension' in e for e in check(self.root,strict=True)['errors']))

    def test_inferred_question_hierarchy_is_advisory(self):
        path=self.root/'part-a/ethics/ethics-questions.tex'
        source=path.read_text().replace('human participants?}{unanswered}{}','human participants?}{no}{}')
        source=source.replace('children/minors?}{unanswered}{}','children/minors?}{yes}{}')
        path.write_text(source)
        report=check(self.root)
        self.assertTrue(any('inferred parent' in w for w in report['warnings']))
        self.assertFalse(any('inferred parent' in e for e in report['errors']))

    def test_lump_sum_declaration_is_conditional(self):
        standard=check(self.root,strict=True,funding='standard')
        lump_sum=check(self.root,strict=True,funding='lump-sum')
        self.assertFalse(any('declaration 10' in e for e in standard['errors']))
        self.assertTrue(any('declaration 10' in e for e in lump_sum['errors']))

    def test_manifest_mismatch_and_identifier_mismatch_fail(self):
        self.replace_field(self.partner,'budget.participant_number','2')
        self.assertTrue(any('budget.participant_number must match' in e for e in check(self.root)['errors']))
        (self.root/'part-a/partners/participants.tex').write_text(r'\input{part-a/partners/partner-2-MISSING-admin-form.tex}')
        with self.assertRaisesRegex(ValueError,'manifest mismatch'):
            check(self.root)

    def test_add_partner_uses_pristine_data_and_preserves_manifest_comments(self):
        self.replace_field(self.partner,'organisation.legal_name','PRIVATE ORGANISATION')
        self.replace_field(self.partner,'budget.personnel_eur','987654.00')
        manifest=self.root/'part-a/partners/participants.tex'
        manifest.write_text('% Keep this author comment\n'+manifest.read_text())
        later=add_partner(12,'CnRs',root=self.root)
        earlier=add_partner(2,'uu',root=self.root)
        text=earlier.read_text()
        self.assertNotIn('PRIVATE ORGANISATION',text)
        self.assertNotIn('987654.00',text)
        self.assertNotIn(r'\HECoordinator',text)
        self.assertIn(r'\AField{organisation.short_name}{UU}',text)
        self.assertIn(r'\AField{budget.participant_number}{2}',text)
        self.assertIn('% Keep this author comment',manifest.read_text())
        self.assertLess(manifest.read_text().index(earlier.name),manifest.read_text().index(later.name))
        with self.assertRaises(ValueError):
            add_partner(2,'NEW',root=self.root)


if __name__=='__main__':
    unittest.main()
