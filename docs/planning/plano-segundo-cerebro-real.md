# Plano: BerryBrain como Segundo Cérebro Real

**Data:** 2026-07-09
**Objetivo:** Tornar o BerryBrain um segundo cérebro funcional de ponta a ponta — captura → extração estruturada → conexões semânticas → síntese (insights) → recuperação/query — com IA via cloud (NVIDIA NIM) como prioridade.

---

## 1. Arquitetura de IA (regra invariável)

O sistema tem **duas opções mutuamente exclusivas**,控制 por `cfg["provider"]` no worker (`apps/worker/src/berrybrain_worker/main.py:370`):

| Modo | Provider | Endpoint | Quando |
|------|----------|----------|--------|
| **Cloud** | `cloud` | `cloud_api_url` (NVIDIA NIM) | **PRIORIDADE** — em uso |
| **Local** | `local` | `ollama_base_url` | Fallback offline |

- **Nunca os dois ao mesmo tempo.** `ollama_call()` (linha 357) faz `if is_cloud: cloud_generate else: ollama_generate`. Sem fallback misto.
- `effective_generation_provider()` (linha 440) detecta `nvidia-nim` pela URL/model.
- `ai_provider` e `graph_ai_provider` nas settings controlam nota vs grafo independentemente, mas cada um segue a mesma regra (um ou outro).

**Decisão:** Cloud NVIDIA NIM é o padrão. Ollama só se o usuário desativar cloud explicitamente.

---

## 2. Estado Atual (varredura global)

### ✅ Funciona (fundação real)
- Captura de notas Markdown + vault watcher + auto-titulo
- Grafo persistido: 23 nós / 22 arestas vivos
- Backlinks reais via `[[wikilinks]]` (estilo Obsidian)
- Busca FTS5 full-text
- Persistência SQLite + arquivos sobrevivem a sessões
- Pipeline de jobs com recuperação de jobs travados

### ❌ Não é "segundo cérebro" (gaps críticos)
| # | Problema | Localização | Impacto |
|---|----------|-------------|---------|
| G1 | `GENERATE_INFERRED_CONNECTIONS` é **no-op** (POST vazio) | worker/main.py:1305 | Grafo não tem conexões IA — só backlinks manuais |
| G2 | `InsightRecord` sempre vazio (jobs falham) | pipeline `GENERATE_GRAPH_INSIGHTS` | "O que meu cérebro aprendeu" nunca roda |
| G3 | `concepts` table nunca populada | `EXTRACT_CONCEPTS` só joga em metadata | Conceitos não viram nós do grafo |
| G4 | Busca "híbrida" é mentira (FTS5 only) | search.py | Sem similaridade semântica |
| G5 | `infer_from_graph` ignora `graph_edges` | second_brain.py:548 | QA do grafo não usa estrutura rica |
| G6 | Insight nodes órfãos (5 nós, 0 records) | second_brain.py | Inconsistência de dados |
| G7 | Schema drift (10 colunas faltando) | database.py | `/enrich` e `/validate-web` crasham |

**G7 já resolvido** em código (`ensure_sqlite_columns` em database.py:27, chamado em `init_database` main.py:40). Aplica no restart do container API.

---

## 3. Plano de Ação

### Fase 0 — Fundação (pronta)
- [x] G7: Schema migration (reiniciar API aplica 10 colunas)
- [x] Cloud NVIDIA NIM como provider padrão nas settings
- [x] SearxNG adicionado como serviço opcional (profile `web-validation`) no `docker-compose.yml` (não obrigatório para cloud)

### Fase 1 — Conexões Semânticas Reais (o "cérebro")
**Prioridade: ALTA** — sem isso o grafo é só um visualizador de notas.

- [x] **G1:** `generate_inferred_graph_connections` (second_brain.py) — usa `ai_gateway` (cloud NVIDIA NIM OU Ollama, nunca os dois) para encontrar conexões não-óbvias entre nós
  - Endpoint `POST /api/v1/graph/infer-connections`
  - Worker `process_generate_inferred_connections` expande primeiro (conceitos→nós) depois infere
  - Cria `GraphEdgeRecord(type="inferred", reason, confidence, provider, model)`
  - Respeita `auto_confirm_confidence`
- [x] **G3:** Mecanismo já existia em `expand_knowledge_graph` (`_upsert_concept` → `_upsert_concept_node`); worker agora expande antes de inferir, garantindo nós de conceito presentes
  - Bridge `EXTRACT_CONCEPTS` → `ConceptRecord` → `GraphNodeRecord(type="concept")` confirmada funcionando
- [x] **Concluído:** cor de aresta `inferred` (#9EBF61) no `graph-view.tsx` (EDGE_COLORS)

### Fase 2 — Síntese (Insights)
**Prioridade: ALTA** — define o "segundo cérebro" como ativo, não passivo.

- [x] **G2:** IA (`process_generate_graph_insights`) já cria `InsightRecord` quando cloud NIM responde. Adicionado **fallback determinístico** `_generate_deterministic_insights` (second_brain.py) que cria insights REAIS da estrutura do grafo mesmo sem IA: notas isoladas → `knowledge_gap`, conceito hub (≥3 conexões) → `central_concept`. Com `why_it_matters`, `evidence`, `suggested_action`, `provider="deterministic"`.
- [x] **G6:** `_prune_orphan_insight_nodes` (second_brain.py) remove nós `insight` sem `InsightRecord` correspondente; chamado em `expand_knowledge_graph`. Nós legados `source='ai'` órfãos limpos.

### Fase 3 — Recuperação / Query
**Prioridade: MÉDIA** — melhora UX, não bloqueia o "cérebro".

- [x] **G5:** `infer_from_graph` agora casa tokens contra `graph_edges` (com labels dos nós) além de `ConnectionRecord`, escolhendo o melhor score entre as duas fontes.
- [x] **G4:** Removida a mentira "híbrido" — worker `FIND_CONNECTIONS` não envia mais `mode:"hybrid"`; busca é FTS5 honesta. Embeddings via cloud NIM (YAGNI: sem embeddings locais).

### Fase 4 — Validação Web (SearxNG)
**Prioridade: BAIXA** — diferencial, não core.

- [x] Serviço SearxNG adicionado ao `docker-compose.yml` (profile `web-validation`, porta `BERRYBRAIN_SEARXNG_PORT:-8888`, volume `searxng_config`). Opt-in para não obrigar em modo cloud.
- [x] `VALIDATE_GRAPH_NODE_WITH_WEB` implementado (services.py) + endpoint `POST /nodes/{id}/validate-web` — disparo manual via UI. Mantido manual (não automático) pois SearxNG é opt-in.

---

## 4. O que NÃO fazer (YAGNI)

- Não implementar embeddings locais se cloud NVIDIA NIM já faz similaridade
- Não criar sistema de flashcards (já removido do produto)
- Não adicionar mais temas de cor (só light/dark com #9EBF61/#CC4168)
- Não misturar Ollama + Cloud na mesma execução

---

## 5. Critério de Sucesso

BerryBrain é "segundo cérebro real" quando:
1. Nota criada → pipeline extrai conceitos/entidades → viram nós do grafo ✅
2. Grafo tem conexões IA explicáveis (reason + evidence) ✅
3. Insights gerados periodicamente e exibidos na Home ✅
4. "Pergunte ao grafo" responde usando arestas reais ✅
5. Tudo via cloud NVIDIA NIM, sem Ollama obrigatório ✅
