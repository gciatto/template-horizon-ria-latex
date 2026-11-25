#!/usr/bin/env python3
"""Create a blank partner file and register it without copying another partner's data."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

from admin_data import ROOT, DATA, PARTNER_NAME, args_of, read_manifest


def format_name(number,acronym):
    acronym=acronym.upper()
    if number < 1 or not re.fullmatch(r'[A-Z0-9]+(?:-[A-Z0-9]+)*',acronym):
        raise ValueError('Use a positive participant number and an acronym of ASCII letters/digits/internal hyphens')
    return f'partner-{number}-{acronym}-admin-form.tex'


def add_partner(number,acronym,role='partner',root=ROOT):
    if role not in ('coordinator','partner','affiliated'):
        raise ValueError('Role must be coordinator, partner or affiliated')
    root=Path(root).resolve()
    name=format_name(number,acronym)
    partners=root/'partners'
    manifest=partners/'participants.tex'
    existing=read_manifest(root) if manifest.exists() else []
    if not manifest.exists() and list(partners.glob('partner-*.tex')):
        raise ValueError('Register existing partner files in partners/participants.tex first')
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
    line=f'\\input{{partners/{name}}}\n'
    prefix=body[:insertion]
    if prefix and not prefix.endswith('\n'):
        prefix+='\n'
    updated=prefix+line+body[insertion:]
    partners.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding='utf-8')
    try:
        manifest.write_text(updated,encoding='utf-8')
    except OSError:
        path.unlink()  # Only the new file created by this call is rolled back.
        raise
    return path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('number',type=int)
    parser.add_argument('acronym')
    parser.add_argument('--role',choices=('coordinator','partner','affiliated'),default='partner')
    parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args()
    try:
        path=add_partner(args.number,args.acronym,args.role,args.root)
    except (OSError,ValueError) as error:
        parser.error(str(error))
    print(f'Created {path.relative_to(args.root.resolve())}; updated partners/participants.tex')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
