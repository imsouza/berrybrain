---
id: sciref-database-lookup-drugbank
name: "Scientific Ref: DrugBank APIs"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): DrugBank APIs"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup drugbank"
  - "drugbank apis"
keywords:
  - "database"
  - "lookup"
  - "drugbank"
  - "specialized"
  - "scientific"
  - "reference"
---

# DrugBank APIs

DrugBank requires licensed API access; a website account does not imply an API
subscription. Use the product and quota authorized for your key.

For drug/target research, the [Discovery API](https://docs.drugbank.com/discovery/v1/)
base is `https://api.drugbank.com/discovery/v1`. Server-side authentication is
`Authorization: <DRUGBANK_API_KEY>` without a Bearer prefix. Responses are JSON.

| GET path | Purpose |
|---|---|
| `/drugs/DB00316` | Drug details |
| `/drugs?q=acetaminophen` | Search drugs |
| `/drugs/DB00316/bonds` | Target, enzyme, carrier and transporter bonds |
| `/bonds/targets` | Target bonds |
| `/polypeptides/P49189/bonds` | Bonds involving a UniProt protein |

Illustrative authenticated request (not executed):
```bash
curl --fail-with-body 'https://api.drugbank.com/discovery/v1/drugs/DB00316/bonds' \
  -H "Authorization: $DRUGBANK_API_KEY"
```

Bond responses are arrays with type, bio-entity, actions and references. Preserve
organism, action direction and evidence; a listed bond need not prove efficacy.

[Clinical API](https://docs.drugbank.com/v1/) calls use `https://api.drugbank.com/v1`
and a different endpoint catalogue (including `/ddi`). Do not move Discovery
routes under that base. Browser applications require short-lived tokens issued
by a trusted backend; never embed the secret API key in a browser.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

