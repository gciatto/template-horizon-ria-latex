# Part A fields, budgets and checks

## Source and scope

The administrative structure comes from the supplied
`horizon-part-a-templates(2).zip`, preserved as
`reference/part-a-structure-source.zip`. Its data dictionary identifies
`Proposal-SEP-211303496.pdf`, administrative pages 1–202, and form version
`Horizon Europe ver 1.00 20241022` as its original evidence. That source PDF
was not supplied with this integration; the archive's evidence labels are
retained rather than presented as a fresh examination of that proposal.

The [EC standard RIA/IA application form](https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/horizon/temp-form/af/af_he-ria-ia_en.pdf)
was checked on 25 November 2026. Its Part A version 3.0, dated 10 November 2025,
supplies the title/keyword limits, conditional lump-sum declaration and
other-ethics explanation added during integration. The actual call's Portal
form determines its enabled fields and conditional follow-up questions.

These sources serve different purposes: the supplied archive provides the
editable drafting structure; current official guidance refines known rules.
The PDF produced here coordinates answers for entry into the Portal.

## What to edit

All author input belongs in `.tex` and `.bib` files. The administrative sources
use four small constructs:

| Construct | Meaning |
| --- | --- |
| `\AField{field.id}{value}` | One typed or narrative value |
| `\AQuestion{id}{question}{answer}{Part B pages}` | A yes/no answer with page references |
| `\ADeclaration{number}{statement}{confirmation}` | A coordinator declaration |
| `\begin{ARecord}{record_type} ... \end{ARecord}` | One organisation, contact, researcher, achievement or other repeated record |

Empty fields and `unanswered`/`unconfirmed`/`unknown` are recognised as unfinished.
A bracketed placeholder is also unfinished. Keep stable field IDs intact;
change the value in the final braces. Repeated records can be copied as ordinary
LaTeX blocks. Rendering and inclusion modes are implemented in `he-admin26.sty`.
The schemas under `scripts/data/` are internal checker data; ordinary authors
do not edit or regenerate them.

## Field lengths

Lengths include spaces. Blank lines denote paragraph breaks; physical source
line wrapping is normalised to spaces as in ordinary LaTeX prose.

| Field | Limit | Evidence |
| --- | ---: | --- |
| Proposal title | 200 characters | Current EC Part A, printed p. 4 |
| Free keywords | 200 characters | Current EC Part A, printed p. 4 |
| Abstract | 2,000 characters | Exact counter reconstruction recorded in the supplied archive |
| Other participant role | 50 characters | Explicit limit recorded in the supplied archive |
| Achievement description | 500 characters | Explicit limit recorded in the supplied archive |
| Previous-project description | 500 characters | Explicit limit recorded in the supplied archive |
| Infrastructure description | 300 characters | Explicit limit recorded in the supplied archive |
| Ethics dimension narrative | 5,000 characters | Counter-derived limit recorded in the supplied archive |
| Ethics compliance narrative | 5,000 characters | Counter-derived limit recorded in the supplied archive |
| Other ethics explanation | 1,000 characters | Current EC Part A, printed p. 20 |
| Security national-restrictions explanation | 1,000 characters | Explicit limit in the supplied archive and current EC form |
| Other security explanation | 1,000 characters | Explicit limit in the supplied archive and current EC form |
| Security self-assessment | 5,000 characters | Current EC Part A, printed p. 23 |

The title excludes `<`, `>`, `"` and `&`. Unknown lengths remain unspecified.
Each participant may provide up to five achievements and five previous projects.
Other repeated-record counts have no invented maximum.

The checker resolves the shared values defined in `metadata.tex` and understands
ordinary text formatting. It reports a count as uncertain when unresolved
commands prevent reliable text extraction. Exact final Portal text can be
checked independently with `scripts/count_chars.py`; that command counts
literal Unicode code points, including every space and line break in the file.

## Value types

Use ordinary LaTeX escapes for special characters in prose (for example `\&`).
Numeric fields use literal values without formatting commands.

| Type | Input convention |
| --- | --- |
| Answer / boolean | `yes`, `no`; `unanswered` while drafting |
| Declaration | `yes` when confirmed; `unconfirmed` while drafting |
| Participant role | `coordinator`, `partner`, `affiliated` |
| Participant number / duration | Positive integer without leading zeroes |
| Gender | `woman`, `man`, `non_binary`, or unfinished |
| Researcher career stage | `A`, `B`, `C`, `D`, or unfinished; D is inferred in the source |
| Researcher role | `leading`, `team_member`, or unfinished |
| Date | A real calendar date in `DD/MM/YYYY` form |
| EUR amount | Nonnegative decimal with at most two decimal places, e.g. `1250.50` |
| Funding rate | Numeric percentage from 0 to 100, e.g. `100` |
| PIC | Nine digits |
| Previous proposal reference | Six or nine digits, as recorded in the supplied archive |
| Part B page references | Numbers, lists or ranges such as `3`, `3, 7`, `7-9` |

For participating-organisation roles, use a comma-separated selection from:

- `project_management`
- `communication_dissemination_engagement`
- `research_technology_infrastructure`
- `research_market_needs`
- `civil_society_representative`
- `policy_maker_regulator_standardisation`
- `research_performer`
- `technology_developer`
- `testing_validation`
- `prototyping_demonstration`
- `ipr_management_technology_transfer`
- `public_procurer`
- `private_buyer`
- `finance_provider`
- `education_training`
- `social_sciences_humanities`
- `other`

Supply the role explanation when `other` is selected. Identifiers containing
underscores are accepted directly by the field renderer. Registry-derived
organisation statuses should match the organisation's Portal record.

## Partner identity and completeness

Every organisation has one `partners/partner-N-ACRO-admin-form.tex` source.
It contains its participant record, repeated administrative records and one
budget record. The ordered manifest `partners/participants.tex` supplies both
Part A passes and Part B's participant list.

Checks match the filename number/acronym against the fields, detect duplicate
numbers, verify the manifest, and check each organisation's required fields
independently. One completed partner cannot conceal another partner's missing
contact or identity. The source's affiliated-entity contact exception is retained.

The ordinary check accepts incomplete drafting information. The strict check
requires the known mandatory fields, confirmations and applicable explanatory
narratives. It does not certify that every call-specific online field is covered.
The inherited ethics/security catalogue reflects questions visible in the
supplied source. Add call-specific follow-up prompts and answers as ordinary
LaTeX in the relevant `.tex` source or `part-a-other.tex`. Adding a new typed
field ID is a template-maintenance change and also requires its checker definition.

## Budget arithmetic

The supplied stub represents six ordinary direct-cost categories: personnel,
subcontracting, travel/subsistence, equipment, other goods/works/services, and
internally invoiced goods/services. For the standard profile, the checker uses:

```text
indirect = round_to_cents(0.25 × (personnel + travel + equipment + other purchases))
total eligible = sum(six direct-cost categories) + indirect
maximum EU contribution = round_to_cents(total eligible × funding rate / 100)
total estimated income = requested EU + action income + financial contributions + own resources
```

These are the ordinary-category calculations in the supplied source. The
[Horizon Europe Model Grant Agreement](https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/common/agr-contr/general-mga_horizon-euratom_en.pdf),
Articles 6.2.D.2 and 6.2.E, excludes internally invoiced costs from the indirect
base and establishes the 25% flat rate with its listed exclusions. The
[2026–2027 General Annexes](https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/horizon/wp-call/2026-2027/wp-15-general-annexes_horizon-2026-2027_en.pdf)
also describe that rate and exclusions.

Calculations use decimal arithmetic. Every supplied amount is checked for
finiteness, sign and precision. Empty means unknown; zero means known zero.
The report separates computed expectations from supplied values and aggregates
monetary totals without adding funding-rate percentages. For a call enabling
additional categories, adapt the budget field/check specification before using
its totals as complete.

For `FUNDING=lump-sum`, the checker validates supplied numeric values and generic
arithmetic without treating the standard reimbursement calculation as the
lump-sum award. The detailed lump-sum budget is a separate call deliverable when
required; declaration 10 is displayed and checked only in this profile.

## Reports and commands

```sh
make check-admin
make check-budget
make strict
python3 scripts/check_admin.py --json build/admin-checks.json
python3 scripts/check_budget.py --json build/budget-checks.json
```

`make check` runs the drafting checks together with both clean PDF checks.
`make strict` is a separate completeness gate; it is intentionally excluded
from the reusable blank template's CI release gate.
