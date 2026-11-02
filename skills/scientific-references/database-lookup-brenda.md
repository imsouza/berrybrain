---
id: sciref-database-lookup-brenda
name: "Scientific Ref: BRENDA Enzyme Database (SOAP API)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): BRENDA Enzyme Database (SOAP API)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup brenda"
  - "brenda enzyme database (soap api)"
keywords:
  - "database"
  - "lookup"
  - "brenda"
  - "specialized"
  - "scientific"
  - "reference"
---

# BRENDA Enzyme Database (SOAP API)

## Important: BRENDA uses SOAP, not REST. Requires Python with `zeep` library.

## SOAP Endpoint
```
https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl
```

## Auth
Free registration required at https://www.brenda-enzymes.org/register.php
Credentials (email + SHA-256 hashed password) passed with every call.

## Key SOAP Methods

All methods take `email`, `password` (SHA-256), and `ecNumber` as base parameters.

| Method | Description |
|--------|-------------|
| `getKmValue` | Michaelis constant (Km) |
| `getTurnoverNumber` | Turnover number (kcat) |
| `getKcatKmValue` | Catalytic efficiency (kcat/Km) |
| `getKiValue` | Inhibition constant (Ki) |
| `getIc50Value` | IC50 values |
| `getSpecificActivity` | Specific activity |
| `getPhOptimum` | pH optimum |
| `getTemperatureOptimum` | Temperature optimum |
| `getSubstrate` | Substrates |
| `getProduct` | Products |
| `getInhibitors` | Inhibitors |
| `getCofactor` | Cofactors |
| `getOrganism` | Source organisms |
| `getReaction` | Reaction equations |
| `getSequence` | Protein sequences |
| `getDisease` | Associated diseases |

## Parameter Syntax
`fieldName*value` format. Empty value = return all.

```
ecNumber*1.1.1.1           # Required: EC number
organism*Homo sapiens      # Optional: filter by organism
substrate*ethanol          # Optional: filter by substrate
kmValue*                   # Return field (empty = all)
```

## Python Example
```python
import hashlib
from zeep import Client

client = Client("https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl")
email = "your@email.com"
password = hashlib.sha256("your_password".encode()).hexdigest()

# Get Km values for alcohol dehydrogenase
result = client.service.getKmValue(
    email, password,
    "ecNumber*1.1.1.1", "organism*Homo sapiens",
    "kmValue*", "kmValueMaximum*", "substrate*", "commentary*",
    "ligandStructureId*", "literature*"
)
```

## Response Format
The `brenda_zeep.wsdl` binding returns typed records, including `kmValue`,
`kmValueMaximum`, `organism`, and `substrate` for `getKmValue`. Serialize with
`zeep.helpers.serialize_object` when needed. The delimiter-separated string
format belongs to the older `brenda.wsdl` interface; do not apply that parser to
Zeep record objects. Each method has its own ordered arguments: inspect its WSDL
signature instead of reusing the Km parameter tuple for every method.

## Rate Limits
BRENDA requests at most **one request per second**. The online service is
CC BY 4.0; registration is required. The authenticated example is illustrative
and was not executed during this documentation review.

Reviewed 2026-09-30: [official SOAP help](https://www.brenda-enzymes.org/soap.php)
and the linked Zeep WSDL.

## Note for this skill
Since BRENDA uses SOAP (not REST), making calls requires writing and executing a Python script with `zeep`. Use Bash to run the script rather than WebFetch.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

