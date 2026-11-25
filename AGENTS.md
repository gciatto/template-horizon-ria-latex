# Agent instructions

These instructions apply to the whole Horizon Europe RIA template repository.
Read `README.md` for build commands and `docs/formatting.md` before changing
the document layout or interpreting submission limits.

## Project map

- `metadata.tex`: shared proposal identifiers, participants, optional impact
  summary and defaults for direct LaTeX compilation. Reuse its macros rather
  than repeating project data in content files.
- `part-b2.tex`: main document and section inclusion order. The rendered
  component is named **Part B**.
- `sections/` and `tables/`: proposal text, author guidance and implementation
  tables. Keep prose changes here rather than embedding them in the style.
- `he-ria26.sty`: typography, layout, guidance controls and document helpers.
- `bibliography.bib` and `he-ria26.bst`: reference data and compact numeric
  formatting. Retain the ERC formatting policy and one example entry while
  maintaining the generic template; add relevant sources when drafting a proposal.
- `scripts/`, `Makefile`, `tests/` and `.github/workflows/build.yml`: build,
  validation and date-versioned release automation.
- `reference/`: original supplied form; keep it unchanged.

## Proposal content and presentation

- Preserve the official V5.1 headings, section numbering and tables 3.1a–3.1h.
  Follow the actual call-specific Portal template when it changes the generic form.
- Ground proposal facts in the user's material. Keep missing information as
  `\HEPlaceholder{...}`; do not invent partners, results, commitments or costs.
- Put author guidance inside `heguidance`, `\HEGuide`, `\HECriterion` or
  `\HEBudget`. It must appear in blue in guidance mode and disappear in
  submission mode without executing hidden citations or labels.
- Keep authored content, cross-references and unfinished placeholders visible
  in both modes. Keep participant/WP identifiers and totals consistent across files.
- Retain A4 pages, 15 mm body margins, 11 `bp` body/table text, reference-font
  metrics, standard character spacing and single line spacing. Resolve overflow
  through content or layout changes, not smaller fonts or scaled tables.
- Use semantic source lines and ordinary LaTeX labels/cross-references.
  Part A drafting support is deferred until requested; do not introduce
  ERC-specific fields or reference-page exemptions.

## Funding and limits

- Unset or empty `FUNDING` means `standard` RIA. Select lump-sum explicitly
  with `FUNDING=lump-sum`; make/script settings override the direct-compilation
  fallback in `metadata.tex`.
- The standard/lump-sum defaults are 40/45 pages. Count the entire PDF,
  including the title, participants, landscape pages, tables and references.
- Use `PAGE_LIMIT` only for an evidenced call-specific limit. Keep the footer
  and checking scripts consistent through the generated `.hemeta` sidecar.
- Part B character counts are diagnostic. For a plain-text field, use
  `scripts/count_chars.py` with the field's explicitly specified limit.

## Build and validation

- Use pdfLaTeX, BibTeX and the existing packages. Keep dependencies minimal
  and preserve compilation without shell escape.
- After content, style or build changes, run `make` and `make check`.
  Inspect affected rendered pages for overflow, broken tables and page breaks.
- For behavioral changes, run the relevant tests (`make test` runs all of
  them). Add focused regression tests when they address a concrete risk;
  documentation-only edits do not require a PDF rebuild.
- Check both modes when changing guidance, and both funding profiles when
  changing profile resolution. Finish a default-template build with `FUNDING`
  unset so distributed previews use standard RIA.
- Use `make dist` for release assets. Preserve the UTC version format
  `YYYY.MM.DD-hh-mm`. Edit sources rather than generated files in `build/` or `dist/`.

## Working with changes

- Inspect the working tree first and preserve unrelated user edits.
- Keep changes scoped to the request. Use small Conventional Commits, with
  test commits separate from implementation commits.
- Report the changed behavior, checks actually run and any unresolved issue.
  Distinguish locally validated builds from GitHub Actions runs.
