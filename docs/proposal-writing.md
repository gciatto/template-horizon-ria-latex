# Writing and reviewing Horizon Europe proposals

Act as a careful proposal collaborator. Turn the consortium's ideas into a
credible, coherent and evaluable project. Persuade through evidence, a sound
project logic and a feasible delivery plan. Never improve apparent
competitiveness by inventing facts or commitments.

This is an agent/maintainer workflow. Ordinary proposal authors work in the
existing `.tex`, `.bib` and `metadata.sty` files. Apply the workflow proportionately: a new
application needs call analysis and project design; a local wording correction
needs the relevant inputs and checks, not a second planning system.

The repository defaults to a full collaborative RIA. The writing principles
also apply to IAs, but changing action type or submission stage requires checking
the actual form, evaluation criteria and budget rules. Do not impose this
structure on ERC, MSCA, EIC, CSA or other instruments with different requirements.

## 1. Establish the actual call requirements

- Read the existing proposal, consortium inputs, research evidence, work plan
  and budget before editing. Preserve terminology, author decisions and the
  project's file organisation.
- Identify the exact topic ID, action type, submission stage, deadline and time
  zone, funding model, requested contribution and duration. Without a selected
  topic, prepare a clearly provisional concept and do not claim call compliance.
- Retrieve the current topic conditions, relevant work programme and destination,
  applicable General Annexes, evaluation form and the template supplied inside
  the Submission System. Record versions and retrieval dates in existing
  project notes or nearby TeX comments. Public sample forms are starting
  references; the live call determines the application structure.
- Distinguish binding requirements from recommendations and examples. Apply
  explicit topic-specific exceptions. Flag conflicting instructions for
  resolution instead of silently choosing one.
- Verify admissibility and eligibility separately from proposal quality:
  consortium composition and independence, countries, entity roles, funding
  eligibility, restrictions, annexes and organisational conditions. Check when
  each condition must be satisfied. Participation does not automatically imply
  eligibility for EU funding.
- Read the actual scoring criteria, thresholds, weighting and stage-specific
  instructions. Do not carry page limits, reimbursement rates, consortium
  minima or evaluation rules over from another call or year.

Use the template baseline and constraints maintained in
[formatting.md](formatting.md#template-baseline) and
[part-a.md](part-a.md#source-and-scope), then verify their applicability to the
selected call. Update those documents when a requirement changes rather than
creating conflicting copies of the same rule.

`FUNDING` unset or empty selects this template's `standard` RIA profile;
`FUNDING=lump-sum` selects the lump-sum profile. Their Part B defaults
are 40 and 45 pages, respectively. These are configurable defaults for the
supported full-proposal form, not universal Horizon rules. Use `PAGE_LIMIT`
for an evidenced call-specific override and update the relevant template or
checker when a different requirement cannot be represented by that override.
The funding switch does not change the action type or submission stage.

## 2. Put each contribution in its source file

| Content | Author source |
| --- | --- |
| Shared title, acronym, topic, coordinator, duration and keywords | `metadata.sty`; reuse the macros across both parts |
| Consortium general information, abstract and declarations | `part-a/part-a-consortium.tex` |
| Each organisation's identity, contacts, researchers, achievements, previous projects, facilities and budget | Its `part-a/partners/partner-N-ACRO-admin-form.tex` |
| Participant inclusion and numbering order | `part-a/partners/participants.tex`; shared by both parts and the budget |
| Budget presentation | `part-a/part-a-budget.tex`; the actual amounts remain in each partner's file |
| Ethics/security questions and assessment narratives | `part-a/ethics/ethics-questions.tex`, `part-a/ethics/security-questions.tex`, `part-a/ethics/ethics-self-assessment.tex`, `part-a/ethics/security-self-assessment.tex` |
| Additional call-specific administrative questions | `part-a/part-a-other.tex` |
| Objectives, ambition and methodology | `part-b/sections/1-excellence.tex` |
| Pathways to impact, dissemination/exploitation/communication and optional summary | `part-b/sections/2-impact.tex` |
| Work plan, resources and consortium capacity | `part-b/sections/3-implementation.tex` and the corresponding files in `part-b/tables/` |
| Verified reference data | `bibliography.bib` |

Preserve the assembly files `part-a.tex`, `part-a/part-a-partner.tex`,
`part-a/part-a-ethics-security.tex` and `part-b.tex` unless their structure must change.
Keep layout and inclusion logic in `he-ria26.sty` and `he-admin26.sty`.

Administrative values use `\AField{field.id}{value}`. Edit the value while
preserving the field ID and its enclosing `ARecord`. Use `\AQuestion` for
yes/no questions and Part B page references, and `\ADeclaration` for
coordinator confirmations. Follow the types and constraints in
[part-a.md](part-a.md); do not invent field IDs that the checker will ignore.
Adding a new typed field is template maintenance and requires the corresponding
validation definition. Extra narrative questions can remain ordinary LaTeX.

Leave unknown typed values empty or use their recognised unfinished status.
Zero, `no` and `yes` are substantive answers, not substitutes for missing input.
Use `\HEPlaceholder{...}` for visible narrative gaps. Put author instructions
or working notes in `heguidance` or the existing guidance commands so they are
blue in the drafting PDF and absent from the clean PDF. Authored answers and
unresolved placeholders must remain visible when guidance is hidden.

## 3. Build one project logic

For a new application or major redesign, prepare or update a compact matrix:

**Topic requirement → proposal response → evidence or planned activity →
section → responsible partner → unresolved gap.**

Distinguish mandatory scope from optional examples and check whether the topic
requires all or selected outcomes. Keep the matrix in the existing planning
material or removable drafting guidance; do not impose another authoring format
for a local edit.

Connect the whole proposal through one chain:

**Need → objective → activities → results → uptake by specific users →
topic outcomes → destination impacts.**

- Give objectives stable identifiers. For each, define a verifiable success
  condition, a justified baseline where available, a proposed target,
  measurement method, timing and responsibility.
- Distinguish activities, deliverables, results, outcomes and longer-term
  impacts. A report documents work; it does not by itself demonstrate adoption
  or societal benefit.
- Trace objectives to work packages, validation and outcomes. Remove unsupported
  promises and tasks that serve no objective. Make the European and transnational
  rationale concrete.

## 4. Maintain evidence and commitment integrity

- Separate verified facts, preliminary findings, assumptions, proposed targets
  and confirmed commitments. Describe planned research as planned work.
- Never invent partner capabilities, PICs, personnel, facilities, publications,
  preliminary data, costs, access rights, users, pilot sites, letters of support
  or endorsements. Mark unconfirmed partners and arrangements as pending.
- Support technical, market and policy claims with sources checked for the
  exact assertion. Search literature, relevant products, patents and related
  EU projects as appropriate; use CORDIS to examine overlap and complementarity.
  Verify references before adding them to `bibliography.bib`.
- Give quantitative estimates a source or an explicit calculation and
  assumptions. Avoid false precision, unsupported market shares and double
  counting of beneficiaries or benefits.
- Keep missing inputs visible in working drafts, raise material gaps early and
  continue independent work. Do not turn a suggestion into an agreed consortium
  obligation or fill a declaration merely to make validation pass.

## 5. Excellence: explain why the approach can work

Write objectives and ambition in section 1.1 and methodology in section 1.2 of
`part-b/sections/1-excellence.tex`, using the actual call's evaluation criteria.

- Establish the problem and closest existing solutions, then identify the
  specific advance. Test novelty claims against contrary evidence; replace
  generic claims of uniqueness or revolution with supported comparisons.
- Explain the methodology, assumptions, integration between disciplines,
  validation design and alternatives. Distinguish the scientific approach from
  the task schedule in section 3.1.
- Match ambition and maturity to the action. Where Technology Readiness Levels
  apply, justify starting and intended end levels through demonstrable
  capabilities and validation environments.
- Specify comparisons, baselines, metrics, study populations or use cases,
  data access and evaluation conditions as relevant. Identify feasibility
  challenges and credible fallback approaches.
- Explain how prior projects and existing assets feed into the work, including
  the necessary access and the distinction from activities already funded.

Use the evaluation criteria applicable to the selected instrument and call.

## 6. Impact: explain who will use results and what changes

Use section 2.1 for pathways towards impact and section 2.2 for measures in
`part-b/sections/2-impact.tex`. Keep the optional section 2.3 canvas consistent with
those explanations.

- Identify concrete users, beneficiaries and adoption settings. Explain the
  mechanism connecting each relevant result to the topic's expected outcomes
  and the destination's wider impacts.
- Quantify contributions where meaningful. State the baseline, timeframe,
  reach, assumptions and calculation. Distinguish effects under project control
  from those dependent on later investment, policy or uptake.
- Address adoption barriers and external dependencies: regulation,
  interoperability, procurement, skills, trust, incentives, competing solutions
  and market conditions. Assign credible measures to address them.
- Keep communication, dissemination and exploitation distinct. Communication
  builds awareness; dissemination shares results with relevant audiences;
  exploitation puts results to use in research, products, services, standards,
  policy or practice.
- For each important result, identify its intended user, route to use,
  responsible partner, timing, resources and useful indicator. Publications,
  events and website visits alone do not demonstrate uptake.
- Explain protection, ownership, background assets, dependencies, licensing and
  access arrangements at the level actually agreed. Do not promise rights a
  partner cannot grant.
- Make post-project use credible through prospective owners, maintenance,
  financing or institutional adoption. Present unconfirmed arrangements as
  dependencies rather than secured sustainability.

Consult the Commission's [dissemination and exploitation guidance][exploitation]
when checking the distinction between sharing results and their actual use.

## 7. Implementation: make commitments deliverable

Use section 3.1 and tables 3.1a–3.1h for the work plan/resources, and section 3.2
for consortium capacity. The tables cover work-package summaries/descriptions,
deliverables, milestones, risks, staff effort, subcontracting and equipment.
Keep those roles and the actual call's requested columns intact.

- Organise work packages around coherent work and results. Define objectives,
  tasks or equivalent activities, leads, contributors, timing, dependencies
  and resources.
- Make deliverables useful and proportionate, with clear content,
  responsibility and due dates. Define milestones as verifiable decision or
  control points with the evidence needed to pass them.
- Check the critical path. Inputs must exist before dependent work begins;
  align pilots, recruitment, procurement, approvals, integration and validation
  with realistic lead times.
- Explain why each partner is needed, its owned work and evidence of capacity.
  Connect section 3.2 to the relevant achievements, projects and facilities in
  that partner's administrative file. Identify gaps and complementary roles;
  avoid generic biographies and partners without a defined contribution.
- Specify practical coordination, decision-making, quality assurance and
  conflict resolution in proportion to project complexity and template needs.
- Describe material risks with likelihood, severity, affected objectives,
  ownership, mitigation, warning indicators and fallback actions. Separate
  delivery risks from external barriers to impact. Do not classify every risk
  as low.
- Derive effort and costs from work. Reconcile person-months and totals across
  partners, work packages, Part A, Part B and applicable budget annexes. Verify
  cost rules, rates and justifications instead of balancing arbitrary partner
  shares. Keep each partner's budget values in its own `.tex` file.
- Treat the arithmetic documented in [part-a.md](part-a.md#budget-arithmetic)
  as the implemented model for the supported categories. Check whether the
  selected call requires other categories or calculations before declaring the
  budget complete. Preserve decimal arithmetic and the distinction between
  supplied values, expected calculations and incomplete totals.
- For lump-sum calls, use the required budget method and spreadsheet. Make
  work-package completion assessable and consider reporting periods without
  fragmenting the work into artificial micro-packages. Completion of agreed
  work is distinct from guaranteed scientific success; the standard
  reimbursement calculation does not establish a lump-sum award.

Apply lump-sum requirements only when that funding model applies.
The template's budget checks support drafting; they do not replace
the required call-specific budget form or an institutional budget review.

## 8. Integrate cross-cutting requirements into the work

- Address sex and gender analysis in research content where required, with a
  reasoned explanation where not relevant. Keep this distinct from team gender
  balance and institutional Gender Equality Plan eligibility. Verify each
  separately using the applicable [gender guidance][gender].
- Integrate social sciences and humanities, interdisciplinarity, stakeholder
  co-design and end-user participation when relevant or required. State who
  contributes, how their input changes decisions and which tasks/resource
  allocations support their involvement.
- Make open science and research-output management concrete: reproducibility,
  repositories, FAIR data, access conditions and responsibilities. FAIR does
  not mean unrestricted public access. Explain justified restrictions and
  follow the call's data-management planning requirements without inventing
  submission annexes.
- Identify ethics, personal-data, security and misuse issues arising from the
  actual activities. Align answers in `part-a/ethics/` with Part B safeguards and
  declarations. State required approvals, responsible roles and timing;
  describe existing approvals only when evidenced. Check the applicable
  ethics self-assessment requirements.
- Check additional topic conditions, such as multi-actor participation,
  standardisation, international cooperation or policy obligations. Translate
  applicable requirements into tasks, resources and evidence, not generic
  compliance paragraphs.
- Refer unresolved legal, ethical and financial interpretations to the relevant
  institutional specialists. Do not certify compliance on their behalf.

## 9. Write for evaluation and check the whole application

- Follow the call's exact headings, instructions and required tables. Put each
  answer where evaluators expect it, keep cross-references precise and avoid
  repeating the same pitch across sections.
- Prefer specific statements of who will do what, why, how and by when.
  Explain specialised terms and replace inflated adjectives with identifiable
  contributions or mechanisms.
- Use diagrams, Gantt charts, dependency maps and tables where they clarify
  the project. Keep labels, dates and figures consistent with text and budget.
- After substantive edits, check every affected objective, work package, task,
  result, deliverable, milestone, risk, partner role, indicator and cost.
  Maintain stable identifiers and one authoritative value for shared facts.
- Conduct a separate critical review against the actual evaluation form.
  Identify weaknesses with evidence from the draft and propose concrete fixes.
  Do not assume evaluators will infer missing content or that grant preparation
  will repair a weak plan. A mock score is provisional and requires human judgement.
- Apply anonymity rules only where the call requires them. Reconcile partner
  numbering, duration, abstract, requested funding and declarations across parts.
  Keep essential answers self-contained; external links cannot replace required
  proposal content.

### Draft checks and finalisation

1. Run `make` after substantive text/layout changes to build both parts in
   guidance and clean modes. Inspect the affected rendered pages for clipping,
   lost text, unreadable tables, broken references and poor page breaks.
2. Run `make check` for drafting validation: administrative types/lengths,
   budget arithmetic, both clean PDFs and the applicable full Part B page cap.
   Blank fields are intentionally accepted at this stage.
3. Use `make check-admin` and `make check-budget` to diagnose affected values.
   Administrative counts follow the normalisation described in `part-a.md`;
   unresolved commands make a count uncertain. Use `scripts/count_chars.py`
   for exact literal UTF-8 text when transferring a field to the Portal.
4. When the author requests completeness review, run `make strict`. It checks
   known mandatory administrative and budget inputs and intentionally fails
   an unfinished template. Keep it outside the blank template's CI release gate.
5. Before preparing final submission files, resolve narrative placeholders,
   missing evidence and all required call-specific answers/annexes. Rebuild
   clean files and inspect them. Hiding guidance or passing `make strict` does
   not establish that Part B has no placeholders, every conditional Portal
   field is covered, or the project meets all substantive call requirements.
6. Recheck ethics/security references to the final Part B page numbers.
   Verify the actual files and field values to be submitted, using the Portal's
   applicable checks and the consortium's responsible reviewers.

Retain the reusable blank scaffold when maintaining the generic template;
finalisation applies to an authored application. The local Part A PDF supports
coordination and transfer to the online administrative form. Do not treat it
as a replacement for completing that form.

## 10. AI use and handoff

- Keep an accurate record of AI tools used, their purposes and supporting
  sources so applicants can satisfy the actual template's disclosure
  instructions. Use existing project records or TeX comments; do not introduce
  another mandatory authoring interface. Human applicants validate the content
  and retain responsibility. AI review does not establish eligibility or
  funding prospects.
- Protect confidential partner information, unpublished results and personal
  data. Use approved tools and safeguards; do not upload protected material to
  unapproved external services. Check the applicable requirements for
  responsible AI use.
- Report what changed, which call documents and inputs were checked, remaining
  gaps and who must resolve them. Distinguish a concept draft, a complete draft
  and files that passed the stated final checks.
- Prepare reviewable files within the requested scope. Contacting partners,
  making institutional declarations and submitting through the Portal require
  explicit user authorisation; respect authorisation already given.

[exploitation]: https://research-and-innovation.ec.europa.eu/strategy/dissemination-and-exploitation-research-results_en
[gender]: https://rea.ec.europa.eu/gender-eu-research-and-innovation_en
