---
id: sciref-research-grants-nih-guidelines
name: "Scientific Ref: NIH application guidance"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (research-grants): NIH application guidance"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "research grants nih guidelines"
  - "pesquisa grants nih guidelines"
  - "nih application guidance"
keywords:
  - "research"
  - "grants"
  - "nih"
  - "guidelines"
  - "pesquisa"
  - "specialized"
  - "scientific"
  - "reference"
  - "application"
---

# NIH application guidance

Reviewed 2026-10-01. Start from a specific active NOFO, its amendments, related NIH
Guide notices, due date, activity code, and application form package. Since October
2025, [Grants.gov is the official source of NIH funding opportunities](https://www.grants.nih.gov/funding/explore-nih-opportunities);
the NIH Guide continues to carry policy notices. An old Guide NOFO or a RePORTER award
is not proof of current availability or eligibility.

## Appropriate assistance and applicant ownership

[NIH policy](https://grants.nih.gov/grants/policy/nihgps/HTML5/section_2/2.3.7_policies_affecting_applications.htm)
permits limited AI assistance but will not consider applications, or sections,
substantially developed by AI to be applicants' original ideas. Use this skill to
extract requirements, critique investigator-authored material, check consistency and
calculations, and suggest limited edits. Keep the scientific ideas, interpretation,
and substantive application development with the applicant; human review alone does
not erase the policy. Never invent preliminary findings, citations, collaborators,
patient access, credentials, or commitments. The same policy section limits an
individual PD/PI or MPI to six covered applications per council calendar year, with
specified activity-code exclusions; verify how the limit applies before planning
multiple submissions.

## Review framework

For most research project grants with due dates on/after January 25, 2025, use the
[simplified review framework](https://www.grants.nih.gov/policy-and-compliance/policy-topics/peer-review/simplifying-review/framework):

| Factor | Applicant's evidence | Assessment |
| --- | --- | --- |
| Importance of the Research | Important gap and contribution; significance and innovation | 1-9 |
| Rigor and Feasibility | Design, analysis, sample-size justification, bias control, alternatives, timeline | 1-9 |
| Expertise and Resources | Project-specific capabilities, facilities, access and missing expertise | Sufficiency, not a separate numeric score |

All three affect overall impact. This is not a weighted average. Additional review
criteria, including applicable human-subject and animal protections, may affect
impact despite lacking standalone scores; budget appropriateness is a different
review consideration. Check Section V of the NOFO: fellowships, K awards, small
business, and complex multi-project mechanisms need their own review instructions.
The research narrative still uses Significance, Innovation, and Approach where the
application instructions require them; do not rename these to the review factors.

[NOT-OD-26-114](https://grants.nih.gov/grants/guide/notice-files/NOT-OD-26-114.html)
continues modified practices for the January 2027 Advisory Council: most meetings
discuss 30-35% of applications; a middle category is competitive but not discussed.
Such applications can still be considered for funding. Summary statements are
simplified. Do not promise that half will be discussed or classify an application as
unfundable solely because it was not discussed. Overall impact scores for discussed
applications normally run 10-90; do not map a score to an agency-wide funding chance.

## Narrative and attachments

Use the [current page-limit table](https://grants.nih.gov/grants-process/write-application/how-to-apply-application-guide/page-limits)
and the NOFO. For standard R01 applications, Specific Aims is **up to one page** and
Research Strategy up to 12; for standard R03/R21 the strategy is generally six. The
Project Summary/Abstract is generally at most 30 lines, and Project Narrative at most
three sentences. These are maxima, not required exact lengths or interchangeable
components. Check exceptions rather than shrinking type to fit.

An aims page should connect the gap, objective, investigator's hypothesis or research
question, achievable aims, expected knowledge, and impact. Two or three aims may work
well, but NIH has no universal required number. Avoid making all later aims depend on
one uncertain result; state alternatives. See [specific_aims_guide.md](specific_aims_guide.md)
for illustrative writing patterns, not a ready-to-submit application.

For the research strategy:

1. **Significance:** identify the important barrier and what resolving it changes.
   Cite the strengths and limitations of prior evidence, not just disease burden.
2. **Innovation:** explain the actual conceptual or technical advance. Do not claim
   that all worthwhile NIH research must be revolutionary.
3. **Approach:** connect each aim to design, subjects/models, controls, randomization
   and blinding where appropriate, sample-size rationale, analysis, quality controls,
   plausible outcomes, pitfalls, alternatives, resources, and a realistic timeline.
   Separate observed preliminary results from predictions. Do not present a power
   calculation as meaningful without its effect-size/variance assumptions.

Follow [attachment requirements](https://www.grants.nih.gov/grants-process/write-application/how-to-apply-application-guide/format-attachments):
PDF; ordinarily at least 11-point body text, no more than 15 characters per horizontal
inch or six lines per vertical inch, and at least half-inch margins. Smaller graphic
text may be acceptable if legible at 100%. Check searchable text, embedded fonts,
filenames and file limits in the actual package. Do not put overflow narrative in
appendices or hyperlinks. Preserve SciENcv-generated certification in its PDF instead
of printing or altering it to imitate a manually formatted attachment.

## Common Forms, disclosures, and data sharing

For application due dates and relevant JIT/RPPR/prior-approval submissions on/after
January 25, 2026, NIH requires Common Forms; enforcement began May 8, 2026.
Use [SciENcv for the Biographical Sketch Common Form and NIH Supplement](https://www.grants.nih.gov/grants-process/write-application/forms-directory/biographical-sketch-common-form)
and the Current and Pending (Other) Support Common Form. There is no downloadable
blank substitute for the SciENcv biosketch. Each investigator must review and certify
accurate records, supply the required ORCID linkage to eRA Commons, and follow the
current field limits. Do not reuse the retired five-page Word biosketch format.
Other Support includes applicable external support and in-kind resources; reconcile
scientific, budgetary, and commitment overlap with the actual instructions.

For data-g

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

