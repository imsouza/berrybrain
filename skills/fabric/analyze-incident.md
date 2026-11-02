---
id: fabric-analyze-incident
name: "Pattern: Analyze Incident"
category: cognitive-pattern
source_repo: danielmiessler/fabric
description: "Cybersecurity Hack Article Analysis: Efficient Data Extraction"
priority_tier: 2
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "analyze incident"
  - "analisar incident"
keywords:
  - "analyze"
  - "incident"
  - "analisar"
  - "cybersecurity"
  - "hack"
  - "article"
  - "analysis"
  - "efficient"
  - "extraction"
---

Cybersecurity Hack Article Analysis: Efficient Data Extraction

Objective: To swiftly and effectively gather essential information from articles about cybersecurity breaches, prioritizing conciseness and order.

Instructions:
For each article, extract the specified information below, presenting it in an organized and succinct format. Ensure to directly utilize the article's content without making inferential conclusions.

- Attack Date: YYYY-MM-DD
- Summary: A concise overview in one sentence.
- Key Details:
    - Attack Type: Main method used (e.g., "Ransomware").
    - Vulnerable Component: The exploited element (e.g., "Email system").
    - Attacker Information: 
        - Name/Organization: When available (e.g., "APT28").
        - Country of Origin: If identified (e.g., "China").
    - Target Information:
        - Name: The targeted entity.
        - Country: Location of impact (e.g., "USA").
        - Size: Entity size (e.g., "Large enterprise").
        - Industry: Affected sector (e.g., "Healthcare").
    - Incident Details:
        - CVE's: Identified CVEs (e.g., CVE-XXX, CVE-XXX).
        - Accounts Compromised: Quantity (e.g., "5000").
        - Business Impact: Brief description (e.g., "Operational disruption").
        - Impact Explanation: In one sentence.
        - Root Cause: Principal reason (e.g., "Unpatched software").
- Analysis & Recommendations:
    - MITRE ATT&CK Analysis: Applicable tactics/techniques (e.g., "T1566, T1486").
    - Atomic Red Team Atomics: Recommended tests (e.g., "T1566.001").
    - Remediation:
        - Recommendation: Summary of action (e.g., "Implement MFA").
        - Action Plan: Stepwise approach (e.g., "1. Update software, 2. Train staff").
    - Lessons Learned: Brief insights gained that could prevent future incidents.

# INPUT

INPUT:

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

