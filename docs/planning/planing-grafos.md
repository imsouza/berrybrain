# Planejamento do Grafo BerryBrain

## Veredito Atual

O BerryBrain **ainda não é um segundo cérebro real completo**.

Ele já tem base real:

- notas reais do vault;
- nós persistidos;
- arestas persistidas;
- motivos e evidências em várias conexões;
- inferência do grafo usando provider configurado;
- manual notes por nó;
- status confirm/ignore;
- proveniência básica de provider/model;
- validação web parcial via SearxNG;
- relatório de qualidade do grafo no backend.

Mas ainda falta o ponto central: o grafo precisa produzir pensamento útil, não só estrutura. Hoje ele é um **grafo de conhecimento parcial com automação**, não ainda um segundo cérebro completo.

## Problema Principal

O grafo ainda mistura:

- nós de nota úteis;
- conceitos reais;
- tópicos extraídos de headings;
- entidades fracas;
- fontes web;
- insights;
- conexões confirmadas;
- conexões sugeridas;
- artefatos parser/system.

Isso gera visualização confusa. Um nó pode existir sem responder:

- por que ele importa?
- que evidência local sustenta isso?
- que insight nasceu dessa conexão?
- existe fonte externa que confirma, contradiz ou expande?
- que ação de estudo o usuário deve tomar?

## Objetivo

Transformar o grafo em uma camada cognitiva do BerryBrain.

O grafo deve responder:

1. O que esta nota/conceito significa?
2. Por que este nó existe?
3. Que evidências locais sustentam este nó?
4. Que conexões são explicáveis?
5. Que insight surge dessa conexão?
6. Que fontes externas confirmam, expandem ou contradizem?
7. Que lacunas surgem?
8. Que ação de estudo faz sentido agora?

## Status por Área

| Área | Status | Evidência | Problema | Ação |
|---|---|---|---|---|
| Notas reais | OK | `GraphNodeRecord`, `NoteRecord`, `/api/v1/graph` | Base existe | Manter |
| Nós dinâmicos | Parcial | `type`, `source`, `source_note_ids` | Alguns nós são parser/raw | Ocultar raw por padrão e enriquecer |
| Conexões explicadas | Parcial | `GraphEdgeRecord.reason`, `evidence` | Motivo nem sempre vira insight útil | Exibir como Connection Insight e gerar insights por conexão |
| Inferência com IA | Parcial | `/api/v1/graph/infer` | Depende de evidência e provider | Melhorar grounding e salvar inferências boas |
| Validação web | Parcial | `validate_node_with_web`, SearxNG | Era pouco visível na UI e podia duplicar fontes | Botão na UI, dedupe de fontes, status visível |
| Fonte externa | Parcial | `web_source`, `source_supports`, `source_expands`, `source_contradicts` | Precisa confirmação e resumo melhor | Criar painel de fontes por nó |
| Insights reais | Parcial | `InsightRecord`, graph insight jobs | Ainda pode ficar vazio se IA/provider falha | Criar pipeline específico de insights por aresta |
| Home como segundo cérebro | Parcial | Home mostra resumo | Ainda depende da qualidade do grafo | Mostrar “what changed in the graph” |
| Qualidade do grafo | Parcial | `/api/v1/graph/quality-report` | Não aparece na UI | Adicionar card/relatório |

## Ajustes Aplicados nesta Etapa

1. Brain View agora não deve receber arestas ligadas a nós filtrados.
2. Web validation evita duplicar fontes web pelo mesmo URL.
3. Web validation grava `source_evidence`, `source_quality` e metadata de URL.
4. Painel de nó mostra:
   - AI understanding;
   - learning value;
   - source evidence;
   - validation status;
   - source quality.
5. Cada conexão no painel aparece como `Connection insight`, com motivo, evidência, provider/model e botões confirm/ignore.
6. Painel do nó ganhou ação `Validate with web`.

## Modelo-Alvo de Nó

Cada nó útil deve ter:

- `type`;
- `label`;
- `summary`;
- `aiSummary`;
- `aiContext`;
- `learningValue`;
- `sourceEvidence`;
- `sourceQuality`;
- `validationStatus`;
- `sourceNoteIds`;
- `provider`;
- `model`;
- `promptVersion`;
- `confidence`;
- `status`.

Nós sem `aiContext`, `aiSummary` ou evidência devem continuar auditáveis, mas não devem dominar o Brain View.

## Modelo-Alvo de Conexão

Cada conexão útil deve ter:

- `sourceNodeId`;
- `targetNodeId`;
- `type`;
- `reason`;
- `evidence`;
- `confidence`;
- `provider`;
- `model`;
- `status`;
- `connectionInsight`;
- `studyAction`;
- `graphImpact`.

Regra: conexão sem `reason` e sem `evidence` não é conhecimento; é ruído.

## Internet e Retroalimentação

Provider padrão: SearxNG local.

Fluxo desejado:

1. Usuário clica `Validate with web` ou job automático valida nó importante.
2. Sistema busca fontes externas relevantes.
3. Sistema cria nós `web_source`.
4. Sistema cria arestas:
   - `source_supports`;
   - `source_expands`;
   - `source_contradicts`.
5. IA compara notas locais com fontes externas.
6. Sistema gera:
   - insight de confirmação;
   - insight de expansão;
   - insight de contradição;
   - lacuna de estudo.
7. Nada externo sobrescreve notas do usuário.
8. Fontes externas entram como sugestão e exigem confirmação quando alteram o grafo.

## Pipeline Necessário

### Fase 1: Higiene e Visibilidade

- Ocultar raw parser nodes no Brain View.
- Remover/mesclar duplicados por label normalizado.
- Filtrar arestas de nós ocultos.
- Mostrar qualidade do nó no painel.
- Mostrar status web validation.

### Fase 2: Insights por Conexão

Criar job:

- `GENERATE_CONNECTION_INSIGHTS`

Entrada:

- nó A;
- nó B;
- reason;
- evidence;
- notas relacionadas;
- contexto local.

Saída:

- insight;
- why it matters;
- evidence;
- graph impact;
- suggested action;
- confidence;
- provider/model.

### Fase 3: Enriquecimento por Nó

Criar job:

- `ENRICH_GRAPH_NODE`

Saída:

- `aiSummary`;
- `aiContext`;
- `learningValue`;
- `sourceEvidence`;
- `sourceQuality`;
- conexões sugeridas;
- lacunas.

### Fase 4: Web Validation com IA

Melhorar `VALIDATE_GRAPH_NODE_WITH_WEB`:

- buscar via SearxNG;
- deduplicar fontes por URL;
- pedir IA para classificar suporte/contradição/expansão;
- salvar rationale;
- criar insights;
- marcar status `validated`, `needs_review` ou `conflict_found`.

### Fase 5: UI Cognitiva

Tela de grafo deve mostrar:

- Brain View limpo por padrão;
- filtros Raw / Enriched / Web Validated / Needs Review;
- painel de nó com interpretação;
- fontes externas;
- connection insights;
- ações: Enrich with AI, Validate with web, Create note, Confirm, Ignore, Merge.

### Fase 6: Home e Sistema

Home deve mostrar:

- o que o grafo aprendeu recentemente;
- conexões novas com insight;
- fontes externas adicionadas;
- contradições/lacunas;
- qualidade do grafo.

## Critérios para Virar Segundo Cérebro Real

O sistema só deve ser considerado segundo cérebro real quando:

- a maioria dos nós visíveis tem `aiContext` ou `aiSummary`;
- conexões visíveis têm motivo e evidência;
- conexões importantes geram insight real;
- inferência usa dados do grafo e cita evidência;
- fontes web entram como nós/fonte e não como texto solto;
- contradições externas são marcadas e revisáveis;
- usuário pode confirmar/ignorar tudo que é inferido;
- Home mostra aprendizado recente, não só contadores;
- raw parser nodes não poluem a visão padrão;
- o grafo sugere ações de estudo úteis.

## Próximas Implementações Prioritárias

1. `POST /api/v1/graph/connections/{id}/generate-insight`
2. `POST /api/v1/graph/nodes/{id}/enrich-ai`
3. `GET /api/v1/graph/nodes/{id}/sources`
4. `GET /api/v1/graph/quality-report` na UI
5. Job `GENERATE_CONNECTION_INSIGHTS`
6. Job `ENRICH_GRAPH_NODE`
7. Job `VALIDATE_GRAPH_NODE_WITH_WEB`
8. Card “Graph learned recently” na Home.

## Risco Atual

Se o BerryBrain continuar apenas criando nós/arestas, ele vira um visualizador de relações.

Para ser segundo cérebro, o grafo precisa produzir:

- interpretação;
- evidência;
- hipótese;
- validação;
- contradição;
- lacuna;
- ação de estudo.
