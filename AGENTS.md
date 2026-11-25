# Agent instructions

These instructions apply to the whole Horizon Europe RIA template repository.
Read `README.md` for commands, `docs/formatting.md` for layout rules, and
`docs/part-a.md` for administrative types, limits and budget scope.
For proposal drafting, substantive revision or critical review, also read and
apply `docs/proposal-writing.md`. It covers call analysis, evidence, project
logic, the evaluation sections and final handoff; apply it proportionately to
the requested change.

## Author interface and project map

- Ordinary proposal authors edit `.tex` and `.bib` only. Keep presentation,
  repeated-inclusion logic, validation and generation in styles or scripts.
  Do not require authors to edit JSON schemas or run schema generators.
  Markdown guidance and internal schemas are agent/maintainer interfaces.
- `metadata.tex` supplies shared project values. Reuse its macros in both parts.
- `part-a.tex` assembles general information, partners, budget, ethics/security
  and call-specific questions through the other `part-a-*.tex` files.
- Each `partners/partner-N-ACRO-admin-form.tex` holds one organisation's
  administrative records and budget. `partners/participants.tex` is the ordered
  manifest used by Part A, the budget section and Part B's participant list.
- `ethics/` contains editable questions and assessment narratives.
- `part-b2.tex`, `sections/` and `tables/` contain the technical description.
  The rendered component is named **Part B**.
- `he-ria26.sty` owns shared typography, layout, headings and guidance;
  `he-admin26.sty` owns administrative rendering and partner inclusion modes.
- `bibliography.bib` holds references; `he-ria26.bst` preserves the compact
  numeric ERC formatting policy. Keep one example in the generic template;
  add relevant sources when drafting a proposal.
- `scripts/`, `Makefile`, `tests/` and `.github/workflows/build.yml` own automation.
  Internal schemas/scaffolds under `scripts/data/` are maintained with the tools.
- Keep original inputs in `reference/` unchanged.

## Proposal content and presentation

- Ground proposal facts in the user's material. Retain empty fields or
  `\HEPlaceholder{...}` when facts are missing; do not invent participants,
  research results, commitments, contact details or costs.
- Preserve Part B V5.1 headings and tables 3.1a–3.1h. The actual call-specific
  Portal template takes precedence over generic defaults.
- Keep stable administrative field IDs, record boundaries and partner naming
  consistent with the checker. Add/update validation and labels when extending
  the field specification; do not silently ignore unknown fields.
- Keep incomplete information distinct from known zero/false/no values.
  Preserve evidence and confidence labels for inferred administrative limits.
- Put author guidance in `heguidance`, `\HEGuide`, `\HECriterion` or `\HEBudget`.
  It appears in blue and disappears in clean mode without executing hidden
  citations or labels. Authored text and unfinished placeholders remain visible.
- Preserve the supplied form's A4, 15 mm body margins, 11 `bp` body/table text, reference-font
  metrics, standard character spacing and single line spacing. Resolve overflow
  through content or layout; avoid shrinking/scaling ordinary table text.
- Use semantic source lines and ordinary LaTeX cross-references. Keep partner
  identifiers, work packages, staff effort and costs consistent across parts.

## Funding, limits and budget checks

- Unset or empty `FUNDING` means `standard` RIA. Select `FUNDING=lump-sum`
  explicitly. Make/script settings override direct-compilation metadata defaults.
- The supplied full-RIA profiles default to 40/45 pages; verify the actual call
  and submission stage before applying those limits. The applicable cap covers
  the whole Part B PDF, including references. Part A has field constraints and
  no inherited Part B page cap. `FUNDING` selects the funding model, not another
  action type or submission stage.
- Apply `PAGE_LIMIT` only for an evidenced call-specific Part B limit. The
  footer and PDF checks use the generated `.hemeta` sidecar consistently.
- Administrative text counts include spaces and paragraph breaks after stated
  normalisation. Flag unresolved commands instead of presenting an exact count.
  `count_chars.py` counts literal UTF-8 field text when exact source text is known.
- Use decimal arithmetic for money, validate each partner separately, and
  distinguish supplied values, calculated expectations and incomplete totals.
  Do not apply standard reimbursement formulas to lump-sum awards automatically.
- Preserve the pristine blank scaffold used by `add_partner.py`. Creating a
  partner must not clone another partner's completed personal or budget data.

## Build and validation

- Use pdfLaTeX, BibTeX and existing packages. Keep dependencies minimal and
  compilation independent of shell escape or Python source-generation steps.
- `make` builds both parts with and without guidance; `make check` checks draft
  values, budgets and both clean PDFs. Blank fields are allowed at this stage.
- `make strict` checks administrative completeness and intentionally fails the
  blank template. Keep it separate from the generic template's CI release gate.
- For behavioral changes, run the relevant tests. Add focused regression tests
  for concrete risks, keeping test commits separate from implementation commits.
  Documentation-only changes do not need PDF rebuilds.
- Inspect affected rendered pages after layout/content changes. Check both modes
  for guidance changes and both profiles for funding changes. Finish distribution
  builds with `FUNDING` unset so previews use standard RIA.
- `make dist` validates and packages all four PDFs, sources and reports.
  Preserve UTC version format `YYYY.MM.DD-hh-mm` and existing-release guards.
- `make ci` runs independent checks to completion and retains per-check logs,
  JSON results and a Markdown summary under `build/ci/`. Keep failures visible:
  skipped or unfinished checks must never be reported as passed.
- GitHub Actions builds and uploads PDFs/logs on every branch and pull request.
  Publish releases only after a successful push/manual build of `master`.
  Preserve failure summaries and log uploads even when a check fails.
- Edit sources, not generated files in `build/` or `dist/`. Keep `.gitignore`
  aligned with generated outputs while retaining authored figures and sources.

## Working with changes

- Inspect the working tree first and preserve unrelated user edits.
- Scope work to the request. Use small Conventional Commits; separate test
  commits from feature/fix/build/documentation commits.
- Report changed behavior, checks actually run and unresolved issues.
  Distinguish local validation from GitHub Actions runs.
