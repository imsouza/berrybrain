---
id: sciref-treatment-plans-readme
name: "Scientific Ref: Treatment-Plan Documentation References"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (treatment-plans): Treatment-Plan Documentation References"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "treatment plans readme"
  - "treatment-plan documentation references"
keywords:
  - "treatment"
  - "plans"
  - "readme"
  - "specialized"
  - "scientific"
  - "reference"
---

# Treatment-Plan Documentation References

These references support a documentation-only workflow. They do not contain disease-specific treatment guidance and do not authorize clinical use.

Read in this order:

1. `safety_scope.md` — hard boundary, refusal rules, emergency routing, and accountable roles.
2. `privacy_governance.md` — local-only handling, minimum-necessary practice, de-identification limits, and report minimization.
3. `documentation_workflow.md` — package lifecycle, deterministic checks, sign-off, and release gates.
4. `source_boundaries.md` — FDA labeling, Medication Guide, REMS, CMS, and official reporting boundaries.
5. `shared_decision_handoff.md` — shared-decision records, transitions, reconciliation, and ownership.
6. `source_ledger.md` — authoritative sources reviewed on 2026-10-01.
7. `security_validation.md` — historical security findings and current local validation.

## Governing rule

Only format information already supplied and verified by authorized licensed professionals. Missing or conflicting clinical content remains unresolved and is routed back to the responsible professional.

The bundled scripts perform structural, traceability, completeness, privacy-process, date, and consistency checks. They do not establish clinical correctness, medical necessity, safety, effectiveness, regulatory status, legal compliance, privacy compliance, or fitness for care.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

