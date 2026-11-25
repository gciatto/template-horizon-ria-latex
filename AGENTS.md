# Horizon Europe RIA template

- Use `metadata.tex` for proposal identifiers, participants and funding profile.
- Preserve the official V5.1 section numbers and tables 3.1a--3.1h.
- Keep body and table text at least 11 physical points and all margins at least 15 mm.
- Keep reference-font metrics, standard character spacing and single line spacing.
- Put guidance inside `heguidance`, `\HEGuide`, `\HECriterion` or `\HEBudget`.
- Guidance must disappear in submission mode. Authored content and placeholders must remain.
- The full Part B PDF, including references, counts towards the 40/45-page cap.
- Treat the actual call-specific Portal template as authoritative over generic defaults.
- Split prose into semantic source lines. Avoid unexplained negative spacing or scaled tables.
- After changes run `make check` and inspect the affected rendered pages.
- Use small Conventional Commits; keep test commits separate from implementation commits.
- Part A drafting support is deferred; do not copy ERC-specific Part A fields or limits here.
