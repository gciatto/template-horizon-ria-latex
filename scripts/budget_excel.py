#!/usr/bin/env python3
"""Read detailed Excel budgets and generate checked LaTeX without formula caches."""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import re
import sys

from admin_data import ROOT, PARTNER_NAME, read_manifest
from check_budget import INPUTS, EXTRA_INPUTS, MONEY, amount, rounded
from budget_workbook import BUDGET_CELLS, VERSION, SECTIONS, load, partners, section


def number(cell, *, money=True, rate=False):
    value = cell.value
    if value is None or value == '':
        return None
    if cell.data_type == 'f':
        raise ValueError(f'{cell.parent.title}!{cell.coordinate}: enter a literal input number, not a formula')
    try:
        text = str(value)
        if money:
            return amount(text, rate=rate)
        if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?', text):
            raise ValueError('expected finite nonnegative person-months or quantity')
        return Decimal(text)
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f'{cell.parent.title}!{cell.coordinate}: {error}') from error


def total(values):
    return sum((Decimal(value) for value in values), Decimal(0)) if all(value is not None for value in values) else None


def read_workbook(path, root=ROOT, funding='standard'):
    root = Path(root).resolve()
    path = Path(path)
    if not path.is_absolute():
        path = root / path
    book = load(path)
    sheets = partners(book)
    if book['total']['C2'].value != funding:
        raise ValueError('Workbook funding profile (total!C2) must match FUNDING')
    manifest = {PARTNER_NAME.fullmatch(p.name).groups(): p for p in read_manifest(root)}
    rows, identities, wps, leaders, incomplete = [], set(), None, {}, []
    for sheet in sheets:
        name = sheet.title
        if sheet['A1'].value != VERSION:
            raise ValueError(f'{name}: unexpected partner sheet format')
        if {table.rsplit('_', 1)[0] for table in sheet.tables} != set(SECTIONS):
            raise ValueError(f'{name}: unexpected detail table; keep the six named sections')
        identity = (str(sheet['C2'].value), str(sheet['C3'].value).strip())
        if (identity not in manifest or identity in identities or
                name != 'partner-' + identity[0]):
            raise ValueError(f'{name}: duplicate identity or partner not in manifest: {identity}')
        identities.add(identity)
        complete = str(sheet['C7'].value or '').lower()
        if complete not in ('', 'yes', 'no'):
            raise ValueError(f'{name}!C7: completed details must be yes, no or blank')
        if complete != 'yes':
            incomplete.append(f'{name}: detailed costs are not confirmed complete (C7)')
        effort = {}
        for row in section(sheet, 'Effort'):
            wp = row[0].value
            if not isinstance(wp, str) or not re.fullmatch(r'WP[1-9][0-9]*', wp) or wp in effort:
                raise ValueError(f'{name}!{row[0].coordinate}: expected a unique WP identifier')
            value = number(row[1], money=False)
            effort[wp] = None if value is None else format(value, 'f')
            leader = str(row[2].value or '').lower()
            if leader not in ('', 'yes', 'no'):
                raise ValueError(f'{name}!{row[2].coordinate}: leader must be yes, no or blank')
            if leader == 'yes':
                if wp in leaders:
                    raise ValueError(f'{wp}: multiple work-package leaders')
                leaders[wp] = identity[0]
        if not effort or (wps is not None and set(wps) != set(effort)):
            raise ValueError(f'{name}: work packages must match every partner sheet')
        wps = list(effort) if wps is None else wps
        budget, subtotals, staff_pm = {}, {}, []
        for kind in ('Staff', 'Subcontracts', 'Equipment', 'Purchases', 'Travel'):
            costs = []
            for row in section(sheet, kind):
                # Labels in the staff category column do not make an unused row active.
                inputs = row[1:-1] if kind == 'Staff' else row[:-1] if kind in ('Equipment', 'Travel') else row
                if not any(cell.value is not None and cell.value != '' for cell in inputs):
                    continue
                if kind == 'Staff':
                    if row[0].value not in ('Permanent', 'Hired', 'Seconded'):
                        raise ValueError(f'{name}!{row[0].coordinate}: invalid staff category')
                    values = [number(row[2]), number(row[3], money=False)]
                    staff_pm.append(values[1])
                    cost = None if None in values else rounded(values[0] / 12 * values[1])
                elif kind == 'Equipment':
                    values = [number(row[2]), number(row[3], money=False), number(row[4], money=False), number(row[5], money=False)]
                    if values[3] is not None and values[3] > 1:
                        raise ValueError(f'{name}!{row[5].coordinate}: project share must be between 0 and 1')
                    if values[1] == 0:
                        raise ValueError(f'{name}!{row[3].coordinate}: depreciation months must be positive')
                    cost = None if None in values else rounded(values[0] * min(values[2], values[1]) / values[1] * values[3])
                elif kind == 'Travel':
                    values = [number(row[2], money=False), number(row[3], money=False), number(row[4])]
                    cost = None if None in values else rounded(values[0] * values[1] * values[2])
                else:
                    cost = number(row[-1])
                if not row[0].value or (kind in ('Subcontracts', 'Purchases', 'Travel') and not row[1].value):
                    cost = None
                if kind == 'Staff' and not row[1].value:
                    cost = None
                if cost is None:
                    incomplete.append(f'{name}: incomplete {kind} row {row[0].row}')
                costs.append(cost)
            subtotals[kind] = total(costs) if complete == 'yes' else None
        pm = total(list(effort.values()))
        personnel_pm = total(staff_pm)
        if pm is None:
            incomplete.append(f'{name}: missing effort; enter 0 explicitly for unused WPs')
        if pm is not None and personnel_pm is not None and complete == 'yes' and pm != personnel_pm:
            raise ValueError(f'{name}: staff effort {personnel_pm} differs from work-package effort {pm}')
        mapping = {'Staff': 'personnel_eur', 'Subcontracts': 'subcontracting_eur',
                   'Equipment': 'equipment_eur', 'Purchases': 'other_goods_works_services_eur',
                   'Travel': 'travel_subsistence_eur'}
        for kind, key in mapping.items():
            value = subtotals[kind]
            if kind == 'Staff' and pm is None:
                value = None
            if value is not None:
                budget[key] = format(value, '.2f')
        for key in ('internally_invoiced_eur', *EXTRA_INPUTS, 'funding_rate_pct',
                    'requested_eu_eur', 'max_grant_amount_eur', 'income_generated_eur',
                    'financial_contributions_eur', 'own_resources_eur'):
            value = number(sheet[BUDGET_CELLS[key]], rate=key == 'funding_rate_pct')
            if value is None and complete == 'yes' and key in ('internally_invoiced_eur', *EXTRA_INPUTS):
                value = Decimal(0)
            if value is not None:
                budget[key] = format(value, 'f')
        if funding == 'lump-sum':
            value = number(sheet['C21'])
            if value is not None:
                budget['indirect_eur'] = format(value, 'f')
        rows.append({'file': manifest[identity].relative_to(root).as_posix(),
                     'number': identity[0], 'acronym': identity[1], 'sheet': name,
                     'budget': budget, 'effort': effort})
    if identities != set(manifest):
        raise ValueError(f'Workbook partner sheets do not match manifest: missing {sorted(set(manifest) - identities)}')
    for wp in wps or []:
        if wp not in leaders:
            incomplete.append(f'{wp}: work-package leader is not identified')
    return {'file': str(path), 'rows': rows, 'work_packages': wps or [],
            'leaders': leaders, 'incomplete': incomplete}


def tex(value):
    escapes = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$',
               '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    return ''.join(escapes.get(char, char) for char in str(value))


def display(value, money=False):
    if value is None:
        return r'\HEPlaceholder{pending}'
    text = format(Decimal(value), '.2f' if money else 'f')
    return text.rstrip('0').rstrip('.') if not money and '.' in text else text


def table(headers, rows, totals, *, money=False, bold=None):
    """Long tables retain 11bp type, repeated headers and page breaks."""
    count = len(headers) - 1
    width = (180 - 58 - 2 * (count + 1) * 2.2) / count
    columns = '|L{58mm}|' + (f'>{{\\raggedleft\\arraybackslash}}p{{{width - 0.8:.2f}mm}}|' * count)
    heading = ' & '.join(r'\textbf{' + tex(h) + '}' for h in headers) + r' \\ \hline'
    lines = [r'\begingroup\setlength{\tabcolsep}{2.2mm}', r'\begin{longtable}{' + columns + '}',
             r'\hline', heading, r'\endfirsthead', r'\hline', heading, r'\endhead']
    for index, row in enumerate(rows):
        values = [tex(row[0])]
        for column, value in enumerate(row[1:]):
            rendered = display(value, money)
            values.append(r'\textbf{' + rendered + '}' if bold and (index, column) in bold else rendered)
        lines.append(' & '.join(values) + r' \\ \hline')
    lines.append(r'\textbf{Total} & ' + ' & '.join(display(value, money) for value in totals) + r' \\ \hline')
    lines.extend([r'\end{longtable}', r'\endgroup', ''])
    return '\n'.join(lines)


def generate(root, workbook, directory, funding='standard'):
    from check_budget import check
    report = check(root, funding=funding, workbook=workbook)
    if report['errors']:
        raise ValueError('\n'.join(report['errors']))
    data = report['excel']
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    effective = [{**row['entered'], **row['calculated']} for row in report['rows']]
    fields = ['% Generated from Excel; do not edit.']
    for row, values in zip(data['rows'], effective):
        for key in (*MONEY, 'funding_rate_pct'):
            value = values.get(key, '')
            if value and key in MONEY:
                value = format(Decimal(value), '.2f')
            fields.append(r'\HEExcelBudgetField{' + row['number'] + '}{' + key + '}{' + value + '}')
    (directory / 'fields.tex').write_text('\n'.join(fields) + '\n', encoding='utf-8')
    budget = ['% Generated from Excel; do not edit.']
    groups = [(('personnel_eur', 'Personnel'), ('subcontracting_eur', 'Subcontracting'),
               ('travel_subsistence_eur', 'Travel')),
              (('equipment_eur', 'Equipment'), ('other_goods_works_services_eur', 'Other purchases'),
               ('internally_invoiced_eur', 'Internal invoices')),
              (('financial_support_eur', 'Third-party support'), ('transnational_access_eur', 'Transnational access'),
               ('virtual_access_eur', 'Virtual access'), ('pcp_ppi_eur', 'PCP/PPI')),
              (('indirect_eur', 'Indirect'), ('total_eligible_eur', 'Total eligible'), ('requested_eu_eur', 'Requested EU'))]
    for group in groups:
        keys, labels = zip(*group)
        rows = [[row['number'] + ' / ' + row['acronym'], *(values.get(key) for key in keys)]
                for row, values in zip(data['rows'], effective)]
        budget.append(table(['Participant / EUR', *labels], rows,
                            [total([values.get(key) for values in effective]) for key in keys], money=True))
    (directory / 'overall-budget.tex').write_text('\n'.join(budget), encoding='utf-8')
    effort = ['% Generated from Excel; do not edit.']
    wps = data['work_packages']
    # Four WP columns per panel keep ordinary table text at its required 11bp.
    for start in range(0, len(wps), 4):
        panel = wps[start:start + 4]
        rows, bold = [], set()
        for index, row in enumerate(data['rows']):
            rows.append([row['number'] + ' / ' + row['acronym'],
                         *(row['effort'][wp] for wp in panel), total(list(row['effort'].values()))])
            bold.update((index, column) for column, wp in enumerate(panel) if data['leaders'].get(wp) == row['number'])
        totals = [total([row['effort'][wp] for row in data['rows']]) for wp in panel]
        totals.append(total([total(list(row['effort'].values())) for row in data['rows']]))
        effort.append(table(['Participant', *panel, 'Total PM'], rows, totals, bold=bold))
    (directory / 'staff-effort.tex').write_text('\n'.join(effort), encoding='utf-8')
    (directory / 'checks.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workbook', type=Path)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/excel-budget')
    parser.add_argument('--funding', choices=('standard', 'lump-sum'), default=os.environ.get('FUNDING') or 'standard')
    args = parser.parse_args()
    try:
        report = generate(args.root.resolve(), args.workbook, args.output, args.funding)
    except (OSError, ValueError, InvalidOperation) as error:
        print(f'Cannot generate Excel budget: {error}', file=sys.stderr)
        return 2
    print(f'Generated budget and effort for {len(report["rows"])} partner(s) in {args.output}')
    if report['incomplete']:
        print(f'Draft: {len(report["incomplete"])} incomplete item(s); see checks.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
