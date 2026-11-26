"""Workbook structure and safe partner-sheet creation for the Excel workflow."""
from copy import copy, deepcopy
from pathlib import Path
import re

VERSION = 'Horizon RIA budget v1'
SECTIONS = {
    'Staff': ['Category', 'Role', 'Annual cost EUR', 'Person-months', 'Eligible cost EUR'],
    'Subcontracts': ['Description', 'WP / task', 'Eligible cost EUR'],
    'Equipment': ['Description', 'Type', 'Purchase cost EUR', 'Depreciation months', 'Use months', 'Project share', 'Eligible cost EUR'],
    'Purchases': ['Description', 'WP / task', 'Eligible cost EUR'],
    'Travel': ['Description', 'WP / task', 'Trips', 'People', 'Unit cost EUR', 'Eligible cost EUR'],
    'Effort': ['WP', 'Person-months', 'Leader'],
}
BUDGET_CELLS = {
    'personnel_eur': 'C11', 'subcontracting_eur': 'C12',
    'travel_subsistence_eur': 'C13', 'equipment_eur': 'C14',
    'other_goods_works_services_eur': 'C15', 'internally_invoiced_eur': 'C16',
    'financial_support_eur': 'C17', 'transnational_access_eur': 'C18',
    'virtual_access_eur': 'C19', 'pcp_ppi_eur': 'C20',
    'indirect_eur': 'C21', 'total_eligible_eur': 'C22',
    'funding_rate_pct': 'C6', 'maximum_eu_for_eligible_eur': 'C23',
    'requested_eu_eur': 'C24', 'max_grant_amount_eur': 'C25',
    'income_generated_eur': 'C26', 'financial_contributions_eur': 'C27',
    'own_resources_eur': 'C28', 'total_estimated_income_eur': 'C29',
}


def load(path):
    from zipfile import BadZipFile
    if Path(path).suffix.lower() != '.xlsx':
        raise ValueError('Budget workbooks must use the .xlsx format')
    try:
        from openpyxl import load_workbook
    except ImportError as error:
        raise ValueError('Excel budgets require openpyxl; install requirements-budget.txt (see README.md)') from error
    from openpyxl.utils.exceptions import InvalidFileException
    try:
        return load_workbook(path, data_only=False)
    except (BadZipFile, InvalidFileException, KeyError) as error:
        raise ValueError(f'Cannot read budget workbook: {error}') from error


def partners(book):
    sheets = [s for s in book if re.fullmatch(r'partner-[1-9][0-9]*', s.title)]
    if not sheets or set(book.sheetnames) - {s.title for s in sheets} - {'total', 'effort', 'instructions'}:
        raise ValueError('Expected partner-N sheets, total, effort and optional instructions')
    if 'total' not in book or 'effort' not in book or book['total']['A1'].value != VERSION:
        raise ValueError('Use the supplied Horizon RIA budget.xlsx template')
    return sorted(sheets, key=lambda s: int(s.title.split('-')[1]))


def section(sheet, kind):
    from openpyxl.utils.cell import range_boundaries
    names = [name for name in sheet.tables if name.startswith(kind + '_')]
    if len(names) != 1:
        raise ValueError(f'{sheet.title}: expected one {kind} table')
    table = sheet.tables[names[0]]
    left, top, right, bottom = range_boundaries(table.ref)
    headers = [sheet.cell(top, c).value for c in range(left, right + 1)]
    if headers != SECTIONS[kind]:
        raise ValueError(f'{sheet.title}: unexpected columns in {kind}: {headers}')
    return [[sheet.cell(r, c) for c in range(left, right + 1)] for r in range(top + 1, bottom + 1)]


def summary(book):
    """Only the two generated summary sheets are rebuilt; inputs remain untouched."""
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    sheets = partners(book)
    profile = book['total']['C2'].value or 'standard'
    for name in ('total', 'effort'):
        sheet = book[name]
        sheet.delete_rows(1, sheet.max_row)
        sheet['A1'] = VERSION
        sheet['A1'].font = Font(name='Arial', size=15, bold=True)
        sheet.sheet_view.showGridLines = False
    budget = book['total']
    budget['B2'], budget['C2'] = 'Funding profile', profile
    budget['C2'].fill = PatternFill('solid', fgColor='FFF2CC')
    budget['C2'].font = Font(name='Arial', size=11, color='0000FF')
    keys = list(BUDGET_CELLS)
    headings = ['Participant'] + [key.removesuffix('_eur').replace('_', ' ') for key in keys]
    for column, heading in enumerate(headings, 1):
        budget.cell(4, column, heading)
    wps = []
    for sheet in sheets:
        for row in section(sheet, 'Effort'):
            if row[0].value and row[0].value not in wps:
                wps.append(row[0].value)
    effort = book['effort']
    for column, heading in enumerate(['Participant', *wps, 'Total PM'], 1):
        effort.cell(4, column, heading)
    for index, sheet in enumerate(sheets, 5):
        identity = f'=\'{sheet.title}\'!C2&" / "&\'{sheet.title}\'!C3'
        budget.cell(index, 1, identity)
        effort.cell(index, 1, identity)
        for column, key in enumerate(keys, 2):
            address = BUDGET_CELLS[key]
            ref = f"'{sheet.title}'!{address}"
            empty = f'IF(\'{sheet.title}\'!C7="yes",0,"")' if key in (
                'internally_invoiced_eur', 'financial_support_eur',
                'transnational_access_eur', 'virtual_access_eur', 'pcp_ppi_eur') else '""'
            budget.cell(index, column, f'=IF({ref}="",{empty},{ref})')
        effort_rows = {row[0].value: row[1].coordinate for row in section(sheet, 'Effort') if row[0].value}
        for column, wp in enumerate(wps, 2):
            if wp not in effort_rows:
                effort.cell(index, column, '=NA()')
            else:
                ref = f"'{sheet.title}'!{effort_rows[wp]}"
                effort.cell(index, column, f'=IF({ref}="","",{ref})')
        end = get_column_letter(len(wps) + 1)
        effort.cell(index, len(wps) + 2,
                    f'=IF(COUNT(B{index}:{end}{index})={len(wps)},SUM(B{index}:{end}{index}),"")')
    last = 4 + len(sheets)
    for sheet in (budget, effort):
        sheet.cell(last + 1, 1, 'Total')
        for column in range(2, sheet.max_column + 1):
            letter = get_column_letter(column)
            # Funding rates describe participants; they are never added.
            if sheet == budget and keys[column - 2] == 'funding_rate_pct':
                continue
            sheet.cell(last + 1, column,
                       f'=IF(COUNT({letter}5:{letter}{last})={len(sheets)},SUM({letter}5:{letter}{last}),"")')
        sheet.freeze_panes = 'B5'
        sheet.row_dimensions[4].height = 45
        sheet.column_dimensions['A'].width = 24
        for column in range(2, sheet.max_column + 1):
            sheet.column_dimensions[get_column_letter(column)].width = 19
        for row in sheet.iter_rows(min_row=4):
            for cell in row:
                cell.font = Font(name='Arial', size=11, bold=cell.row in (4, last + 1))
                cell.alignment = Alignment(vertical='center', wrap_text=cell.row == 4)
                if cell.row == 4:
                    cell.fill = PatternFill('solid', fgColor='243746')
                    cell.font = Font(name='Arial', size=11, bold=True, color='FFFFFF')
                elif cell.column > 1:
                    cell.number_format = '#,##0.00' if sheet == budget else '0.##'
    from openpyxl.workbook.properties import CalcProperties
    book.calculation = CalcProperties(fullCalcOnLoad=True)


def with_partner(path, number, acronym):
    """Prepare an updated workbook in memory, using only the pristine scaffold."""
    from openpyxl.worksheet.table import Table
    book = load(path)
    partners(book)
    title = f'partner-{number}'
    if title in book:
        raise ValueError(f'{title} already exists in the budget workbook')
    pristine = load(Path(__file__).resolve().parent / 'data/budget-template.xlsx')
    source = pristine['partner-1']
    target = book.create_sheet(title)
    for row in source:
        for cell in row:
            new = target.cell(cell.row, cell.column, cell.value)
            new.number_format = cell.number_format
            # Style IDs are local to each workbook.
            new.font, new.fill, new.border = copy(cell.font), copy(cell.fill), copy(cell.border)
            new.alignment, new.protection = copy(cell.alignment), copy(cell.protection)
    for merged in source.merged_cells.ranges:
        target.merge_cells(str(merged))
    for key, dimension in source.column_dimensions.items():
        target.column_dimensions[key] = copy(dimension)
    for key, dimension in source.row_dimensions.items():
        target.row_dimensions[key] = copy(dimension)
    target.data_validations = deepcopy(source.data_validations)
    target.freeze_panes = source.freeze_panes
    target.sheet_view.showGridLines = False
    mapping = {name: name.rsplit('_', 1)[0] + '_' + str(number) for name in source.tables}
    for name, new_name in mapping.items():
        table = source.tables[name]
        new = Table(displayName=new_name, ref=table.ref)
        new.tableStyleInfo = deepcopy(table.tableStyleInfo)
        target.add_table(new)
    for row in target:
        for cell in row:
            if cell.data_type == 'f':
                for name, new_name in mapping.items():
                    cell.value = cell.value.replace(name + '[', new_name + '[')
    target['C2'], target['C3'] = number, acronym.upper()
    if book['total']['C2'].value == 'lump-sum':
        target['C21'] = None
        target['C21']._style = copy(target['C16']._style)
    # Copy the project WP identifiers, never another partner's allocations.
    wps = [row[0].value for row in section(partners(book)[0], 'Effort')]
    rows = section(target, 'Effort')
    top, left = rows[0][0].row, rows[0][0].column
    for row in rows:
        for cell in row:
            cell.value = None
    for index, wp in enumerate(wps):
        for offset in range(3):
            cell = target.cell(top + index, left + offset)
            cell._style = copy(target.cell(top, left + offset)._style)
            cell.value = wp if offset == 0 else None
    from openpyxl.utils import get_column_letter
    target.tables[f'Effort_{number}'].ref = f'{get_column_letter(left)}{top-1}:{get_column_letter(left+2)}{top+len(wps)-1}'
    leader_column = get_column_letter(left + 2)
    for validation in target.data_validations.dataValidation:
        if str(validation.sqref) == f'{leader_column}{top}:{leader_column}{rows[-1][0].row}':
            validation.sqref = f'{leader_column}{top}:{leader_column}{top+len(wps)-1}'
    summary(book)
    return book


def main():
    import argparse
    import tempfile
    parser = argparse.ArgumentParser(description='Refresh budget/effort summaries after editing WP tables.')
    parser.add_argument('workbook', type=Path)
    args = parser.parse_args()
    temporary = None
    try:
        book = load(args.workbook)
        summary(book)
        with tempfile.NamedTemporaryFile(dir=args.workbook.parent, suffix='.xlsx', delete=False) as handle:
            temporary = Path(handle.name)
        book.save(temporary)
        temporary.replace(args.workbook)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)
    print(f'Updated total and effort in {args.workbook}')


if __name__ == '__main__':
    main()
