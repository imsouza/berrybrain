---
id: sciref-research-grants-readme
name: "Scientific Ref: Research-grants reference map"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (research-grants): Research-grants reference map"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "research grants readme"
  - "pesquisa grants readme"
  - "research-grants reference map"
keywords:
  - "research"
  - "grants"
  - "readme"
  - "pesquisa"
  - "specialized"
  - "scientific"
  - "reference"
---

# Research-grants reference map

Reviewed 2026-10-01. This skill supports proposal preparation and review for NSF, NIH,
DOE, DARPA and Taiwan NSTC. It is not a live opportunity database, submission service,
or source of guaranteed eligibility, deadlines or funding odds.

Start with the specific call and effective instructions, then load only the material
needed for the requested component. Preserve applicant authorship and real evidence;
NIH specifically limits substantial AI development of applications and sections.

| Need | Reference |
| --- | --- |
| NSF structure, SciENcv, mentoring, DMSP and CAREER | [nsf_guidelines.md](nsf_guidelines.md) |
| NIH review, forms, dates, budgets and A1 | [nih_guidelines.md](nih_guidelines.md) |
| DOE office/portal, stages, cost share and Common Forms | [doe_guidelines.md](doe_guidelines.md) |
| DARPA solicitation, metrics, volumes and instruments | [darpa_guidelines.md](darpa_guidelines.md) |
| NSTC CM03, division forms and institutional routing | [nstc_guidelines.md](nstc_guidelines.md) |
| Section-by-section scientific narrative | [core_components.md](core_components.md) |
| Review-factor comparison | [review_criteria.md](review_criteria.md) |
| Aims-page writing patterns | [specific_aims_guide.md](specific_aims_guide.md) |
| Broader-impact design and assessment | [broader_impacts.md](broader_impacts.md) |
| Style, evidence, coherence and alternatives | [writing_principles.md](writing_principles.md) |
| Mechanism selection and resubmission | [proposal_types_and_resubmission.md](proposal_types_and_resubmission.md) |

Templates under `assets/` are **illustrative worksheets**, not agency-approved forms:
NSF Project Summary, NIH Specific Aims, and budget justification. Delete instructions
and unverified examples before creating a deliverable. Render the final artifact to
check page limits; Markdown line count cannot establish PDF compliance.

Useful requests include: "extract the requirements from this NOFO," "critique my R01
aims against the review factors," "check effort and F&A calculations," or "map these
reviewer concerns to revisions." Each should produce a traceable requirement matrix,
critique, corrected calculation, or investigator-reviewed edits with unresolved gaps.

The skill's examples, agency names and review date do not establish that any named
program is currently accepting applications. Recheck current calls and notices for
each task, particularly NIH form transitions and NSF's supplemented PAPPG.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

