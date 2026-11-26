# Horizon Europe RIA 2026 LaTeX template

One project for **Part A administrative drafting and Part B technical writing**.
Both parts share metadata, partner data, typography, guidance controls and build
commands. Part B implements the EC V5.1 structure of 22 January 2026.

**For ordinary proposal work, edit `.tex`, `.bib`, `metadata.sty` and `budget.xlsx`.** Styles and
scripts handle layout, repeated inclusion, field checks and releases. There is
no schema-generation step. The Part A PDF is a coordination document: enter its
values into the Funding & Tenders Portal, which generates the submitted Part A.

## Template baseline

| Component | Implementation |
| --- | --- |
| Part B appearance and structure | RIA/IA full-proposal **V5.1, 22 January 2026** |
| Part A administrative structure and constraints | `scripts/data/part-a-fields.json` and `scripts/data/part-a-questions.json`; see `docs/part-a.md` |
| Agent proposal-writing workflow | `docs/proposal-writing.md` |

Use the actual topic's Submission System form to resolve call-specific changes;
the shipped baseline supports a full RIA, not every Horizon instrument or stage.

## Start

Install the tools once on Ubuntu/Debian:

```sh
sudo apt-get update
sudo apt-get install --no-install-recommends \
  make python3 python3-openpyxl latexmk poppler-utils \
  texlive-latex-base texlive-latex-recommended texlive-latex-extra \
  texlive-fonts-recommended
```

TeX Live or MacTeX with the same packages also works. The engine is pdfLaTeX,
with BibTeX for references. Excel budgets additionally require `openpyxl`:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-budget.txt
make PYTHON=.venv/bin/python
```

Alternatively install the distribution's `python3-openpyxl` package alongside
Python. The TeX-only workflow uses the Python standard library.
On macOS, use MacTeX together with `make`, Python 3 and Poppler's `pdfinfo` and
`pdftotext` commands. Direct LaTeX compilation needs the TeX packages; the full
Make/check workflow also needs those command-line tools.

1. Edit the common project values in `metadata.sty`.
2. Fill `part-a/part-a-consortium.tex`, the files in `part-a/partners/`, `part-a/ethics/`, and `budget.xlsx`.
3. Write Part B in `part-b/sections/` and `part-b/tables/`, and add sources to `bibliography.bib`.
4. Run `make` and `make check`.

```sh
make                 # Build Part A and Part B, with and without guidance
make check           # Check field values, budgets and both clean PDFs
make a               # Build only Part A, in both modes
make b               # Build only Part B, in both modes
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

Use `make help` for a compact command list. `make part-a` and `make part-b`
are aliases of `make a` and `make b`.

## Outputs

| PDF | Purpose |
| --- | --- |
| `build/guidance/part-a-guidance.pdf` | Administrative forms with blue author guidance |
| `build/submission/part-a.pdf` | Administrative drafting copy without guidance |
| `build/guidance/part-b-guidance.pdf` | Technical description with blue author guidance |
| `build/submission/part-b.pdf` | Technical description without guidance |

Guidance removal preserves authored text and visible unfinished placeholders.
Each document and mode has separate auxiliary files. Reports in `build/`
record administrative fields, budgets, page sizes, page counts and text counts.

To select a mode, use `make guidance` or `make submission`. For one document
and one mode, use `make guidance-a`, `make guidance-b`, `make submission-a` or
`make submission-b`. Changing funding/profile options regenerates the relevant
driver while keeping the other document's bibliography and cross-reference
state separate.

| Report | Content |
| --- | --- |
| `build/admin-checks.json` | Field types, required/unfinished values, character counts and partner consistency |
| `build/budget-checks.json` | Per-partner supplied values, calculated expectations and consortium totals |
| `build/part-a-counts.json` | Part A page sizes, page count and extracted-text statistics |
| `build/counts.json` | Part B page sizes, page count, active page cap and extracted-text statistics |
| `build/ci/summary.md`, `build/ci/results.json` | Human-readable CI summary and individual check results, produced by `make ci` |

## Files to edit

| File | Content |
| --- | --- |
| `metadata.sty` | Project title, acronym, call/topic, coordinator, duration, keywords and direct-compilation defaults |
| `budget.xlsx` | Detailed partner costs and WP effort, with computed Excel summaries |
| `part-a/part-a-consortium.tex` | General information, abstract and declarations |
| `part-a/partners/partner-N-ACRO-admin-form.tex` | One organisation's administrative information **and its budget** |
| `part-a/partners/participants.tex` | Ordered list of partner files |
| `part-a/ethics/ethics-questions.tex` | Ethics answers, Part B page references and explanatory fields |
| `part-a/ethics/ethics-self-assessment.tex` | Ethics narratives |
| `part-a/ethics/security-questions.tex` | Security answers and explanatory fields |
| `part-a/ethics/security-self-assessment.tex` | Security narrative |
| `part-a/part-a-other.tex` | Call-specific administrative questions |
| `part-b/sections/`, `part-b/tables/` | Part B content, impact canvas and implementation tables 3.1a–3.1h |
| `bibliography.bib` | Bibliographic entries; initially one example |

`part-a.tex` and `part-b.tex` are the only root `.tex` files. They load the shared
`metadata.sty` package and assemble the sources under `part-a/` and `part-b/`.
Documentation and build/configuration files also remain at the repository root.
The `part-a/part-a-*.tex` assembly files call presentation helpers;
ordinary data entry does not require
changing them. The style and automation live in `he-ria26.sty`, `he-admin26.sty`,
`he-ria26.bst`, `scripts/`, `Makefile` and the GitHub workflow. `AGENTS.md`
provides instructions for agents working in the project. Markdown documentation
and internal validation schemas are maintainer interfaces; proposal authors
keep their inputs in `.tex`, `.bib`, `metadata.sty` and the Excel budget.

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

Keep field identifiers and record names unchanged. Add text to the value braces,
and use ordinary LaTeX escapes for special characters in prose. Numeric fields
use literal numbers without formatting macros. A new call-specific narrative
question can be written directly in `part-a/part-a-other.tex`; adding a new *typed*
field is a maintainer change that also extends the checker.

### Partners and budgets

The filename convention is `part-a/partners/partner-N-ACRO-admin-form.tex`, with an
unpadded positive participant number and an uppercase acronym. The initial
partner is `partner-1-UNIBO-admin-form.tex`; its substantive information is blank.

To create another blank partner and update the manifest:

```sh
python3 scripts/add_partner.py 2 CNRS
python3 scripts/add_partner.py 3 INSTITUTE --role affiliated
```

The helper starts from a pristine scaffold. It does not copy another partner's
completed contacts, achievements or budget. You may also copy the blank partner
structure manually, update its number/acronym/role and add one `\input{...}` line
to `part-a/partners/participants.tex` in participant-number order.

The same partner sources feed Part A, the budget section and Part B's participant
list. Shared proposal fields use `metadata.sty` macros. The coordinator's legal
name is supplied through `\HECoordinator` in that metadata file.

The helper also adds a pristine sheet to `budget.xlsx` and rebuilds its `total`
and `effort` summaries, including all registered partners. It preserves existing
budget inputs. Use `--workbook path.xlsx` to select another workbook. If the
default workbook is absent, the helper retains its TeX-only behaviour.
Save and close the workbook before running the partner helper or `budget-sync`.

### Detailed Excel budgets

The supplied `budget.xlsx` starts with `partner-1`, `total`, `effort` and
`instructions`. The first sheet matches the initial participant in the TeX
manifest. There is no fixed participant count: add participants with the helper
above, which updates both the TeX manifest and Excel summaries. Its blank Excel
scaffold is maintained under `scripts/data/`; never fill that internal copy.

Each partner fills the yellow inputs for permanent, hired and seconded staff,
subcontracting, equipment depreciation, other purchases, travel and WP effort.
The workbook computes eligible costs and summaries. Set `C7` to `yes` only after
reviewing all cost sections: unused detail rows and blank additional cost
categories then mean confirmed zero. Unconfirmed details remain incomplete.
WP effort requires explicit zeroes. Exactly one participant should identify
itself as each WP's leader. Enter requested EU contributions and income sources
explicitly. The maximum grant field is optional.

```sh
make                   # Read budget.xlsx and build both parts in both modes
make check-budget      # Recompute and validate detailed costs and WP allocations
make budget-tables     # Export standalone tables under build/excel-budget/
make budget-sync       # Refresh Excel summary rows/columns after changing WPs
make BUDGET_XLSX=other.xlsx  # Use another workbook
make BUDGET_XLSX=       # Use TeX-only budgets and the manual effort table
```

Use the same `PYTHON` setting as above for these commands and the partner helper.
No Excel application, macros, shell escape or spreadsheet recalculation command
is needed for the build. Python reads literal inputs, recalculates with decimal
arithmetic, and generates files under `build/`. Compilation does not trust
Excel's saved formula results or rewrite the workbook. Part A receives a
consortium summary and each participant's budget. Part B table 3.1f receives
WP effort and totals, with leaders in bold. Wide effort tables use repeated
panels at the normal font size. Keep table 3.1a's work plan consistent manually.

The partner detail areas are named Excel Tables. Extend them with table rows,
keeping their headers and names. Add the same WP identifiers to every partner's
effort table, then run `make budget-sync`; the next partner inherits those WP
identifiers with empty allocations. Summary sheets are generated views: edit
partner inputs and the funding profile in `total!C2`, not summary formulas.
Partner numbers/acronyms must match the TeX manifest. Country and duration should
agree with the administrative sources and `metadata.sty`.

In Excel mode, leave TeX budget amounts empty. A populated conflicting TeX amount
fails validation. Editable numeric inputs must be literal numbers; formula cells
in the detail areas are calculations. Unknown values produce visible `pending`
placeholders in the generated tables.

For lump-sum estimates, select `lump-sum` in `total!C2`, replace each partner's
`C21` formula with an explicit indirect-cost estimate (or clear it while
drafting), and run with `FUNDING=lump-sum`. Requested contributions remain
explicit inputs. The workflow does not infer lump-sum awards or WP payments.
Verify cost eligibility, rates and extra categories against the actual call.

For the TeX-only workflow, enter EUR amounts as decimals without currency symbols or thousands separators,
for example `120000.00`. Enter a funding rate as `100`, rather than `100%`.
Use `0.00` for a known zero and an empty value for an unknown amount. Budget
checks compute expected totals and compare any supplied calculated fields.
They retain incomplete rows as incomplete rather than treating blanks as zero.
Run `make check-budget` for the budget report and `make check-admin` for the
partner/field report. Their strict variants are included in `make strict`.

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
`\HEImpactSummaryfalse` in `metadata.sty`.

For inline guidance use `\HEGuide{...}`. The template also uses
`\HECriterion{heading}{guidance}` for evaluation boxes and `\HEBudget{...}` for
indicative section allocations. Those drafting allocations do not create
separate hard section limits. Preserve the official Part B headings and
implementation table numbers when replacing their placeholders.

References retain the ERC formatting policy: numeric name/year/title ordering,
initialled given names, at most two authors, otherwise the first author and
“et al.”; compact author/title/year entries with DOI, otherwise arXiv, otherwise
URL. Full publication details print when none of those identifiers exists.
Only cited entries print. Replace the one example in `bibliography.bib` with
your proposal's sources.

The bibliography backend is BibTeX with `natbib` and `he-ria26.bst`.
`\cite{key}`, `\citep{key}` and `\citet{key}` use the same numeric reference
set, printed by `\HEPrintBibliography` at the end of Part B. An uncited
database produces no empty bibliography section.

## Funding and limits

Unset or empty `FUNDING` means **standard RIA**. This applies to Make and to
`scripts/build.py`. An explicit override applies consistently to both parts,
checks and PDF metadata:

```sh
make check FUNDING=lump-sum              # Lump-sum profile
make check FUNDING=standard              # Standard RIA profile
make check FUNDING=standard PAGE_LIMIT=35 # Example call-specific Part B cap
```

For the full-proposal profile, Part B defaults to **40 pages**, or
**45 for lump-sum**. Every Part B page counts,
including title, participant list, figures, tables, landscape pages and references.
`PAGE_LIMIT` overrides Part B only. Part A has field constraints and **no inherited
Part B page cap**. Its footer therefore shows its page number without a 40/45 limit.

An omitted `PAGE_LIMIT` uses the direct-compilation override in `metadata.sty`
when present, otherwise the profile default. Make's `FUNDING` value is explicit:
omitting it returns to `standard`, even if the previous build used lump-sum.
The `FUNDING` switch changes the funding profile, not the action type or stage.

The standard budget checker uses the ordinary cost categories documented in
`docs/part-a.md`. Lump-sum mode retains numeric/total checks without
applying the standard reimbursement formula as if it defined the lump-sum award.
Call-specific categories and conditions belong in the actual Portal form.

PDF character statistics are diagnostic. Administrative field checks count
normalised text, including spaces and paragraph breaks, resolve shared metadata
macros, and flag unsupported LaTeX commands when a reliable count is unavailable.
For literal Portal text, use `scripts/count_chars.py` with the path to your
UTF-8 input and an optional `--limit`.

The literal counter includes spaces and line breaks exactly as present in the
UTF-8 file. It does not expand LaTeX. `make strict` adds known administrative and
budget completeness checks; final review also resolves narrative placeholders,
ethics/security page references and call-specific Portal requirements.

## Typography and paragraph layout

| Setting | Shared implementation |
| --- | --- |
| Paper | A4; the optional Part B impact canvas uses A4 landscape |
| Body margins | Exactly 15 mm; portrait text rectangle **180 × 267 mm** |
| Body and table font | Times-compatible Nimbus Roman, **11 physical points** (`11bp`) |
| Line spacing | Single spacing, **13.2bp** baseline |
| Prose paragraph spacing | **`\parskip=0pt`**: no additional gap between paragraphs |
| First-line indentation | **`\parindent=1em`**, including the first paragraph after headings |
| Draft guidance | Blue and removable; authored content and placeholders remain |
| Running elements | Call/template header and grey footer outside the text rectangle |

The paragraph policy also applies to blue guidance, administrative narrative
answer boxes, `\HEParagraph` and native `\paragraph`/`\subparagraph` headings.
Lists, labels, tables, captions and headings retain their structural spacing.
Space savings come from compact paragraph/layout spacing while retaining the
required text size.

Separate prose paragraphs with a blank source line:

```tex
\HEParagraph{Approach}
The first paragraph starts here. Source lines may wrap normally
without creating another paragraph.

This is the next paragraph. Its first line is indented automatically,
with no additional vertical gap between paragraphs.
```

See [docs/formatting.md](docs/formatting.md) for the exact layout decisions and
their source requirements.

## Direct compilation and Overleaf

Select `part-a.tex` or `part-b.tex` as the main document and choose pdfLaTeX.
No Python generation step is needed to compile either source. Direct compilation
uses TeX-only budgets and the manual effort table; use Make to include Excel data.
Direct compilation
shows guidance. Hide it with `[part-a,final]` in Part A's `he-ria26` package options,
or `[final]` in Part B. Direct compilation takes the funding fallback from
`metadata.sty`; the supplied fallback is `standard`.

For local direct compilation, use `latexmk -pdf part-a.tex` or
`latexmk -pdf part-b.tex`. The supplied `.latexmkrc` selects pdfLaTeX/BibTeX
and disables shell escape. Make remains the entry point for field, budget and
PDF-limit checks.

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

Date versions use the build's UTC minute. Existing tags without a release are
not reused; a new release tag targets the exact commit that was built.
The generated source ZIP excludes `.git`, `build/`, `dist/` and auxiliary files,
and includes a `VERSION` file. PDF assets and validation reports are distributed
separately alongside that source ZIP.

Run `make ci` locally to use the same check runner. Its report is
`build/ci/summary.md`, with structured results in `build/ci/results.json` and
one log per check. CI creates release packages only on `master`; `make dist`
remains available locally to validate and package any checkout.

`.gitignore` excludes build/release directories, generated document PDFs,
LaTeX auxiliary files, Python caches and editor leftovers. Authored figures,
including PDF figures, remain trackable. `make clean` removes build outputs;
`make distclean` also removes release assets.

## Maintainer documentation and licensing

| Document | Purpose |
| --- | --- |
| [AGENTS.md](AGENTS.md) | Agent entry point, project boundaries and verification workflow |
| [docs/proposal-writing.md](docs/proposal-writing.md) | Call analysis, evidence, proposal logic, drafting/review and handoff |
| [docs/part-a.md](docs/part-a.md) | Administrative value types, field lengths, source confidence and budget calculations |
| [docs/formatting.md](docs/formatting.md) | Layout decisions and Part B formatting rules |
| [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) | Attribution and source-specific terms |

Original project code is under the [MIT licence](LICENSE). The modified
`he-ria26.bst` retains the `plainnat` family's LPPL terms and attribution.
Those terms do not replace the rights in adapted guidance, bibliographic data or
proposals subsequently written with the template.
