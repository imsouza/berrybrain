---
id: sci-research-grants
name: "Scientific: research-grants"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Supports research proposal preparation and review for NSF, NIH, DOE, DARPA, and Taiwan NSTC, including opportunity-specific requirements, aims, review criteria, budgets, broader impacts, forms, and resubmissions. Use for investigator-authored grant development, compliance matrice"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "research grants"
  - "pesquisa grants"
  - "research-grants"
keywords:
  - "research"
  - "grants"
  - "pesquisa"
  - "supports"
  - "proposal"
  - "preparation"
  - "review"
  - "darpa"
---

# Research Grant Writing

## Overview

Research grant writing is the process of developing competitive funding proposals for federal agencies and foundations. Master agency-specific requirements, review criteria, narrative structure, budget preparation, and compliance for NSF (National Science Foundation), NIH (National Institutes of Health), DOE (Department of Energy), DARPA (Defense Advanced Research Projects Agency), and Taiwan's NSTC (National Science and Technology Council) submissions.

**Critical Principle: Grants are persuasive documents that must simultaneously demonstrate scientific rigor, innovation, feasibility, and broader impact.** Each agency has distinct priorities, review criteria, formatting requirements, and strategic goals that must be addressed.

## When to Use This Skill

This skill should be used when:
- Writing research proposals for NSF, NIH, DOE, DARPA, or NSTC programs
- Preparing project descriptions, specific aims, or technical narratives
- Developing broader impacts or significance statements
- Creating research timelines and milestone plans
- Preparing budget justifications and personnel allocation plans
- Responding to program solicitations or funding announcements
- Addressing reviewer comments in resubmissions
- Planning multi-institutional collaborative proposals
- Writing preliminary data or feasibility sections
- Preparing biosketches, CVs, or facilities descriptions

## Establish the governing opportunity first

For each task, record agency, opportunity identifier and amendment, activity/project
type, due date/time zone, eligibility, submission stage, application form version,
limits, required attachments, review criteria and source URL/retrieval date. Check
current notices as well as the original solicitation. An archived call, funded award,
or budget announcement does not establish live funding availability. If the official
package is unavailable, provide a bounded drafting review and list unresolved rules.

Build a requirement -> source section -> draft location -> gap matrix before judging
compliance. Templates in `assets/` are illustrative worksheets, not official forms.
Never invent data, citations, investigator records, partner commitments or approvals.
Inspect the final exported files; Markdown text does not establish page compliance.

For NIH, use this skill for requirements, critique, consistency checks and limited
editing of investigator-authored material. [NIH policy](https://grants.nih.gov/grants/policy/nihgps/HTML5/section_2/2.3.7_policies_affecting_applications.htm)
excludes applications or sections substantially developed by AI. Preserve applicant
ownership of substantive science and writing; review or disclosure alone does not
make substantial AI authorship compliant. Apply other agencies' current rules too.

## Visual Enhancement (Optional)

Strong proposals often include 1–3 figures (timelines, workflow diagrams, preliminary data). Figures support review but are not a substitute for clear aims and methods.

**When figures help:**
- Research methodology and workflow diagrams
- Project timeline or Gantt charts
- Conceptual framework or system architecture (technical proposals)
- Experimental design flowcharts
- Broader impacts activity diagrams
- NSTC CM03 research architecture diagrams when they clarify the proposed methods

**How to create figures:**
- **Preferred:** Use the **scientific-schematics** skill (`--doc-type grant`) for AI-generated diagrams from a natural-language description
- **Alternative:** Build figures in your usual tools (matplotlib, Illustrator, PowerPoint, etc.)

Illustrative optional integration (CLI options checked; no paid generation tested in this refresh). Run from the repository root, with `OPENROUTER_API_KEY` set:

```bash
python skills/scientific-schematics/scripts/generate_schematic.py "project timeline with Year 1-3 milestones" -o figures/timeline.png --doc-type grant
```

**Disclosure:** AI schematic generation sends your prompt to [OpenRouter](https://openrouter.ai/) (a third-party API). Do not include unpublished sensitive details unless that transmission is appropriate for your project.

---

## Agency-Specific Overview

### NSF (National Science Foundation)
**Mission**: Promote the progress of science and advance national health, prosperity, and welfare

**Key Features**:
- Use the [current PAPPG index](https://www.nsf.gov/policies/pappg), effective supplements and solicitation; as reviewed, NSF 24-1 is supplemented by NSF 26-200 and 26-202
- Intellectual Merit + Broader Impacts both receive full consideration; no universal numerical weighting
- 15-page project description limit (most programs; includes Results from Prior NSF Support, max 5 pages)
- Education and societal benefit, with activities aligned to current NSF priorities and the solicitation
- Collaborative research encouraged
- Current SciENcv Common Forms, graduate/postdoc mentoring, and Research.gov DMSP tool requirements
- Merit review process with panel + ad hoc reviewers

### NIH (National Institutes of Health)
**Mission**: Enhance health, lengthen life, and reduce illness and disability

**Key Features**:
- Standard R01: Specific Aims up to 1 page and Research Strategy up to 12; verify the NOFO
- Most RPGs use Importance, Rigor/Feasibility, and Expertise/Resources review factors; required narrative headings remain Significance, Innovation, Approach
- Preliminary evidence normally supports R01 feasibility; follow the mechanism-specific instructions
- Rigor and reproducibility; SciENcv Common Forms and NIH Supplement required under the 2026 implementation
- For eligible applications, modular budgets use **$25,000 increments**, up to **$250,000 in direct costs per budget period**, excluding consortium F&A; verify the NOFO and organization eligibility. See [NIH budget guidance](https://grants.nih.gov/grants/developing_budget.htm).
- NIH permits **one resubmission (A1)** of an unfunded application, within 37 months of the initial application due date when the NOFO permits resubmissions; see [resubmission policy](https://grants.nih.gov/grants-process/submit/submission-policies/resubmission-applications).

### DOE (Department of Energy)
**Mission**: Ensure America's security and prosperity through energy, environmental, and nuclear challenges

**Key Features**:
- Focus on energy, climate, computational science, basic energy sciences
- Cost sharing and partnerships depend on the specific office, NOFO, and award instrument
- Emph

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

