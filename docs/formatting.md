# Formatting and provenance

## Authoritative sources

Part B implements the supplied **Horizon Europe RIA/IA Part B V5.1,
22 January 2026**. It is the full-proposal form for a single-stage call or
the second stage of a two-stage call.

- [EC standard application form, including Part B V5.1](../references/README.md#ec-application-form),
  Part B instructions, printed page 3; page 30 of the combined 54-page PDF checked on 25 November 2026.
- [2026–2027 Work Programme General Annexes](../references/README.md#general-annexes),
  Annex A, page 4, for page limits and the precedence of the actual submission-system form.
- The supplied RTF is retained unchanged in
  [`references/template-he-ria-part-b-5.1.rtf`](../references/template-he-ria-part-b-5.1.rtf).
  Its checksum, provenance and the upstream URLs are recorded in the
  [source registry](../references/README.md).

Use the template downloaded inside the Portal for the actual topic to identify
call-specific changes. The generic template is the baseline implemented here.
Part A uses the same visual style for administrative drafting; its field
structure and constraints are documented separately in `docs/part-a.md`.

## Layout decisions

| Element | Implemented setting | Reason |
| --- | --- | --- |
| Paper | A4, 210 × 297 mm; optional impact canvas on A4 landscape | Same page format and canvas orientation as the supplied form |
| All body margins | Exactly 15 mm | Minimum permitted on every side |
| Portrait body area | 180 × 267 mm | Headers and footers are outside this rectangle |
| Body and table font | Times-compatible Nimbus Roman through `mathptmx` | The reference Linux font family; ordinary font metrics |
| Body and table size | Exactly 11 `bp` | 11 physical PDF points; avoids the smaller size implied by LaTeX's nominal `11pt` option |
| Line spacing | `\linespread{1}`, 13.2 `bp` baseline for 11 `bp` body | Ordinary single spacing, with no compressed lines |
| Character spacing | Standard | No tracking, font expansion, condensed font or scaled text |
| Prose paragraphs | 1 em first-line indentation; exactly 0 pt `\parskip` | Paragraphs are separated by indentation, including the first after headings |
| Headings | Black bold serif, official numbering and labels | Matches the blank proposal form |
| Running header | Call identification and official template version | Matches the RTF |
| Footer | Grey framed band, “Part B – Page n of limit” | Matches the form's page-limit placeholder rather than presenting the limit as a total page count |
| Guidance | Blue; removable as a whole | Distinguishes instructions from author text |
| Impact canvas | Six turquoise panels, three columns by two rows | Preserves the form's visual language with stable, non-overlapping layout |

The RTF already specifies 851 twips, approximately 15.01 mm, on every side.
There is effectively no additional margin area to recover from that document.
The template instead reduces avoidable paragraph, heading and table padding,
and gives the header and footer their own space inside the permitted margins.
The instruction cover, revision history, large empty answer areas and
instruction watermarks are not part of the proposal PDF.

The same paragraph policy applies to authored prose, blue `heguidance`
paragraphs, administrative narrative answer boxes, `\HEParagraph`, and native
`\paragraph`/`\subparagraph` run-in headings. Ordinary line spacing stays at
13.2 `bp`. Lists, field labels, tables, captions and headings retain the
structural spacing appropriate to those elements. Separate prose paragraphs
with a blank source line; additional manual vertical space is unnecessary.

Headers, footnotes and captions may be smaller under the form's express
exception for text other than body text. That exception does **not** apply to
ordinary text in tables. Template tables retain 11-point text and wrap their
contents instead of shrinking them.

## Page and character accounting

The supplied full-proposal baseline uses a **40-page** standard RIA cap and a
**45-page** lump-sum RIA cap. The title, participant list, all three evaluation sections,
tables, figures and references all count. There is no ERC-style exemption for
references. Call-specific limits can override these defaults.

The footer and the counting scripts use the same profile and page limit from
the compiled `.hemeta` sidecar. The PDF's actual pages are counted rather than
estimated from source lines. All pages, including landscape pages, count once.
Page sizes are checked for each page.

The form does not impose a global Part B character cap. PDF character counts
are therefore diagnostics. They measure extracted visible text, including
repeated headers, footers, table text and bibliography. They are not exact
Portal-field counts or an estimate of page usage. `scripts/check_admin.py`
checks bounded Part A fields after normalising ordinary LaTeX text and resolving
metadata macros. `scripts/count_chars.py` counts literal UTF-8 field text with
an explicitly supplied limit. Part A has no inherited Part B page cap.

Indicative allocations in the supplied form are 4 pages for 1.1, 14 for 1.2,
3 for 2.1, 3 for 2.2 excluding 2.3, 12 for 3.1 (17 for lump sum), and 3 for 3.2.
They are guidance, not independent hard limits or a guarantee that their sum
leaves space for the title, participants and bibliography.

## Version-specific structure

- Version 5.0 removed the machine tags used in older templates.
- Section 2.3 is optional. `\HEImpactSummaryfalse` removes both its heading and canvas.
- The implementation tables are 3.1a through 3.1h.
- Table 3.1h concerns equipment costs exceeding 15% of a participant's personnel costs.
- The source is named `part-b2.tex` to match the requested project convention;
  the document itself correctly identifies the Horizon component as **Part B**.
- Part A is produced by the Portal. This project's local administrative PDF
  supports drafting and coordination and uses an uncapped Part A footer.

## Relationship to the reference repositories

[logological/heria](../references/README.md#implementation-references), commit
`518f234c1c47e84451cb7705fe1331c4fc72d3b7`, was inspected. That snapshot
supports V5.1, but this project implements its own small style package rather
than depending on the generated class and its data model. This permits the
requested file structure, exact physical font size, and a text rectangle that
does not reserve header/footer height inside the body margins. No `heria`
source is incorporated.

The uploaded [`erc27-formagent-master.zip` snapshot](../references/README.md#supplied-erc-snapshot) supplied the project-organisation
reference: shared metadata, a dedicated `.sty`, guidance switching, Make
targets and a dated release workflow. Its compact bibliography-formatting
policy is retained, with just one example bibliographic entry. Its proposal text, project identity, personal documents and
ERC-specific page exemptions are not carried into this generic RIA template.

The bibliography backend is BibTeX with `natbib`. The local `he-ria26.bst`
implements the ERC project's numeric name/year/title ordering, family-given
names with initials, and two-author limit (first author and “et al.” for longer
lists). It keeps author, title, year and the first available identifier in the
order DOI, arXiv eprint, URL; full publication details are retained when none
of those identifiers is present. It supports `@online` and a year fallback
from `date`. Only cited references print. This choice retains the formatting
policy while keeping the build small and avoiding a Biber dependency.
