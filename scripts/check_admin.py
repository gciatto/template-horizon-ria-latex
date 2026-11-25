#!/usr/bin/env python3
"""Check editable Part A TeX fields; blanks are allowed until --strict is used."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import re
import sys

from admin_data import (ROOT, SCHEMA, QUESTIONS, PARTNER_NAME, TextValue,
                        read_project, record_values)


def location(root, item):
    return f'{item.file.relative_to(root)}:{item.line}'


def valid_pages(value):
    if not value:
        return True
    for part in re.split(r'\s*[,;]\s*', value):
        match = re.fullmatch(r'([1-9][0-9]*)(?:\s*[-–]\s*([1-9][0-9]*))?', part)
        if not match or (match.group(2) and int(match.group(2)) < int(match.group(1))):
            return False
    return True


def check(root=ROOT, strict=False, funding='standard'):
    root = Path(root).resolve()
    sources = read_project(root)
    errors, warnings, incomplete, counts = [], [], [], []
    all_fields = [item for source in sources for item in source.fields]
    global_values = {}
    partners = []

    def missing(message):
        incomplete.append(message)
        if strict:
            errors.append(message)

    def require(values, key, where):
        value = values.get(key, TextValue(''))
        if value.missing:
            missing(f'{where}: {key} is not completed')
        elif value.unknown_commands:
            (errors if strict else warnings).append(
                f'{where}: {key} contains unresolved commands; verify its value')

    for source in sources:
        seen = set()
        is_partner = source.path.parent.name == 'partners'
        for item in source.fields:
            where = location(root, item)
            identity = (item.record, item.key)
            if identity in seen:
                errors.append(f'{where}: duplicate {item.key} in the same record')
            seen.add(identity)
            definition = SCHEMA['fields'].get(item.key)
            if not definition:
                errors.append(f'{where}: unknown field {item.key}')
                continue
            if not is_partner:
                if item.key in global_values:
                    errors.append(f'{where}: duplicate consortium field {item.key}')
                global_values[item.key] = item.value
            if is_partner:
                expected_record = 'budget_row:' if item.key.startswith('budget.') else 'participant:'
                if not item.record or not item.record[0].startswith(expected_record):
                    errors.append(f'{where}: {item.key} is outside its {expected_record[:-1]} record')
            val = item.value
            limit = definition.get('max_chars')
            if limit is not None:
                counts.append({'file':str(source.path.relative_to(root)), 'line':item.line,
                               'field':item.key, 'record':'/'.join(item.record),
                               'characters':None if val.unknown_commands else len(val.text),
                               'limit':limit, 'spaces_included':True,
                               'confidence':definition.get('confidence'),
                               'complete':not val.missing,
                               'unresolved_commands':list(val.unknown_commands)})
            if val.missing:
                continue
            if val.unknown_commands:
                (errors if strict else warnings).append(
                    f'{where}: {item.key}: unresolved {", ".join(val.unknown_commands)}; text count/type not certified')
                continue
            text = val.text
            if limit is not None and len(text) > limit:
                errors.append(f'{where}: {item.key}: {len(text)} > {limit} characters including spaces')
            illegal = set(definition.get('forbidden_characters','')).intersection(text)
            if illegal:
                errors.append(f'{where}: {item.key}: forbidden characters {sorted(illegal)}')
            ty = definition['type']
            if ty == 'boolean' and text.casefold() not in ('yes','no','true','false'):
                errors.append(f'{where}: {item.key}: expected yes or no')
            elif ty == 'enum' and definition.get('values'):
                if text.casefold() not in [str(v).casefold() for v in definition['values']]:
                    errors.append(f'{where}: {item.key}: expected one of {definition["values"]}')
            elif ty == 'multiselect':
                values = [value.strip() for value in text.split(',')]
                if len(values) != len(set(values)) or not set(values).issubset(definition['values']):
                    errors.append(f'{where}: {item.key}: invalid or repeated role selection')
            elif ty == 'integer':
                if not re.fullmatch(r'(0|[1-9][0-9]*)',text):
                    errors.append(f'{where}: {item.key}: expected a nonnegative integer')
                elif int(text) < definition.get('minimum',0):
                    errors.append(f'{where}: {item.key}: below minimum {definition["minimum"]}')
            elif ty == 'decimal':
                try:
                    number = Decimal(text)
                    if not number.is_finite() or number < Decimal(str(definition.get('minimum',0))):
                        raise ValueError('expected a finite nonnegative amount')
                    if 'maximum' in definition and number > Decimal(str(definition['maximum'])):
                        raise ValueError(f'exceeds {definition["maximum"]}')
                    if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?',text):
                        raise ValueError('use digits and a decimal point, without currency symbols or separators')
                    if 'precision' in definition and -number.as_tuple().exponent > definition['precision']:
                        raise ValueError(f'use at most {definition["precision"]} decimal places')
                except (InvalidOperation, ValueError) as error:
                    errors.append(f'{where}: {item.key}: {error}')
            elif ty == 'email' and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',text):
                errors.append(f'{where}: {item.key}: invalid email address')
            elif ty == 'date':
                try:
                    if not re.fullmatch(r'[0-9]{2}/[0-9]{2}/[0-9]{4}',text):
                        raise ValueError()
                    datetime.strptime(text,'%d/%m/%Y')
                except ValueError:
                    errors.append(f'{where}: {item.key}: invalid date; use DD/MM/YYYY')
            pattern = definition.get('pattern')
            if pattern and not definition.get('condition') and not re.fullmatch(pattern,text):
                errors.append(f'{where}: {item.key}: invalid identifier format')

        if not is_partner:
            continue
        match = PARTNER_NAME.fullmatch(source.path.name)
        if not match:
            errors.append(f'{source.path.name}: invalid canonical partner filename')
            continue
        participant_records = [r for r in source.records if r.kind == 'participant' and len(r.path) == 1]
        budget_records = [r for r in source.records if r.kind == 'budget_row' and len(r.path) == 1]
        if len(participant_records) != 1 or len(budget_records) != 1:
            errors.append(f'{source.path.name}: expected exactly one participant and one budget_row record')
            continue
        values = record_values(participant_records[0])
        budget = record_values(budget_records[0])
        number, acronym = match.groups()
        for key, expected, fields in [('participant.number',number,values),
                                      ('organisation.short_name',acronym,values),
                                      ('budget.participant_number',number,budget)]:
            if fields.get(key,TextValue('')).text != expected:
                errors.append(f'{source.path.name}: {key} must match filename value {expected}')
        partners.append((source,values,number))
        for key in ('participant.role','organisation.pic','organisation.legal_name','organisation.country'):
            require(values,key,source.path.name)
        role = values.get('participant.role',TextValue('')).text
        contacts = [r for r in source.records if r.kind == 'main_contact']
        if len(contacts) > 1:
            errors.append(f'{source.path.name}: at most one main_contact record is allowed')
        if role != 'affiliated':
            if not contacts:
                missing(f'{source.path.name}: main_contact record is missing')
            for record in contacts:
                contact = record_values(record)
                for key in ('contact.first_name','contact.last_name','contact.email'):
                    require(contact,key,f'{source.path.name}:{record.line}')
        for record in source.records:
            data = record_values(record)
            if record.kind == 'other_contact' and any(not v.missing for v in data.values()):
                for key in ('contact.first_name','contact.last_name','contact.email'):
                    require(data,key,f'{source.path.name}:{record.line}')
            if record.kind == 'researcher':
                ident_type = data.get('researcher.identifier_type',TextValue('')).text.casefold()
                ident = data.get('researcher.reference_identifier',TextValue(''))
                if ident_type in ('orcid','orcid id') and not ident.missing:
                    if not re.fullmatch(r'[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]',ident.text):
                        errors.append(f'{source.path.name}:{record.line}: invalid ORCID format')
        for kind, rule in SCHEMA['record_limits'].items():
            maximum = rule.get('maximum')
            total = sum(r.kind == kind for r in source.records)
            if maximum is not None and total > maximum:
                errors.append(f'{source.path.name}: {total} {kind} records, maximum {maximum}')
        roles = values.get('participant.project_roles',TextValue('')).text.split(',')
        if 'other' in [v.strip() for v in roles]:
            require(values,'participant.other_role_specification',source.path.name)

    numbers = {number for _,_,number in partners}
    coordinators = [s.path.name for s,v,_ in partners if v.get('participant.role',TextValue('')).text == 'coordinator']
    if len(coordinators) != 1:
        errors.append(f'Expected exactly one coordinator; found {len(coordinators)}')
    for source,_,number in partners:
        for item in source.fields:
            if item.key == 'link.participant_number' and not item.value.missing:
                if item.value.text not in numbers or item.value.text == number:
                    errors.append(f'{location(root,item)}: linked participant must be another registered partner')
    for key in ('proposal.acronym','proposal.title','proposal.abstract'):
        require(global_values,key,'Consortium')
    questions = [(s,*q) for s in sources for q in s.questions]
    expected = {q['id'] for q in QUESTIONS['ethics']+QUESTIONS['security']}
    found = [q[1] for q in questions]
    if set(found) != expected:
        errors.append(f'Question catalogue mismatch: missing={sorted(expected-set(found))}; extra={sorted(set(found)-expected)}')
    for key,total in Counter(found).items():
        if total != 1:
            errors.append(f'Duplicate question {key}')
    answers = {}
    for source,key,answer,pages,line in questions:
        answers[key] = answer
        where = f'{source.path.relative_to(root)}:{line}: {key}'
        if answer not in ('yes','no','unanswered'):
            errors.append(f'{where}: answer must be yes, no or unanswered')
        elif answer == 'unanswered':
            missing(f'{where}: not answered')
        if not valid_pages(pages):
            errors.append(f'{where}: invalid Part B page references')
    for q in QUESTIONS['ethics']+QUESTIONS['security']:
        if q.get('parent') and answers.get(q['parent']) == 'no' and answers.get(q['id']) == 'yes':
            warnings.append(f'{q["id"]}: yes while inferred parent {q["parent"]} is no; review the actual Portal condition')
    for key,definition in SCHEMA['fields'].items():
        condition = definition.get('required_if') or {}
        trigger = False
        if condition.get('field'):
            control = global_values.get(condition['field'],TextValue(answers.get(condition['field'],'')))
            trigger = control.text == condition.get('equals')
        elif condition.get('any_question_prefix'):
            trigger = any(k.startswith(condition['any_question_prefix']) and v == 'yes' for k,v in answers.items())
        if trigger:
            require(global_values,key,'Consortium')
    confirmation = global_values.get('ethics.confirmation',TextValue(''))
    if confirmation.text.casefold() not in ('yes','true'):
        missing('Ethics confirmation is not affirmed')
    declarations = [(s,*d) for s in sources for d in s.declarations]
    ids = [item[1] for item in declarations]
    required = {str(i) for i in range(1,11 if funding == 'lump-sum' else 10)}
    if not required.issubset(ids) or set(ids)-{str(i) for i in range(1,11)} or len(ids)!=len(set(ids)):
        errors.append('Declarations must contain unique numbers 1..9, plus 10 for lump-sum funding')
    for source,number,answer,line in declarations:
        if number == '10' and funding == 'standard':
            continue
        if answer.casefold() not in ('yes','no','true','false','unconfirmed','unanswered',''):
            errors.append(f'{source.path.name}:{line}: declaration {number}: invalid confirmation')
        elif answer.casefold() not in ('yes','true'):
            missing(f'{source.path.name}:{line}: declaration {number} is not affirmed')
    return {'funding':funding, 'strict':strict, 'fields_checked':len(all_fields),
            'partners_checked':len(partners), 'questions_checked':len(questions),
            'declarations_checked':len(declarations), 'field_counts':counts,
            'incomplete':incomplete, 'warnings':warnings, 'errors':errors,
            'counting_note':'Normalized TeX text includes spaces and paragraph separators; unresolved commands yield no certified count. Portal counting remains authoritative.',
            'constraint_note':'Limits combine the supplied form reconstruction with explicit current official template refinements; field_counts retain confidence.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--strict',action='store_true')
    parser.add_argument('--json',type=Path)
    parser.add_argument('--funding',choices=('standard','lump-sum'),default=os.environ.get('FUNDING') or 'standard')
    args = parser.parse_args()
    try:
        if args.funding not in ('standard','lump-sum'):
            raise ValueError('FUNDING must be standard or lump-sum')
        report = check(args.root,args.strict,args.funding)
        if args.json:
            args.json.parent.mkdir(parents=True,exist_ok=True)
            args.json.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    except (OSError,ValueError,UnicodeError) as error:
        print(f'Cannot check Part A: {error}',file=sys.stderr)
        return 2
    print(f'Part A: {report["partners_checked"]} partner(s), {report["fields_checked"]} fields, {report["questions_checked"]} questions')
    for item in report['field_counts']:
        used = ('unfinished' if not item['complete'] else
                '?' if item['characters'] is None else item['characters'])
        print(f'  {item["field"]}: {used}/{item["limit"]} characters including spaces')
    for message in report['warnings']:
        print('WARN:',message)
    for message in report['errors']:
        print('FAIL:',message)
    if report['incomplete'] and not args.strict:
        print(f'Draft: {len(report["incomplete"])} incomplete item(s); see JSON report or make strict for details.')
    print(f'{"FAIL" if report["errors"] else "PASS"}: Part A data checks ({len(report["errors"])} errors)')
    return 1 if report['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
