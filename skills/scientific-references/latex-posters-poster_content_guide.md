---
id: sciref-latex-posters-poster-content-guide
name: "Scientific Ref: Research Poster Content Guide"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (latex-posters): Research Poster Content Guide"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "latex posters poster content guide"
  - "research poster content guide"
keywords:
  - "latex"
  - "posters"
  - "poster"
  - "content"
  - "guide"
  - "specialized"
  - "scientific"
  - "reference"
  - "research"
---

# Research Poster Content Guide

Reviewed 2026-09-30. Design numbers are starting points, not measured guarantees.
Code fragments are illustrative; use the bundled tested templates as the executable
starting point. Replace example names, statistics, citations, URLs, and assets with
verified project content.

## Overview

Content is king in research posters. This guide covers writing strategies, section-specific guidance, visual-text balance, and best practices for communicating research effectively in poster format.

## Core Content Principles

### 1. The 3-5 Minute Rule

**Planning assumption**: Design a brief overview that can be read in 3-5 minutes
- **1 minute**: Scanning from distance (title, figures)
- **2-4 minutes**: Reading key points up close
- **5+ minutes**: Engaged conversation (if interested)

**Design Implication**: Poster must work at three levels:
1. **Distance view** (6-10 feet): Title and main figure visible
2. **Browse view** (3-6 feet): Section headers and key results readable
3. **Detail view** (1-3 feet): Full content accessible

### 2. Tell a Story, Not a Paper

**Poster ≠ Condensed Paper**

**Paper approach** (❌):
- Comprehensive literature review
- Detailed methodology
- All results presented
- Lengthy discussion
- 50+ references

**Poster approach** (✅):
- One sentence background
- Visual methods diagram
- 3-5 key results
- 3-4 bullet point conclusions
- 5-10 key references

**Story Arc for Posters**:
```
Hook (Problem) → Approach → Discovery → Impact
```

**Example**:
- **Hook**: "Antibiotic resistance threatens millions of lives annually"
- **Approach**: "We developed an AI system to predict resistance patterns"
- **Discovery**: "Our model achieves 87% accuracy, 20% better than existing methods"
- **Impact**: "Could reduce treatment failures by identifying resistance earlier"

### 3. The 800-Word Maximum

**Word Count Guidelines**:
- **Ideal**: 300-500 words
- **Maximum**: 800 words
- **Hard limit**: 1000 words (beyond this, poster is unreadable)

**Word Budget by Section**:
| Section | Word Count | % of Total |
|---------|-----------|------------|
| Introduction/Background | 50-100 | 15% |
| Methods | 100-150 | 25% |
| Results (text) | 100-200 | 25% |
| Discussion/Conclusions | 100-150 | 25% |
| References/Acknowledgments | 50-100 | 10% |

**Counting Tool**:
```bash
# TeXcount is a Perl command-line program, not a LaTeX package.
texcount -inc -sum poster.tex
```

[TeXcount](https://ctan.org/pkg/texcount) may need macro rules for poster-class
commands. Cross-check visible text and captions; text inside images is not counted.

### 4. Visual-to-Text Ratio

**Optimal Balance**: 40-50% visual content, 50-60% text+white space

**Visual Content Includes**:
- Figures and graphs
- Photos and images
- Diagrams and flowcharts
- Icons and symbols
- Color blocks and design elements

**Too Text-Heavy** (❌):
- Wall of text
- Small figures
- Intimidating to viewers
- Low engagement

**Well-Balanced** (✅):
- Clear figures dominate
- Text supports visuals
- Easy to scan
- Inviting appearance

## Section-Specific Content Guidance

### Title

**Purpose**: Capture attention, convey topic, establish credibility

**Characteristics of Effective Titles**:
- **Concise**: 10-15 words maximum
- **Descriptive**: Clearly states research topic
- **Active**: Uses strong verbs when possible
- **Specific**: Avoids vague terms
- **Jargon-aware**: Balances field-specific terms with accessibility

**Title Formulas**:

**1. Descriptive**:
```
[Method/Approach] for [Problem/Application]

Example: "Deep Learning for Early Detection of Alzheimer's Disease"
```

**2. Question**:
```
[Research Question]?

Example: "Can Microbiome Diversity Predict Treatment Response?"
```

**3. Assertion**:
```
[Finding] in [Context]

Example: "Novel Mechanism Identified in Drug Resistance Pathways"
```

**4. Colon Format**:
```
[Topic]: [Specific Approach/Finding]

Example: "Urban Heat Islands: A Machine Learning Framework for Mitigation"
```

**Avoid**:
- ❌ Generic titles: "A Study of X"
- ❌ Overly cute or clever wordplay (confuses message)
- ❌ Excessive jargon: "Utilization of CRISPR-Cas9..."
- ❌ Unnecessarily long: "Investigation of the potential role of..."

**LaTeX Title Formatting**:
```latex
% Emphasize key words with bold
\title{Deep Learning for \textbf{Early Detection} of Alzheimer's Disease}

% Two-line titles for long names
\title{Machine Learning Framework for\\Urban Heat Island Mitigation}

% Avoid ALL CAPS (harder to read)
```

### Authors and Affiliations

**Best Practices**:
- **Presenting author**: Bold, underline, or asterisk
- **Corresponding author**: Include email
- **Affiliations**: Superscript numbers or symbols
- **Institutional logos**: 2-4 maximum

**Format Examples**:
```latex
% Simple format
\author{\textbf{Jane Smith}\textsuperscript{1}, John Doe\textsuperscript{2}}
\institute{
  \textsuperscript{1}University of Example, 
  \textsuperscript{2}Research Institute
}

% With contact
\author{Jane Smith\textsuperscript{1,*}}
\institute{
  \textsuperscript{1}Department, University\\
  \textsuperscript{*}jane.smith@university.edu
}
```

### Introduction/Background

**Purpose**: Establish context, motivate research, state objective

**Structure** (50-100 words):
1. **Problem statement** (1-2 sentences): What's the issue?
2. **Knowledge gap** (1-2 sentences): What's unknown/unsolved?
3. **Research objective** (1 sentence): What did you do?

**Illustrative wording** (replace bracketed facts with current cited evidence):
```
Antibiotic resistance causes a substantial burden [cite current estimate].
The relevant diagnostic workflow requires [measured turnaround time],
delaying appropriate treatment. Machine learning offers potential for 
rapid resistance prediction, but existing models lack generalizability 
across bacterial species. 

We developed a transformer-based deep learning model to predict antibiotic 
resistance from genomic sequences across multiple pathogen species. Our 
approach integrates evolutionary information and protein structure to 
improve cross-species accuracy.
```

**Visual Support**:
- Conceptual diagram showing problem
- Infographic with statistics
- Image of application context

**Common Mistakes**:
- ❌ Extensive literature review
- ❌ Too much background detail
- ❌ Undefined acronyms at first use
- ❌ Missing clear objective statement

### Methods

**Purpose**: Describe approach sufficiently for understanding (not replication)

**Key Question**: "How did you do it?

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

