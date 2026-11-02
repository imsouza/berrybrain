# BerryBrain Agent Skills Library (`skills/` — 1,576 Standardized `.md` Skills)

This directory contains BerryBrain's standardized library of **1,576 Markdown Agent Skills (`.md`)**, automatically routed by task context during Ask, multi-hop synthesis, and background 24-hour knowledge enrichment:

- **15 Core BerryBrain Priority-1 Skills (`skills/*.md`, `priority_tier: 1`)**: Scientific Article (IMRaD / IEEE / SBC / ABNT / JBCS), Systematic Literature Review (PRISMA), Thesis / Monograph / Dissertation, Technical Documentation / RFC / ADR, Study Guide & Active Recall, Multi-Hop Research Synthesis, Critical Epistemic Audit, Executive Briefing Report, Software Architecture & Code Analysis, Mathematical & Formal Proof (LaTeX), Experimental Methodology Lab, Pedagogical Lesson Plan (Feynman), Project Roadmap Planning, Comparative Trade-off Matrix, and 24-Hour Continuous Knowledge Enrichment.
- **177 Scientific Agent Skills (`skills/scientific/*.md`, adapted from `K-Dense-AI/claude-scientific-skills`)**: Bioinformatics, statistical inference, scientific critical thinking, measurement uncertainty and units (GUM), ontology resolution, medicinal chemistry, genomics, physics, symbolic mathematics (SymPy), machine learning, and graph neural networks (`torch-geometric`).
- **1,100 Scientific Reference Modules (`skills/scientific-references/*.md`)**: Specialized protocols for experimental design, evidence hierarchies, statistical pitfalls, methodological bias detection, logical fallacies, and domain research checklists.
- **265 Fabric Cognitive Patterns (`skills/fabric/*.md`, adapted from `danielmiessler/fabric`)**: Claim analysis (`analyze-claims`), paper analysis (`analyze-paper`), threat modeling (`threat-model`), wisdom extraction (`extract-wisdom`), debate synthesis, essay structuring, and transparency auditing.
- **19 Anthropic Workflow Skills (`skills/anthropic/*.md`, adapted from `anthropics/skills`)**: Document co-authoring (`doc-coauthoring`), artifact architecture, systems design, and structured workflow orchestration.

All 1,576 skills conform to the **BerryBrain Skill Standard**: structured YAML frontmatter (`id`, `name`, `category`, `source_repo`, `description`, `priority_tier`, `recommended_max_tokens`, `task_types`, `triggers`, `keywords`) paired with BerryBrain's **Mandatory Epistemic Protocol**.

## Non-Negotiable Epistemic Rules

1. **Vault & Admitted Graph First**: Skills govern *analytical structure, methodological rigor, and section completeness*—never factual invention. Parametric model knowledge must never replace missing vault evidence, and factual claims must cite `[Title](bbref:<evidenceId>)`.
2. **24h Enrich AI & Verified Web Provenance**: External sources discovered and checked by 24-hour background enrichment (`RESEARCH_GRAPH`, `VALIDATE_GRAPH_NODE_WITH_WEB`, `ENRICH_GRAPH_NODE`) remain distinct from user-authored Markdown and carry explicit epistemic stances (`source_supports`, `source_expands`, `source_contradicts`).
3. **Automatic Contextual Activation & API Discovery**: When a user or external backend asks for a scientific article, PRISMA review, RFC/ADR, study guide, or formal proof, the skill selector automatically activates the highest-scoring compatible skill(s). External integrations can inspect the catalog and test prompt matching via `GET /api/v1/ai/skills?query=...&task_type=ask`.

## Adding a Custom Skill for Your Project

When incorporating the BerryBrain Architecture into your own product (see [`docs/integrating-berrybrain-architecture.md`](../docs/integrating-berrybrain-architecture.md)), drop a `.md` file into `skills/` with the standard frontmatter:

```markdown
---
id: custom-incident-postmortem
name: Blameless Incident Postmortem
category: engineering
source_repo: local/custom
description: Synthesizes incident timelines, root causes, and follow-up actions from vault notes.
priority_tier: 1
recommended_max_tokens: 1800
task_types:
  - ask
  - synthesis
triggers:
  - incident postmortem
  - root cause report
keywords:
  - outage
  - timeline
  - remediation
---

# Required Structure
1. **Impact & Timeline** — cite verified timestamps and notes via `[Title](bbref:<evidenceId>)`.
2. **Contributing Factors vs. Unverified Hypotheses** — explicitly separate confirmed graph edges from open gaps.
3. **Remediation Checklist** — concrete, bounded engineering actions.
```

## Priority-1 Core Skill Catalog

| Skill ID | File | Category | Primary Contextual Trigger |
| :--- | :--- | :--- | :--- |
| `scientific-article` | `scientific-article.md` | `academic` | Scientific papers (IMRaD, IEEE, SBC, ABNT, JBCS) |
| `literature-review` | `literature-review.md` | `academic` | Systematic literature reviews, state of the art, PRISMA |
| `tcc-dissertation-monograph` | `tcc-dissertation-monograph.md` | `academic` | Undergraduate thesis (TCC), Master's dissertation, PhD monograph |
| `technical-documentation-rfc` | `technical-documentation-rfc.md` | `engineering` | Technical documentation, architecture specs, RFCs, ADRs |
| `study-guide-active-recall` | `study-guide-active-recall.md` | `learning` | Study guides, learning paths, Active Recall prompts |
| `research-synthesis-multihop` | `research-synthesis-multihop.md` | `research` | Multi-hop synthesis across notes, concepts, and graph clusters |
| `critical-epistemic-audit` | `critical-epistemic-audit.md` | `research` | Epistemic critique, contradiction analysis, evidence gaps |
| `executive-briefing-report` | `executive-briefing-report.md` | `synthesis` | Executive summaries, strategic briefings, decision memos |
| `software-architecture-code` | `software-architecture-code.md` | `engineering` | Software architecture reviews, design patterns, trade-off analysis |
| `mathematical-formal-proof` | `mathematical-formal-proof.md` | `quantitative` | Mathematical modeling, formal proofs, statistical derivations, LaTeX |
| `experimental-methodology-lab` | `experimental-methodology-lab.md` | `academic` | Experimental protocols, controls, metrics, threats to validity |
| `pedagogical-lesson-plan` | `pedagogical-lesson-plan.md` | `learning` | Step-by-step pedagogical explanations and Feynman-style teaching |
| `project-roadmap-planning` | `project-roadmap-planning.md` | `planning` | Engineering roadmaps, milestones, and actionable execution plans |
| `comparative-matrix-benchmark` | `comparative-matrix-benchmark.md` | `synthesis` | Multi-criteria comparison matrices and benchmark analyses |
| `knowledge-enrichment-24h` | `knowledge-enrichment-24h.md` | `enrichment` | 24h continuous graph verification across vault + verified web sources |
