#!/usr/bin/env python3
"""Create a blank partner file and register it without copying another partner's data."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys
import tempfile

from admin_data import ROOT, DATA, PARTNER_NAME, args_of, read_manifest


def format_name(number,acronym):
    acronym=acronym.upper()
    if number < 1 or not re.fullmatch(r'[A-Z0-9]+(?:-[A-Z0-9]+)*',acronym):
        raise ValueError('Use a positive participant number and an acronym of ASCII letters/digits/internal hyphens')
    return f'partner-{number}-{acronym}-admin-form.tex'


def add_partner(number,acronym,role='partner',root=ROOT,workbook=None):
    if role not in ('coordinator','partner','affiliated'):
        raise ValueError('Role must be coordinator, partner or affiliated')
    root=Path(root).resolve()
    name=format_name(number,acronym)
    partners=root/'part-a/partners'
    manifest=partners/'participants.tex'
    existing=read_manifest(root) if manifest.exists() else []
    if not manifest.exists() and list(partners.glob('partner-*.tex')):
        raise ValueError('Register existing partner files in part-a/partners/participants.tex first')
    if any(int(PARTNER_NAME.fullmatch(path.name).group(1))==number for path in existing):
        raise ValueError(f'Participant number {number} is already in use')
    path=partners/name
    if path.exists():
        raise ValueError(f'{path.name} already exists')
    text=(DATA/'partner-admin-form.tex.in').read_text(encoding='utf-8')
    for key,value in {'@@NUMBER@@':str(number),'@@ACRONYM@@':acronym.upper(),'@@ROLE@@':role}.items():
        text=text.replace(key,value)
    body=manifest.read_text(encoding='utf-8') if manifest.exists() else '% Partner list, in participant number order.\n'
    # Preserve comments and user formatting; only insert the additional input.
    insertion=len(body)
    for (target,),start in args_of(body,'input',1):
        found=PARTNER_NAME.fullmatch(Path(target.strip()).name)
        if found and int(found.group(1)) > number:
            insertion=body.rfind('\n',0,start)+1
            break
    line=f'\\input{{part-a/partners/{name}}}\n'
    prefix=body[:insertion]
    if prefix and not prefix.endswith('\n'):
        prefix+='\n'
    updated=prefix+line+body[insertion:]
    if workbook is not None and not Path(workbook).is_file():
        raise ValueError(f'Budget workbook does not exist: {workbook}')
    workbook = Path(workbook) if workbook else root/'budget.xlsx'
    staged = None
    if workbook.exists():
        from budget_workbook import with_partner
        book = with_partner(workbook, number, acronym)
        with tempfile.NamedTemporaryFile(dir=workbook.parent, suffix='.xlsx', delete=False) as handle:
            staged = Path(handle.name)
        try:
            book.save(staged)
        except Exception:
            staged.unlink(missing_ok=True)
            raise
    partners.mkdir(parents=True,exist_ok=True)
    try:
        path.write_text(text,encoding='utf-8')
        manifest.write_text(updated,encoding='utf-8')
        if staged:
            staged.replace(workbook)
    except OSError:
        path.unlink(missing_ok=True)
        manifest.write_text(body,encoding='utf-8')
        raise
    finally:
        if staged:
            staged.unlink(missing_ok=True)
    return path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('number',type=int)
    parser.add_argument('acronym')
    parser.add_argument('--role',choices=('coordinator','partner','affiliated'),default='partner')
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--workbook',type=Path,default=os.environ.get('BUDGET_XLSX') or None)
    args=parser.parse_args()
    try:
        path=add_partner(args.number,args.acronym,args.role,args.root,args.workbook)
    except (OSError,ValueError) as error:
        parser.error(str(error))
    print(f'Created {path.relative_to(args.root.resolve())}; updated part-a/partners/participants.tex')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
