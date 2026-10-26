---
id: fabric-create-story-about-people-interaction
name: "Pattern: Create Story About People Interaction"
category: cognitive-pattern
source_repo: danielmiessler/fabric
description: "You will be provided with information about **two individuals** (real or fictional). The input will be **delimited by triple backticks**. This information may include personality traits, habits, fears, motivations, strengths, weaknesses, ba"
priority_tier: 2
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "create story about people interaction"
  - "criar story about people interaction"
keywords:
  - "create"
  - "story"
  - "about"
  - "people"
  - "interaction"
  - "criar"
  - "provided"
  - "information"
  - "individuals"
  - "real"
  - "fictional"
---

### Prompt

You will be provided with information about **two individuals** (real or fictional). The input will be **delimited by triple backticks**. This information may include personality traits, habits, fears, motivations, strengths, weaknesses, background details, or recognizable behavioral patterns. Your task is as follows:

#### Step 1 – Psychological Profiling
- Carefully analyze the input for each person.
- Construct a **comprehensive psychological profile** for each, focusing not only on their conscious traits but also on possible **unconscious drives, repressed tendencies, and deeper psychological landscapes**.
- Highlight any contradictions, unintegrated traits, or unresolved psychological dynamics that emerge.

#### Step 2 – Comparative Analysis
- Compare and contrast the two profiles.
- Identify potential areas of **tension, attraction, or synergy** between them.
- Predict how these psychological dynamics might realistically manifest in interpersonal interactions.

#### Step 3 – Story Construction
- Write a **fictional narrative** in which these two characters are the central figures.
- The story should:
  - Be driven primarily by their interaction.
  - Reflect the **most probable and psychologically realistic outcomes** of their meeting.
  - Allow for either conflict, cooperation, or a mixture of both—but always in a way that is **meaningful and character-driven**.
- Ensure the plot feels **grounded, believable, and true to their psychological makeup**, rather than contrived.

#### Formatting Instructions
- Clearly separate your response into three labeled sections:
  1. **Profile A**
  2. **Profile B**
  3. **Story**

---

**User Input Example (delimited by triple backticks):**

```
Person A: Highly ambitious, detail-oriented, often perfectionistic. Has a fear of failure and tends to overwork. Childhood marked by pressure to achieve. Secretly desires freedom from expectations.
Person B: Warm, empathetic, values relationships over achievement. Struggles with self-assertion, avoids conflict. Childhood marked by neglect. Desires to be seen and valued. Often represses anger.
```

# INPUT

INPUT:

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

