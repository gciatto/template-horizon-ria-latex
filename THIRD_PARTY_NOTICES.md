# Source notices

## European Commission form and guidance

The section structure, table labels and drafting guidance are adapted from the
European Commission's Horizon Europe standard application form, Part B,
version 5.1 of 22 January 2026, supplied by the user.

The original form remains attributed to the European Commission. This
independent LaTeX implementation is not an official Commission publication.
Source links and version details are in `docs/formatting.md`.

## Supplied administrative structure

The Part A field structure, question wording and source-confidence annotations
are adapted from the user-supplied `horizon-part-a-templates(2).zip`. The unchanged
archive is retained as `reference/part-a-structure-source.zip`. The integration
adds shared styling, simpler author files, unified checks and current-form
refinements documented in `docs/part-a.md`.

## Bibliography

The bibliography-formatting policy comes from `erc27.sty` in the user-supplied
`erc27-formagent-master.zip`, originally from
<https://github.com/gciatto/erc27-formagent>. The bibliography contains one real
example entry from that project. Bibliographic data and any proposal
subsequently written with this template retain their existing rights.

## BibTeX style

`he-ria26.bst` is a modified and renamed style from the `plainnat` family.

Copyright 1993–2007 Patrick W. Daly.
Redistributed and modified under the LaTeX Project Public License, version 1
or any later version, as stated in the preserved original file header.

The modifications are identified at the beginning of the file: `@online`
support, year fallback from `date`, compact author names, numeric name/year/title
ordering, and identifier-first entries matching the ERC formatting policy.
The original style is available in
the [natbib distribution](https://ctan.org/pkg/natbib).
The [LPPL text](https://www.latex-project.org/lppl/) governs that derived file.

## Other code

The original project code is distributed under the MIT terms in `LICENSE`.
Those terms do not replace the source-specific rights listed above.
