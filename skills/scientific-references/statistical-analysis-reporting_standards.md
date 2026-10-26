---
id: sciref-statistical-analysis-reporting-standards
name: "Scientific Ref: Statistical Reporting Standards"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (statistical-analysis): Statistical Reporting Standards"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "statistical analysis reporting standards"
  - "estatistica analise reporting standards"
  - "statistical reporting standards"
keywords:
  - "statistical"
  - "analysis"
  - "reporting"
  - "standards"
  - "estatistica"
  - "analise"
  - "specialized"
  - "scientific"
  - "reference"
---

# Statistical Reporting Standards

All numerical prose examples here are illustrative formatting templates, not computed results from a common dataset. Replace numbers, software versions, priors and diagnostic claims with the actual analysis.

This document provides guidelines for reporting statistical analyses according to APA (American Psychological Association) style and general best practices for academic publications.

## General Principles

1. **Transparency**: Report enough detail for replication
2. **Completeness**: Include all planned analyses and outcomes
3. **Honesty**: Report non-significant findings and violations
4. **Clarity**: Write for your audience, define technical terms
5. **Reproducibility**: Provide code, data, or supplements when possible

---

## Pre-Registration and Planning

### What to Report (Ideally Before Data Collection)

1. **Hypotheses**: Clearly stated, directional when appropriate
2. **Sample size justification**: Power analysis or other rationale
3. **Data collection stopping rule**: When will you stop collecting data?
4. **Variables**: All variables collected (not just those analyzed)
5. **Exclusion criteria**: Rules for excluding participants/data points
6. **Statistical analyses**: Planned tests, including:
   - Primary analysis
   - Secondary analyses
   - Exploratory analyses (labeled as such)
   - Handling of missing data
   - Multiple comparison corrections
   - Assumption checks

**Why pre-register?**
- Prevents HARKing (Hypothesizing After Results are Known)
- Distinguishes confirmatory from exploratory analyses
- Increases credibility and reproducibility

**Platforms**: OSF, AsPredicted, ClinicalTrials.gov

---

## Methods Section

### Participants

**What to report**:
- Total N, including excluded participants
- Relevant demographics (age, gender, etc.)
- Recruitment method
- Inclusion/exclusion criteria
- Attrition/dropout with reasons

**Example**:
> "Participants were 150 undergraduate students (98 female, 52 male; M_age = 19.4 years, SD = 1.2, range 18-24) recruited from psychology courses in exchange for course credit. Five participants were excluded due to incomplete data (n = 3) or failing attention checks (n = 2), resulting in a final sample of 145."

### Design

**What to report**:
- Study design (between-subjects, within-subjects, mixed)
- Independent variables and levels
- Dependent variables
- Control variables/covariates
- Randomization procedure
- Blinding (single-blind, double-blind)

**Example**:
> "A 2 (feedback: positive vs. negative) × 2 (timing: immediate vs. delayed) between-subjects factorial design was used. Participants were randomly assigned to conditions using a computer-generated randomization sequence. The primary outcome was task performance measured as number of correct responses (0-20 scale)."

### Measures

**What to report**:
- Full name of measure/instrument
- Number of items
- Scale/response format
- Scoring method
- Reliability (Cronbach's α, ICC, etc.)
- Validity evidence (if applicable)

**Example**:
> "Depression was assessed using the Beck Depression Inventory-II (BDI-II; Beck et al., 1996), a 21-item self-report measure rated on a 4-point scale (0-3). Total scores range from 0 to 63, with higher scores indicating greater depression severity. The BDI-II demonstrated excellent internal consistency in this sample (α = .91)."

### Procedure

**What to report**:
- Step-by-step description of what participants did
- Timing and duration
- Instructions given
- Any manipulations or interventions

**Example**:
> "Participants completed the study online via Qualtrics. After providing informed consent, they completed demographic questions, were randomly assigned to one of four conditions, completed the experimental task (approximately 15 minutes), and finished with the outcome measures and debriefing. The entire session lasted approximately 30 minutes."

### Data Analysis

**What to report**:
- Software used (with version)
- Significance level (α)
- Tail(s) of tests (one-tailed or two-tailed)
- Assumption checks conducted
- Missing data handling
- Outlier treatment
- Multiple comparison corrections
- Effect size measures used

**Example**:
> "All analyses were conducted using Python 3.12 with Pingouin 0.7.0, SciPy 1.18.1, and statsmodels 0.15.0. An alpha level of .05 was used for all significance tests. Assumptions of normality and homogeneity of variance were assessed using Shapiro-Wilk and Levene's tests, respectively. Missing data (< 2% for all variables) were handled using listwise deletion. Flagged observations were reviewed against source records; valid observations were retained, with prespecified robust sensitivity analyses. For the primary ANOVA, partial eta-squared (η²_p) is reported as the effect size measure. Post hoc comparisons used Tukey's HSD to control family-wise error rate."

---

## Results Section

### Descriptive Statistics

**What to report**:
- Sample size (for each group if applicable)
- Measures of central tendency (M, Mdn)
- Measures of variability (SD, IQR, range)
- Confidence intervals (when appropriate)

**Example (continuous outcome)**:
> "Group A (n = 48) had a mean score of 75.2 (SD = 8.5, 95% CI [72.7, 77.7]), while Group B (n = 52) scored 68.3 (SD = 9.2, 95% CI [65.7, 70.9])."

**Example (categorical outcome)**:
> "Of the 145 participants, 89 (61.4%) chose Option A, 42 (29.0%) chose Option B, and 14 (9.7%) chose Option C."

**Tables for descriptive statistics**:
- Use tables for multiple variables or groups
- Include M, SD, and n (minimum)
- Can include range, skewness, kurtosis if relevant

---

### Assumption Checks

**What to report**:
- Which assumptions were tested
- Results of diagnostic tests
- Evidence of departures, and limits of the checks
- Actions taken if violated

**Example**:
> "Normality was assessed using Shapiro-Wilk tests. Data for Group A (W = 0.97, p = .18) and Group B (W = 0.96, p = .12) did not significantly deviate from normality. The median-centered Levene screen did not reject equal variances, F(1, 98) = 1.23, p = .27. Non-rejection did not establish equality; prespecified Welch inference was retained, with Q-Q plots and design reviewed."

**Example (violated)**:
> "Shapiro-Wilk tests indicated significant departure from normality for Group C (W = 0.89, p = .003). The prespecified estimand and tail behavior were reviewed; any alternative rank analysis was labeled as a separate distributional sensitivity analysis, not a replacement mean test se

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

