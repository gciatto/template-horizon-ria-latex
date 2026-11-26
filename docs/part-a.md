# Part A fields, budgets and checks

## Source and scope

The administrative structure and constraints are maintained in
`scripts/data/part-a-fields.json` and `scripts/data/part-a-questions.json`.
Their confidence labels distinguish explicit constraints, counter-derived
limits, observed values and inferences. These inherited labels do not
constitute a fresh verification of the actual call's requirements.

The actual call's Portal form determines its enabled fields and conditional
follow-up questions. The PDF produced here coordinates answers for entry
into the Portal.

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

| Field | Limit | Basis recorded in the constraint catalogue |
| --- | ---: | --- |
| Proposal title | 200 characters | Explicit limit |
| Free keywords | 200 characters | Explicit limit |
| Abstract | 2,000 characters | Exact counter reconstruction |
| Other participant role | 50 characters | Explicit limit |
| Achievement description | 500 characters | Explicit limit |
| Previous-project description | 500 characters | Explicit limit |
| Infrastructure description | 300 characters | Explicit limit |
| Ethics dimension narrative | 5,000 characters | Counter-derived limit |
| Ethics compliance narrative | 5,000 characters | Counter-derived limit |
| Other ethics explanation | 1,000 characters | Explicit limit |
| Security national-restrictions explanation | 1,000 characters | Explicit limit |
| Other security explanation | 1,000 characters | Explicit limit |
| Security self-assessment | 5,000 characters | Explicit limit |

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
| Previous proposal reference | Six or nine digits, as recorded in the constraint catalogue |
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
The ethics/security catalogue is maintained in `scripts/data/part-a-questions.json`.
Add call-specific follow-up prompts and answers as ordinary
LaTeX in the relevant `.tex` source or `part-a-other.tex`. Adding a new typed
field ID is a template-maintenance change and also requires its checker definition.

## Budget arithmetic

The budget fields represent six ordinary direct-cost categories: personnel,
subcontracting, travel/subsistence, equipment, other goods/works/services, and
internally invoiced goods/services. For the standard profile, the checker uses:

```text
indirect = round_to_cents(0.25 × (personnel + travel + equipment + other purchases))
total eligible = sum(six direct-cost categories) + indirect
maximum EU contribution = round_to_cents(total eligible × funding rate / 100)
total estimated income = requested EU + action income + financial contributions + own resources
```

The implemented indirect-cost base excludes subcontracting and internally
invoiced costs. Verify the applicable rate, categories and exclusions for
the selected call.

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
