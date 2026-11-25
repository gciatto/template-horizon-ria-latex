# Source registry

This directory preserves the inputs used to build the template and records
their provenance. The three original files below are byte-for-byte copies;
the adapted author files, styles, checks and agent guidance live elsewhere in
the project. Keep scientific references cited by a proposal in `bibliography.bib`.

## Preserved inputs

| File | Origin | Version or date established by the source | Role in this project |
| --- | --- | --- | --- |
| [template-he-ria-part-b-5.1.rtf](template-he-ria-part-b-5.1.rtf) | User-supplied European Commission RIA/IA Part B template, with the same filename | **Version 5.1, 22 January 2026**; confirmed in the local RTF cover and change history | Part B headings, tables, guidance and appearance; shared layout baseline |
| [part-a-structure-source.zip](part-a-structure-source.zip) | User-supplied `horizon-part-a-templates(2).zip` | No archive release version declared; its data dictionary cites **Horizon Europe ver 1.00 20241022** | Administrative structure, partner-file convention, question catalogue, budget fields and source-confidence annotations |
| [AGENTS-horizon.md](AGENTS-horizon.md) | User-supplied proposal-writing agent instructions, with the same filename | No release version declared; its provenance reports an external-guidance check on **25 November 2026** | Adapted into `docs/proposal-writing.md`, reached through the root `AGENTS.md` |

### Part B RTF

The RTF identifies itself as *Project proposal – Technical description
(Part B), Version 5.1, 22 January 2026*. Its V5.1 change-history entry records
formatting changes to section 2.3 and the instruction to remove that summary
when unused. The visible form version is the baseline; the RTF editor's
internal revision metadata is not another application-form release.

This is the full-proposal form for a single-stage call or the second stage of
a two-stage call. The actual call's Submission System template takes precedence.
Layout decisions and supported page profiles are explained in
[formatting.md](../docs/formatting.md).

### Part A structure

The archived `schemas/fields.json` identifies its evidence as
`Proposal-SEP-211303496.pdf`, administrative pages 1–202 of a 303-page proposal,
with form label `Horizon Europe ver 1.00 20241022`. That underlying proposal PDF
was not supplied with this integration. These are the archive's recorded
provenance and confidence annotations, not a new inspection of that PDF.

Current-form refinements made during integration are recorded separately in
[part-a.md](../docs/part-a.md), including the EC Part A version 3.0 reference
below. The original ZIP remains unchanged and does not contain those adaptations.

### Proposal-writing instructions

The supplied document says it was adapted from companion paper-writing
instructions inspired by PaperOrchestra, and reports checking its linked EC
guidance on 25 November 2026. Preserve that statement as source provenance;
adapting the writing workflow does not establish a fresh verification of the
external documents. See [source notices](../THIRD_PARTY_NOTICES.md).

### SHA-256 checksums

Hashes cover the exact original bytes, including original line endings.
They are not hashes of extracted text or of the derived project files.

```text
507cc6ad2831936b3b41e2bed6ec784cb1c50ba61b1e8dd80590639565575977  template-he-ria-part-b-5.1.rtf
e96d1b07aaf10e7bf589ba14fee1e2f885bea42ca8cfe2f07141512f177b7cfd  part-a-structure-source.zip
8036877e896f65949749fe757a367844f59e78c880a96b5b97f89352d1cf6769  AGENTS-horizon.md
```

## Authoritative external references

The records below distinguish versions/dates actually documented during the
integration from links inherited through a supplied source. They do not claim
that a document's current online bytes have been downloaded again. Check the
live call documents when preparing an application.

### EC application form

- URL: [Standard RIA/IA application form](https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/horizon/temp-form/af/af_he-ria-ia_en.pdf).
- Recorded check: **25 November 2026**, as documented in `docs/formatting.md`
  and `docs/part-a.md`.
- Recorded versions: **Part A version 3.0, 10 November 2025** and
  **Part B version 5.1, 22 January 2026**.
- Use: official Part A refinements and Part B formatting/page instructions.
  The recorded combined PDF has 54 pages; Part B's printed instruction page 3
  is page 30 of that PDF.

### General Annexes

- URL: [Horizon Europe Work Programme 2026–2027 General Annexes](https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/horizon/wp-call/2026-2027/wp-15-general-annexes_horizon-2026-2027_en.pdf).
- Recorded edition: **2026–2027**; retrieved during integration on
  **25 November 2026**. No separate revision identifier was recorded.
- Use: Annex A, page 4, for full-proposal page limits and call-specific
  precedence; budget guidance and exclusions referenced in `docs/part-a.md`.
- The supplied writing workflow also links a
  [Commission document-register copy](https://ec.europa.eu/transparency/documents-register/api/files/C%282026%296687_15/090166e534337d81).
  Its reported check date belongs to that source's provenance, as described above.

### Model Grant Agreement

- URL: [Horizon Europe and Euratom General Model Grant Agreement](https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/common/agr-contr/general-mga_horizon-euratom_en.pdf).
- Retrieved during integration on **25 November 2026**. No specific revision
  identifier was recorded.
- Use: Articles 6.2.D.2 and 6.2.E, as cited in `docs/part-a.md`, for internally
  invoiced costs and the ordinary indirect-cost base. The checker implements
  the supported categories described there; a different call may need changes.

### Evaluation and programme guidance

These URLs are inherited from `AGENTS-horizon.md`. Its provenance reports
checking the linked guidance on 25 November 2026; no individual document
versions or independent retrieval records were supplied with that workflow.

| Reference | Role in the writing workflow |
| --- | --- |
| [RIA/IA evaluation form](https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/horizon/temp-form/ef/ef_he-ria-ia_en.pdf) | Criterion-based drafting and critical review |
| [Dissemination and exploitation](https://research-and-innovation.ec.europa.eu/strategy/dissemination-and-exploitation-research-results_en) | Distinguish communicating/sharing results from putting them to use |
| [Lump-sum grant guidance](https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/common/guidance/how-to-manage-your-lump-sum-grants_en.pdf) | Work-package completion and applicable lump-sum budgeting |
| [Gender in EU research and innovation](https://rea.ec.europa.eu/gender-eu-research-and-innovation_en) | Research-content analysis, team balance and institutional eligibility |
| [Horizon Europe Programme Guide](https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/horizon/guidance/programme-guide_horizon_en.pdf) | Programme-level and cross-cutting requirements |
| [Ethics self-assessment guidance](https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/common/guidance/how-to-complete-your-ethics-self-assessment_en.pdf) | Ethics questions, assessments and planned safeguards |
| [Responsible-AI guidance](https://research-and-innovation.ec.europa.eu/document/download/edc8027b-2811-4347-82f4-fa8b29ece534_en?filename=ec_rtd_ai-guidelines-factsheet.pdf) | AI-assisted research/writing practices and applicant responsibility |

## Implementation references

| Reference | Recorded provenance and use |
| --- | --- |
| [gciatto/erc27-formagent](https://github.com/gciatto/erc27-formagent) | User-supplied `erc27-formagent-master.zip`; project organisation and compact bibliography policy. The exact supplied snapshot is identified below; the full archive is not bundled. |
| [logological/heria](https://github.com/logological/heria) | Inspected at commit `518f234c1c47e84451cb7705fe1331c4fc72d3b7`; supports V5.1. No `heria` source is incorporated. |
| [natbib distribution](https://ctan.org/pkg/natbib) and [LPPL](https://www.latex-project.org/lppl/) | The renamed `he-ria26.bst` derives from the `plainnat` family; its original header and licence terms are preserved. |
| [PaperOrchestra](https://github.com/google-research/paper-orchestra) | Inspiration attributed by the supplied writing instructions; no separate inspection or code reuse is claimed here. |

See [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) for copyright and
licence attribution.

### Supplied ERC snapshot

- Input: user-supplied `erc27-formagent-master.zip`, **13,839,247 bytes**.
- Archive-recorded snapshot identifier (ZIP comment):
  `38405756a50599ed455de7be108ebecf40f7e024`.
- SHA-256 of the supplied archive:
  `e442c840db23f39af7888a406ac61ddff879b6281b3f24bed2d7b0bfb66c5bd0`.
- Use: shared metadata/project organisation, build conventions and the compact
  bibliography-formatting policy; one example reference remains in the template.

This is an **external input, not bundled** in `references/` or release archives.
The snapshot identifier comes from the supplied ZIP rather than a new upstream
repository lookup. Its proposal material and personal documents are not part
of this generic template.

## Maintaining this registry

When adding a template or call source, retain its original bytes and record its
origin, actual version/date, retrieval date when known, SHA-256 and the decisions
it supports. Distinguish direct verification from a supplied source's statements
or an inferred constraint. Preserve older versions under distinct filenames
when an update must remain traceable. Update the affected author guidance,
styles and checks together when an authoritative requirement changes.

This registry is maintained by agents/template maintainers. Proposal authors
continue to edit `.tex` and `.bib` files.
