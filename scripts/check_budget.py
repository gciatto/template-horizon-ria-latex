#!/usr/bin/env python3
"""Check per-partner budget arithmetic without changing editable TeX sources."""
from __future__ import annotations

import argparse
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
import os
from pathlib import Path
import re
import sys

from admin_data import ROOT, SCHEMA, TextValue, metadata_macros, read_manifest, read_source

CENT = Decimal('0.01')
ZERO = Decimal('0.00')
INPUTS = ('personnel_eur','subcontracting_eur','travel_subsistence_eur',
          'equipment_eur','other_goods_works_services_eur','internally_invoiced_eur')
EXTRA_INPUTS = ('financial_support_eur','transnational_access_eur','virtual_access_eur','pcp_ppi_eur')
INDIRECT_BASE = ('personnel_eur','travel_subsistence_eur','equipment_eur','other_goods_works_services_eur')
INCOME = ('income_generated_eur','financial_contributions_eur','own_resources_eur')
MONEY = tuple(k.removeprefix('budget.') for k in SCHEMA['fields']
              if k.startswith('budget.') and k.endswith('_eur'))


def amount(text: str, rate=False) -> Decimal:
    try:
        value = Decimal(text)
        if not value.is_finite() or value < ZERO:
            raise ValueError('must be finite and nonnegative')
        if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?',text):
            raise ValueError('use digits and a decimal point, without separators or currency symbols')
        if not rate and -value.as_tuple().exponent > 2:
            raise ValueError('must have at most two decimal places')
        if rate and value > 100:
            raise ValueError('funding rate must be between 0 and 100')
        return value
    except InvalidOperation as error:
        raise ValueError('invalid numeric value') from error


def rounded(value):
    return value.quantize(CENT,rounding=ROUND_HALF_UP)


def check(root=ROOT,strict=False,funding='standard',workbook=None):
    root = Path(root).resolve()
    errors, incomplete, rows = [], [], []
    totals = defaultdict(lambda:ZERO)
    monetary_coverage = defaultdict(int)
    macros = metadata_macros(root)
    excel = None
    if workbook:
        from budget_excel import read_workbook
        excel = read_workbook(workbook, root, funding)
        incomplete.extend(excel['incomplete'])
    excel_rows = {row['file']: row['budget'] for row in excel['rows']} if excel else {}
    for path in read_manifest(root):
        source = read_source(path,macros)
        records = [r for r in source.records if r.kind == 'budget_row' and len(r.path) == 1]
        if len(records) != 1:
            errors.append(f'{path.name}: expected one budget_row record')
            continue
        record = records[0]
        values, seen = {}, set()
        for field in record.fields:
            key = field.key.removeprefix('budget.')
            if key in seen:
                errors.append(f'{path.name}: duplicate budget field {key}')
            seen.add(key)
            if key not in MONEY and key not in ('participant_number','funding_rate_pct'):
                errors.append(f'{path.name}: unknown budget field {key}')
                continue
            if field.value.missing or key == 'participant_number':
                continue
            if field.value.unknown_commands:
                errors.append(f'{path.name}: {key}: unresolved commands in numeric value')
                continue
            try:
                values[key] = amount(field.value.text,rate=key == 'funding_rate_pct')
            except ValueError as error:
                errors.append(f'{path.name}: {key}: {error}')
        source_values = values if excel else {}
        if excel:
            imported = {key: Decimal(value) for key,value in
                        excel_rows[path.relative_to(root).as_posix()].items()}
            values = imported
        computed = {}
        # Older TeX-only budgets cover six categories. Once an extended category
        # is used, require all four so a missing cost cannot disappear into zero.
        inputs = INPUTS + EXTRA_INPUTS if any(key in values for key in EXTRA_INPUTS) else INPUTS
        missing = [key for key in inputs if key not in values]
        if funding == 'standard' and 'funding_rate_pct' not in values:
            missing.append('funding_rate_pct')
        if funding == 'lump-sum' and 'indirect_eur' not in values:
            missing.append('indirect_eur')
        if missing:
            incomplete.append(f'{path.name}: missing budget inputs: {", ".join(missing)}')
        if funding == 'standard' and all(key in values for key in inputs):
            computed['indirect_eur'] = rounded(sum((values[key] for key in INDIRECT_BASE),ZERO)*Decimal('0.25'))
            computed['total_eligible_eur'] = sum((values[key] for key in inputs),computed['indirect_eur'])
            if 'funding_rate_pct' in values:
                computed['maximum_eu_for_eligible_eur'] = rounded(computed['total_eligible_eur']*values['funding_rate_pct']/100)
        elif funding == 'lump-sum' and all(key in values for key in (*inputs,'indirect_eur')):
            # Estimated costs may be checked for addition, but this checker does
            # not turn them into a lump-sum reimbursement or WP payment amount.
            computed['total_eligible_eur'] = sum((values[key] for key in inputs),values['indirect_eur'])
        for key,expected in computed.items():
            if key in values and values[key] != expected:
                errors.append(f'{path.name}: {key}: entered {values[key]:.2f}, calculated {expected:.2f}')
        effective = {**values,**computed}
        requested = values.get('requested_eu_eur')
        if requested is None:
            incomplete.append(f'{path.name}: requested_eu_eur is not completed')
        if requested is not None:
            if funding == 'standard' and 'maximum_eu_for_eligible_eur' in effective and requested > effective['maximum_eu_for_eligible_eur']:
                errors.append(f'{path.name}: requested EU contribution exceeds calculated eligible-cost maximum')
            if 'max_grant_amount_eur' in values and requested > values['max_grant_amount_eur']:
                errors.append(f'{path.name}: requested EU contribution exceeds entered maximum grant amount')
            if all(key in values for key in INCOME):
                expected_income = sum((values[key] for key in INCOME),requested)
                computed['total_estimated_income_eur'] = expected_income
                effective['total_estimated_income_eur'] = expected_income
                if 'total_estimated_income_eur' in values and values['total_estimated_income_eur'] != expected_income:
                    errors.append(f'{path.name}: total_estimated_income_eur: entered {values["total_estimated_income_eur"]:.2f}, calculated {expected_income:.2f}')
            else:
                incomplete.append(f'{path.name}: income sources are incomplete; enter 0 explicitly where appropriate')
        for key,value in source_values.items():
            if effective.get(key) != value:
                errors.append(f'{path.name}: {key} conflicts with Excel; clear the TeX budget value or reconcile it')
        for key in MONEY:
            if key in effective:
                totals[key] += effective[key]
                monetary_coverage[key] += 1
        rows.append({'file':str(path.relative_to(root)),
                     'entered':{key:format(value,'f') for key,value in values.items()},
                     'calculated':{key:format(value,'.2f') for key,value in computed.items()},
                     'missing_inputs':missing})
    if strict:
        errors.extend(incomplete)
    return {'funding':funding,'strict':strict,'rows':rows,
            **({'excel':excel} if excel else {}),
            'totals':{key:format(value,'.2f') for key,value in totals.items()},
            'totals_rows_included':dict(monetary_coverage),
            'incomplete':incomplete,'errors':errors,
            'note':('Standard RIA arithmetic for the cost categories in this template: indirect costs are 25% of personnel plus purchase costs; subcontracting and internally invoiced costs are excluded. Call-specific exceptions require adaptation.'
                    if funding=='standard' else 'Lump-sum drafting estimate: only entered numeric values and applicable additions are checked. The standard indirect-cost/reimbursement formula and work-package payment model are not inferred.'),
            'totals_note':'Totals cover the populated/calculated rows indicated for each monetary column. Funding rates are never summed.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--strict',action='store_true')
    parser.add_argument('--funding',choices=('standard','lump-sum'),default=os.environ.get('FUNDING') or 'standard')
    parser.add_argument('--json',type=Path)
    parser.add_argument('--workbook',type=Path)
    args=parser.parse_args()
    try:
        if args.funding not in ('standard','lump-sum'):
            raise ValueError('FUNDING must be standard or lump-sum')
        workbook = args.workbook or os.environ.get('BUDGET_XLSX',
            str(args.root/'budget.xlsx') if (args.root/'budget.xlsx').exists() else '')
        report=check(args.root,args.strict,args.funding,workbook or None)
        if args.json:
            args.json.parent.mkdir(parents=True,exist_ok=True)
            args.json.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    except (OSError,ValueError,UnicodeError,InvalidOperation) as error:
        print(f'Cannot check budget: {error}',file=sys.stderr)
        return 2
    print(f'Budget: {len(report["rows"])} partner(s), {report["funding"]} profile')
    print(report['note'])
    for row in report['rows']:
        if row['calculated']:
            print(f'  {row["file"]}: '+', '.join(f'{key}={value}' for key,value in row['calculated'].items()))
    if report['totals']:
        print('Consortium monetary totals (populated or calculated rows only):')
        for key,value in report['totals'].items():
            count=report['totals_rows_included'][key]
            print(f'  {key}: EUR {value} ({count} row(s))')
    for message in report['errors']:
        print('FAIL:',message)
    if report['incomplete'] and not args.strict:
        print(f'Draft: {len(report["incomplete"])} incomplete budget item(s); see JSON report or make strict for details.')
    print(f'{"FAIL" if report["errors"] else "PASS"}: budget checks ({len(report["errors"])} errors)')
    return 1 if report['errors'] else 0


if __name__=='__main__':
    raise SystemExit(main())
