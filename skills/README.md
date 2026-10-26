# BerryBrain Agent Skills Library (`/skills` — 1.576 Skills `.md` Padronizadas)

Esta pasta contém a biblioteca completa de **1.576 Skills em Markdown (`.md`)** do agente cognitivo do **BerryBrain**, unificando e padronizando:
- **15 Core BerryBrain Skills (`skills/*.md`, `priority_tier: 1`):** Artigo Científico (IMRaD/IEEE/SBC/ABNT), Revisão Sistemática de Literatura (PRISMA), TCC/Dissertação/Monografia, Documentação Técnica/RFC/ADR, Guia de Estudo & Active Recall, Síntese Multi-Hop de Pesquisa, Auditoria Epistêmica, Briefing Executivo, Arquitetura de Software, Demonstração Matemática/LaTeX, Metodologia Experimental, Plano de Aula/Feynman, Roadmap de Projeto, Matriz Comparativa e Enriquecimento Contínuo 24h.
- **177 Scientific Agent Skills (`skills/scientific/*.md`, `K-Dense-AI/claude-scientific-skills`):** Bioinformática, análise estatística, pensamento crítico científico, incerteza e unidades (GUM), resolução ontológica, química medicinal, genômica, física, matemática simbólica (SymPy), aprendizado de máquina e grafos (`torch-geometric`).
- **1.100 Módulos de Referência Científica (`skills/scientific-references/*.md`):** Protocolos especializados de desenho experimental, hierarquia de evidências, armadilhas estatísticas, vieses metodológicos, falácias lógicas e receitas científicas.
- **265 Padrões Cognitivos Fabric (`skills/fabric/*.md`, `danielmiessler/fabric`):** Extração de sabedoria (`extract-wisdom`), análise de afirmações (`analyze-claims`), análise de artigos (`analyze-paper`), modelagem de ameaças (`threat-model`), síntese de debates, redação de ensaios e auditoria de transparência.
- **19 Skills Oficiais de Agente (`skills/anthropic/*.md`, `anthropics/skills`):** Coautoria de documentos (`doc-coauthoring`), arquitetura de artefatos, design de sistemas e criação de workflows.

Todas as 1.576 skills seguem o **Padrão Oficial BerryBrain** (frontmatter YAML com `id`, `name`, `category`, `source_repo`, `description`, `priority_tier`, `recommended_max_tokens`, `task_types`, `triggers`, `keywords` + **Protocolo Epistêmico Obrigatório do BerryBrain** exigindo ancoragem primária no Vault/Grafo, integração com o Enrich AI 24h e citações verificáveis `[Título](bbref:<evidenceId>)`).

## Princípios Inegociáveis das Skills do BerryBrain
1. **Busca Primária no Próprio Conteúdo (Vault & Grafo):** Nenhuma skill substitui as evidências reais do usuário por conhecimento paramétrico solto. Toda afirmação factual deve citar `[Título](bbref:<evidenceId>)`.
2. **Integração com o Enrich AI 24h & Fontes Web Verificadas:** As fontes externas pesquisadas, validadas e anexadas ao grafo pelo monitoramento contínuo 24h (`RESEARCH_GRAPH`, `VALIDATE_GRAPH_NODE_WITH_WEB`, `ENRICH_GRAPH_NODE`) são incorporadas com rastreabilidade explícita (`source_supports`, `source_expands`, `source_contradicts`).
3. **Rigor Estrutural Automático:** Quando o usuário pede, por exemplo, um *artigo científico*, uma *revisão de literatura*, um *TCC/monografia*, uma *documentação técnica/RFC* ou um *guia de estudo*, o seletor contextual ativa automaticamente a skill correspondente e aplica seu contrato estrutural completo.

## Catálogo de Skills Disponíveis
| ID da Skill | Arquivo | Categoria | Acionamento Contextual Principal |
| :--- | :--- | :--- | :--- |
| `scientific-article` | `scientific-article.md` | `academic` | Artigos científicos (IMRaD, IEEE, SBC, ABNT, JBCS), papers acadêmicos |
| `literature-review` | `literature-review.md` | `academic` | Revisão sistemática de literatura, estado da arte, PRISMA |
| `tcc-dissertation-monograph` | `tcc-dissertation-monograph.md` | `academic` | TCC, monografia, dissertação de mestrado, tese, projeto de pesquisa |
| `technical-documentation-rfc` | `technical-documentation-rfc.md` | `engineering` | Documentação técnica, especificação de arquitetura, RFC, ADR |
| `study-guide-active-recall` | `study-guide-active-recall.md` | `learning` | Guia de estudo, roteiro de aprendizagem, Active Recall, flashcards |
| `research-synthesis-multihop` | `research-synthesis-multihop.md` | `research` | Síntese multi-hop, conexão profunda entre notas e conceitos |
| `critical-epistemic-audit` | `critical-epistemic-audit.md` | `research` | Análise crítica, auditoria epistêmica, contradições e lacunas |
| `executive-briefing-report` | `executive-briefing-report.md` | `synthesis` | Resumo executivo, briefing estratégico, relatório de decisão |
| `software-architecture-code` | `software-architecture-code.md` | `engineering` | Arquitetura de software, análise de código, padrões e algoritmos |
| `mathematical-formal-proof` | `mathematical-formal-proof.md` | `quantitative` | Modelagem matemática, demonstrações formais, estatística, LaTeX |
| `experimental-methodology-lab` | `experimental-methodology-lab.md` | `academic` | Planejamento experimental, protocolo científico, métricas e validade |
| `pedagogical-lesson-plan` | `pedagogical-lesson-plan.md` | `learning` | Plano de aula, explicação didática passo a passo (Feynman) |
| `project-roadmap-planning` | `project-roadmap-planning.md` | `planning` | Plano de projeto, roadmap, cronograma e checklist acionável |
| `comparative-matrix-benchmark` | `comparative-matrix-benchmark.md` | `synthesis` | Análise comparativa, matriz de trade-offs, benchmark entre abordagens |
| `knowledge-enrichment-24h` | `knowledge-enrichment-24h.md` | `enrichment` | Enriquecimento 24h (validação no próprio conteúdo + fontes web) |
