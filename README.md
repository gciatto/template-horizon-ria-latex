# Horizon Europe RIA 2026 LaTeX template

One project for **Part A administrative drafting and Part B technical writing**.
Both parts share metadata, partner data, typography, guidance controls and build
commands. Part B follows the supplied EC V5.1 form of 22 January 2026.

**For ordinary proposal work, edit `.tex` and `.bib` files only.** Styles and
scripts handle layout, repeated inclusion, field checks and releases. There is
no schema-generation step. The Part A PDF is a coordination document: enter its
values into the Funding & Tenders Portal, which generates the submitted Part A.

## Start

Install the tools once on Ubuntu/Debian:

```sh
sudo apt-get update
sudo apt-get install --no-install-recommends \
  make python3 latexmk poppler-utils \
  texlive-latex-base texlive-latex-recommended texlive-latex-extra \
  texlive-fonts-recommended
```

TeX Live or MacTeX with the same packages also works. The engine is pdfLaTeX,
with BibTeX for references; the Python scripts use the standard library.

1. Edit the common project values in `metadata.tex`.
2. Fill `part-a-consortium.tex`, the files in `partners/` and `ethics/`.
3. Write Part B in `sections/` and `tables/`, and add sources to `bibliography.bib`.
4. Run `make` and `make check`.

```sh
make                 # Build Part A and Part B, with and without guidance
make check           # Check field values, budgets and both clean PDFs
make a               # Build only Part A, in both modes
make b2              # Build only Part B, in both modes
make pages           # Count pages in both clean PDFs
make chars           # Report text statistics and field-length checks
make strict          # Also require complete administrative data
make test            # Run regression tests
make ci              # Run all CI checks with individual logs and a summary
make dist            # Validate and create dated release assets
```

`make check` accepts unfinished fields and reports them as drafting reminders.
It fails on invalid populated data or inconsistent arithmetic. `make strict`
also fails on missing required information; the blank template is expected to
fail that completeness check. CI runs the build, draft checks and regression tests,
so the reusable blank template builds successfully.

## Outputs

| PDF | Purpose |
| --- | --- |
| `build/guidance/part-a-guidance.pdf` | Administrative forms with blue author guidance |
| `build/submission/part-a.pdf` | Administrative drafting copy without guidance |
| `build/guidance/part-b2-guidance.pdf` | Technical description with blue author guidance |
| `build/submission/part-b2.pdf` | Technical description without guidance |

Guidance removal preserves authored text and visible unfinished placeholders.
Each document and mode has separate auxiliary files. Reports in `build/`
record administrative fields, budgets, page sizes, page counts and text counts.

## Files to edit

| File | Content |
| --- | --- |
| `metadata.tex` | Project title, acronym, call/topic, coordinator, duration, keywords and direct-compilation defaults |
| `part-a-consortium.tex` | General information, abstract and declarations |
| `partners/partner-N-ACRO-admin-form.tex` | One organisation's administrative information **and its budget** |
| `partners/participants.tex` | Ordered list of partner files |
| `ethics/ethics-questions.tex` | Ethics answers, Part B page references and explanatory fields |
| `ethics/ethics-self-assessment.tex` | Ethics narratives |
| `ethics/security-questions.tex` | Security answers and explanatory fields |
| `ethics/security-self-assessment.tex` | Security narrative |
| `part-a-other.tex` | Call-specific administrative questions |
| `sections/`, `tables/` | Part B content, impact canvas and implementation tables 3.1a–3.1h |
| `bibliography.bib` | Bibliographic entries; initially one example |

`part-a.tex` and `part-b2.tex` assemble the documents. The other `part-a-*.tex`
assembly files call presentation helpers; ordinary data entry does not require
changing them. The style and automation live in `he-ria26.sty`, `he-admin26.sty`,
`he-ria26.bst`, `scripts/`, `Makefile` and the GitHub workflow. `AGENTS.md`
provides instructions for agents working in the project.

### Entering administrative information

Each field has a stable name and an editable value:

```tex
\AField{department.name}{Department of Computer Science}
\AField{budget.personnel_eur}{120000.00}
```

Leave an unknown value empty: `\AField{contact.email}{}`. Use `yes`, `no` or
`unanswered` for question answers, and `unconfirmed` for declarations awaiting
confirmation. The source files show where each answer belongs. Long text can
span ordinary source lines and paragraphs inside the value braces.

Repeat a complete `ARecord` environment for another department, researcher,
achievement or previous project. The checks apply limits to each record and
partner separately. Known field lengths, value choices, counting conventions
and evidence are documented in [docs/part-a.md](docs/part-a.md).

### Partners and budgets

The filename convention is `partners/partner-N-ACRO-admin-form.tex`, with an
unpadded positive participant number and an uppercase acronym. The initial
partner is `partner-1-UNIBO-admin-form.tex`; its substantive information is blank.

To create another blank partner and update the manifest:

```sh
python3 scripts/add_partner.py 2 CNRS
```

The helper starts from a pristine scaffold. It does not copy another partner's
completed contacts, achievements or budget. You may also copy the blank partner
structure manually, update its number/acronym/role and add one `\input{...}` line
to `partners/participants.tex` in participant-number order.

The same partner sources feed Part A, the budget section and Part B's participant
list. Shared proposal fields use `metadata.tex` macros. The coordinator's legal
name is supplied through `\HECoordinator` in that metadata file.

Enter EUR amounts as decimals without currency symbols or thousands separators,
for example `120000.00`. Enter a funding rate as `100`, rather than `100%`.
Use `0.00` for a known zero and an empty value for an unknown amount. Budget
checks compute expected totals and compare any supplied calculated fields.
They retain incomplete rows as incomplete rather than treating blanks as zero.

## Guidance and references

```tex
\begin{heguidance}
Instructions for the author, visible only in guidance mode.
\end{heguidance}

This proposal text appears in both modes.
\HEParagraph{Approach}
Write the approach here, citing \cite{SumersYNG2024}.
```

Use ordinary LaTeX headings, labels and cross-references. `\HEPlaceholder{...}`
marks an unfinished field that remains visible in both modes. The optional
landscape impact canvas is controlled by `\HEImpactSummarytrue` or
`\HEImpactSummaryfalse` in `metadata.tex`.

References retain the ERC formatting policy: numeric name/year/title ordering,
initialled given names, at most two authors, otherwise the first author and
“et al.”; compact author/title/year entries with DOI, otherwise arXiv, otherwise
URL. Full publication details print when none of those identifiers exists.
Only cited entries print. Replace the one example in `bibliography.bib` with
your proposal's sources.

## Funding and limits

Unset or empty `FUNDING` means **standard RIA**. This applies to Make and to
`scripts/build.py`. An explicit override applies consistently to both parts,
checks and PDF metadata:

```sh
make check FUNDING=lump-sum              # Lump-sum profile
make check FUNDING=standard              # Standard RIA profile
make check FUNDING=standard PAGE_LIMIT=35 # Example call-specific Part B cap
```

Part B defaults to **40 pages**, or **45 for lump-sum**. Every Part B page counts,
including title, participant list, figures, tables, landscape pages and references.
`PAGE_LIMIT` overrides Part B only. Part A has field constraints and **no inherited
Part B page cap**. Its footer therefore shows its page number without a 40/45 limit.

The standard budget checker uses the ordinary cost categories represented in the
supplied administrative stub. Lump-sum mode retains numeric/total checks without
applying the standard reimbursement formula as if it defined the lump-sum award.
Call-specific categories and conditions belong in the actual Portal form.

PDF character statistics are diagnostic. Administrative field checks count
normalised text, including spaces and paragraph breaks, resolve shared metadata
macros, and flag unsupported LaTeX commands when a reliable count is unavailable.
For literal Portal text, count a UTF-8 file directly:

```sh
python3 scripts/count_chars.py abstract.txt --limit 2000
```

## Direct compilation and Overleaf

Select `part-a.tex` or `part-b2.tex` as the main document and choose pdfLaTeX.
No Python generation step is needed to compile either source. Direct compilation
shows guidance. Hide it with `[part-a,final]` in Part A's `he-ria26` package options,
or `[final]` in Part B. Direct compilation takes the funding fallback from
`metadata.tex`; the supplied fallback is `standard`.

## Releases and generated files

```sh
make dist
make dist VERSION=2026.11.25-12-30
```

Versions use **`YYYY.MM.DD-hh-mm`**, in 24-hour UTC, without a `v` prefix.
A release contains the source ZIP, all four PDFs, validation reports and SHA-256
hashes. GitHub Actions runs on pushes to every branch, pull requests and manual
runs. Its behaviour is:

| Run | Build and validate | PDF/log artifacts | Dated GitHub release |
| --- | --- | --- | --- |
| Push or manual run on `master` | Yes | Yes | After all checks pass |
| Push or manual run on any other branch | Yes | Yes | No |
| Pull request | Yes | Yes | No |

Each run summary shows the status and duration of the four PDF builds,
administrative and budget checks, both clean-PDF checks and regression tests.
It also reports page counts and unfinished-field totals, links to downloadable
PDFs/logs, and includes expandable excerpts for failed checks. Independent checks
continue after failures; checks needing a failed compilation are marked skipped.
Failures still fail the job and prevent a release.

The logs artifact retains command output, LaTeX/BibTeX logs and JSON reports,
including on failed runs. Artifacts are kept for 30 days. Existing releases are
preserved when a minute-based version collides. Only the release job has write
permission, and it is restricted to `master`.

Run `make ci` locally to use the same check runner. Its report is
`build/ci/summary.md`, with structured results in `build/ci/results.json` and
one log per check. CI creates release packages only on `master`; `make dist`
remains available locally to validate and package any checkout.

`.gitignore` excludes build/release directories, generated document PDFs,
LaTeX auxiliary files, Python caches and editor leftovers. Authored figures,
including PDF figures, remain trackable. `make clean` removes build outputs;
`make distclean` also removes release assets.

## Formatting and provenance

Both parts use the same Times-compatible 11 physical-point typography, 15 mm
margins, heading styles, blue guidance and grey footer. Part B preserves the
supplied RTF's form structure and turquoise impact canvas. Its text rectangle
is 180 × 267 mm, with headers and footers outside that rectangle.

[docs/formatting.md](docs/formatting.md) explains the layout and Part B rules.
[docs/part-a.md](docs/part-a.md) explains administrative types and constraints.
[docs/proposal-writing.md](docs/proposal-writing.md) adapts the supplied agent
writing workflow to this project; `AGENTS.md` directs drafting and review agents
to it. The unchanged source RTF, supplied Part A ZIP and original writing
instructions are retained in `reference/`.
See `THIRD_PARTY_NOTICES.md` for attribution. Original code is under the MIT
licence; the derived BibTeX style retains its LPPL terms.
