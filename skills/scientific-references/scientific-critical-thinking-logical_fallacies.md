---
id: sciref-scientific-critical-thinking-logical-fallacies
name: "Scientific Ref: Logical Fallacies in Scientific Discourse"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-critical-thinking): Logical Fallacies in Scientific Discourse"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific critical thinking logical fallacies"
  - "cientifico critica pensamento logical fallacies"
  - "logical fallacies in scientific discourse"
keywords:
  - "scientific"
  - "critical"
  - "thinking"
  - "logical"
  - "fallacies"
  - "cientifico"
  - "critica"
  - "pensamento"
  - "specialized"
  - "reference"
---

# Logical Fallacies in Scientific Discourse

The examples are illustrative arguments, not clinical claims or evidence about a named
study. Critique the inferential step; a fallacious argument does not make its conclusion
false. Methodological sources are in [review_sources.md](review_sources.md).

## Fallacies of Causation

### 1. Post Hoc Ergo Propter Hoc (After This, Therefore Because of This)
**Description:** Assuming that because B happened after A, A caused B.

**Examples:**
- "I took this supplement and my cold went away, so the supplement cured my cold."
- "Autism diagnoses increased after vaccine schedules changed, so vaccines cause autism."
- "I wore my lucky socks and won the game, so the socks caused the win."

**Why fallacious:** Temporal sequence is necessary but not sufficient for causation. Correlation ≠ causation.

**Related:** *Cum hoc ergo propter hoc* (with this, therefore because of this) - correlation mistaken for causation even without temporal order.

### 2. Confusing Correlation with Causation
**Description:** Assuming correlation implies direct causal relationship.

**Examples:**
- "Countries that eat more chocolate have more Nobel Prize winners, so chocolate makes you smarter."
- "Ice cream sales correlate with drowning deaths, so ice cream causes drowning."

**Reality:** Often due to confounding variables (hot weather causes both ice cream sales and swimming).

### 3. Reverse Causation
**Description:** Confusing cause and effect direction.

**Examples:**
- "Depression is associated with inflammation, so inflammation causes depression." (Could be: depression causes inflammation)
- "Wealthy people are healthier, so wealth causes health." (Could be: health enables wealth accumulation)

**Solution:** Establish temporal order and assess confounding, selection, and measurement;
longitudinal observation alone does not identify a causal direction.

### 4. Single Cause Fallacy
**Description:** Attributing complex phenomena to one cause when multiple factors contribute.

**Examples:**
- "Crime is caused by poverty." (Ignores many other contributing factors)
- "Heart disease is caused by fat intake." (Oversimplifies multifactorial disease)

**Reality:** Most outcomes have multiple contributing causes.

## Fallacies of Generalization

### 5. Hasty Generalization
**Description:** Drawing broad conclusions from insufficient evidence.

**Examples:**
- "My uncle smoked and lived to 90, so smoking isn't dangerous."
- "This drug worked in 5 patients, so it's effective for everyone."
- "I saw three black swans, so all swans are black."

**Why fallacious:** Small, unrepresentative samples don't support universal claims.

### 6. Anecdotal Fallacy
**Description:** Using personal experience or isolated examples as proof.

**Examples:**
- "I know someone who survived cancer using alternative medicine, so it works."
- "My grandmother never exercised and lived to 100, so exercise is unnecessary."

**Why fallacious:** Anecdotes are observations, but selection, memory, and missing comparators
usually prevent the claimed general or causal inference. Do not dismiss a safety signal
merely because it begins with a case report.

### 7. Cherry Picking (Suppressing Evidence)
**Description:** Selecting only evidence that supports your position while ignoring contradictory evidence.

**Examples:**
- Citing only studies showing supplement benefits while ignoring null findings
- Highlighting successful predictions while ignoring failed ones
- Showing graphs that start at convenient points

**Detection:** Look for systematic reviews, not individual studies.

### 8. Ecological Fallacy
**Description:** Inferring individual characteristics from group statistics.

**Example:**
- "Average income in this neighborhood is high, so this person must be wealthy."
- "This country is richer and has less disease, so its richer individuals must have less disease."

**Why fallacious:** Group-level patterns don't necessarily apply to individuals.

## Fallacies of Authority and Tradition

### 9. Appeal to Authority (Argumentum ad Verecundiam)
**Description:** Accepting claims because an authority figure said them, without evidence.

**Examples:**
- "Dr. X says this treatment works, so it must." (If Dr. X provides no data)
- "Einstein believed in God, so God exists." (Einstein's physics expertise doesn't transfer)
- "99% of doctors recommend..." (Appeal to majority + authority without evidence)

**Valid use of authority:** Experts providing evidence-based consensus in their domain.

**Invalid:** Authority opinions without evidence, or outside their expertise.

### 10. Appeal to Antiquity/Tradition
**Description:** Assuming something is true or good because it's old or traditional.

**Examples:**
- "Traditional medicine has been used for thousands of years, so it must work."
- "This theory has been accepted for decades, so it must be correct."

**Why fallacious:** Age doesn't determine validity. Many old beliefs have been disproven.

### 11. Appeal to Novelty
**Description:** Assuming something is better because it's new.

**Examples:**
- "This is the latest treatment, so it must be superior."
- "New research overturns everything we knew." (Often overstated)

**Why fallacious:** New ≠ better. Established treatments often outperform novel ones.

## Fallacies of Relevance

### 12. Ad Hominem (Attack the Person)
**Description:** Attacking the person making the argument rather than the argument itself.

**Types:**
- **Abusive:** "He's an idiot, so his theory is wrong."
- **Circumstantial:** "She's funded by industry, so her findings are false."
- **Tu Quoque:** "You smoke, so your anti-smoking argument is invalid."

**Why fallacious:** Personal characteristics don't determine argument validity.

**Note:** Conflicts of interest are worth noting but don't invalidate evidence.

### 13. Genetic Fallacy
**Description:** Judging something based on its origin rather than its merits.

**Examples:**
- "This idea came from a drug company, so it's wrong."
- "Ancient Greeks believed this, so it's outdated."

**Better approach:** Evaluate evidence regardless of source.

### 14. Appeal to Emotion
**Description:** Manipulating emotions instead of presenting evidence.

**Types:**
- **Appeal to fear:** "If you don't vaccinate, your child will die."
- **Appeal to pity:** "Think of the suffering patients who need this unproven treatment."
- **Appeal to flattery:** "Smart people like you know that..."

**Why fallacious:** Emotional r

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

