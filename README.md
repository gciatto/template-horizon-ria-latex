# Horizon Europe RIA 2026 LaTeX template

A working Part B project matching the supplied European Commission
**V5.1 template of 22 January 2026**. It uses the shared-metadata and build
organisation of the supplied ERC project, with Horizon-specific sections,
tables, formatting and page accounting.

## Build

On Ubuntu/Debian, install the tools once:

```sh
sudo apt-get update
sudo apt-get install --no-install-recommends \
  make python3 latexmk poppler-utils \
  texlive-latex-base texlive-latex-recommended texlive-latex-extra \
  texlive-fonts-recommended
```

A normal TeX Live or MacTeX installation with these LaTeX packages also works.
The engine is **pdfLaTeX**, with **BibTeX** for references.

```sh
make                 # Build both PDFs
make check           # Check the full submission PDF's page limit and A4 page sizes
make pages           # Page report
make chars           # Character statistics
make test            # PDF layout and tooling regression tests
```

The two principal outputs are:

- `build/guidance/part-b2-guidance.pdf`: blue drafting guidance alongside the author fields.
- `build/submission/part-b2.pdf`: the same document with guidance removed.

The latter remains a **template** until its bracketed placeholders are filled.
Guidance removal leaves authored content, table labels and visible placeholders
in place. Each build has a separate auxiliary directory, so changing modes
cannot reuse the other mode's bibliography or cross-reference state.

## Edit

| File | Purpose |
| --- | --- |
| `metadata.tex` | Title, acronym, call/topic, coordinator, participants, funding profile and optional impact summary |
| `he-ria26.sty` | Layout, typography, guidance, headings, canvas and bibliography helpers |
| `part-b2.tex` | Main document; renders the official name “Part B” |
| `sections/` | Participant list, the three evaluation sections and the impact canvas |
| `tables/` | Editable implementation tables 3.1a–3.1h |
| `bibliography.bib` | One real example reference, ready to replace |
| `he-ria26.bst` | The ERC project's compact numeric bibliography formatting, implemented with BibTeX |
| `scripts/` | Build, page/character counts and dated source archives |
| `.github/workflows/build.yml` | Continuous validation and dated releases |
| `docs/formatting.md` | Rules, precise layout choices and source provenance |
| `reference/` | Unchanged supplied RTF |

Edit `metadata.tex` first, then replace the placeholders in `sections/` and
`tables/`. The participant identifiers, work-package identifiers, staff effort
and costs must agree with the values entered into Part A.

Part A drafting support is deliberately left for the next iteration.

### Guidance and author text

```tex
\begin{heguidance}
Instructions for the author: visible only in the guidance PDF.
\end{heguidance}

This is proposal text, visible in both PDFs.

\HEParagraph{Approach}
A compact run-in heading followed by proposal text.
```

Use ordinary `\section`, `\subsection`, `\label` and `\cref` commands.
The official section numbering is already in place. Use `\HEPlaceholder{...}`
for an unfinished field that should remain visible in both modes.

The optional six-panel impact canvas is controlled in `metadata.tex`:

```tex
\HEImpactSummarytrue   % Include section 2.3 and its landscape canvas
% \HEImpactSummaryfalse % Remove section 2.3 entirely
```

### References

```tex
An article: \cite{SumersYNG2024}.
The same reference in parentheses: \citep{SumersYNG2024}.
```

`\HEPrintBibliography` at the end of the main document prints only cited
entries. An empty proposal builds without an empty bibliography. The database
contains one example entry; replace it with sources relevant to the proposal.
The formatting follows the ERC project: numeric references sorted by name,
year and title; family names with given-name initials; at most two authors,
or the first author followed by “et al.” for longer lists. Entries retain
author, title, year and a DOI, otherwise an arXiv identifier, otherwise a URL.
Full publication details are printed when none of those identifiers is present.

### Profiles and limits

Default: a standard full RIA, **40 pages**. Set the default profile in
`metadata.tex`, or select it for a build:

```sh
make check FUNDING=lump-sum              # 45-page full RIA profile
make check FUNDING=standard              # 40-page full RIA profile
make check FUNDING=standard PAGE_LIMIT=35 # Example call-specific override
```

Only set a custom page limit when the actual call's submission template
requires it. The same value is written into the PDF footer and the `.hemeta`
sidecar used by the checking script. A later build without overrides returns
to the defaults in `metadata.tex`.

Every page of Part B counts, including the title, participants, figures,
tables, landscape canvas and references. A failed page check exits nonzero.
The section-specific page suggestions shown in blue are indicative.

Part B has no general character cap. `make chars` reports extracted PDF text
statistics. For an exact future Portal-field check, put the intended plain
text in a UTF-8 file and supply its applicable limit explicitly:

```sh
python3 scripts/count_chars.py my-field.txt --limit 2000
```

This counts Unicode code points, including literal spaces and line breaks;
it does not interpret LaTeX. The number `2000` is only a usage example, not a
declared limit for any field in this project.

## Releases and source archives

```sh
make dist                              # UTC version generated at build time
make dist VERSION=2026.11.25-12-30      # Explicit reproducible version label
```

Versions have the exact form **`YYYY.MM.DD-hh-mm`**, with a 24-hour UTC time
and no `v` prefix. Source archives exclude `.git`, temporary files and build
artefacts. The PDFs are separate release assets.

GitHub Actions builds and checks the template for pull requests and pushes.
Successful builds on the repository's default branch publish a release with
the dated version and downloadable source/PDF assets. Pull requests use a
read-only token. A release-name collision within the same minute never
overwrites an existing release.

## Direct compilation and Overleaf

Set `part-b2.tex` as the main document and select pdfLaTeX. Direct compilation
shows guidance. For a direct compilation without guidance, use
`\usepackage[final]{he-ria26}` in place of `\usepackage{he-ria26}`.
With the Makefile, select `make guidance` or `make submission` instead.

## Formatting

The body and all table text are **11 physical points** in the reference
Times-compatible family. Margins are exactly **15 mm**, giving a
**180 × 267 mm** portrait body rectangle. Single line spacing and standard
character spacing are retained. The supplied RTF already uses the minimum
margins, so savings come from compact spacing and placing the header/footer
outside the body rectangle.

See [the formatting notes](docs/formatting.md) for sources, the current
40/45-page rules and differences from earlier templates.

## Attribution

See `THIRD_PARTY_NOTICES.md` for the European Commission form, the ERC
bibliography-formatting policy and the derived BibTeX style. Original project code is under
the MIT licence. This is an independent template implementation.
