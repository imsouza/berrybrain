# Plano de Debug e Correções — BerryBrain

> Executar passo a passo. Só avançar para o próximo passo com 100% de certeza de que o atual funciona sem erros.

## Regras de execução
- Um passo por vez, validado (build/lint/runtime) antes de seguir.
- Frontend: `apps/web` (Next 15, React 19, Tailwind 3). Sem lib de gráficos instalada.
- Backend: `apps/api` (FastAPI), Worker: `apps/worker`.
- Verificação frontend: `docker compose exec -T web sh -c 'cd /app/apps/web && npx tsc --noEmit'` (ou build).
- i18n atual: `settings-panel.tsx` exporta `I18N`, `t()`, `getLang()`, `LangKind` — hoje só usado dentro do próprio settings.

---

## Passo 1 — Número do sino em vermelho
- **Arquivo:** `components/sidebar/workspace-sidebar.tsx:80-84`
- Badge de contagem usa `text-white` sobre `bg-accent`.
- **Ação:** trocar `text-white` → `text-red-600` (ou `#CC4168`) no número.
- **Validar:** badge aparece vermelho quando `attentionCount > 0`.

## Passo 2 — Preloader ao criar nota
- **Origem:** `contexts/workspace-context.tsx:92-105` `createDraft()` sem flag de loading.
- 3 pontos de entrada: sidebar `:47-50`, home textarea `home-view.tsx:107-117`, "Criar rascunho vazio" `:158-160`, + command-palette `:38`.
- **Ação:** expor `creatingDraft` no contexto; overlay/spinner global enquanto cria. Criar componente `Spinner` reutilizável (`animate-spin`, não existe hoje).
- **Validar:** ao clicar em qualquer entrada, spinner aparece até a nota abrir.

## Passo 3 — Gráficos nas estatísticas da home
- **Arquivo:** `components/home/home-view.tsx` `StatsGrid` `:352-365`.
- Dados: `summary.stats` de `GET /api/v1/home/summary`.
- Sem lib de gráficos. **Ação:** construir infográficos leves com SVG/divs (barras, donut de confiança, distribuição de tipos) sem dependência nova (YAGNI).
- **Validar:** gráficos renderizam com dados reais, responsivos, tema claro/escuro.

## Passo 4 — Botões do grafo: acentuação + cores + Excluir Nó
- **Arquivo:** `components/graph-screen.tsx:587-601`
- Corrigir: `Confirmar no`→`Confirmar Nó` (`:592`), `Ignorar no`→`Ignorar Nó` (`:595`).
- Pintar: Abrir nota (accent), Confirmar Nó (verde/emerald), Ignorar Nó (âmbar), Excluir Nó (vermelho #CC4168).
- **Adicionar botão Excluir Nó** — não existe hoje. Precisa endpoint DELETE + handler (verificar se existe rota de exclusão de nó; se não, criar).
- **Validar:** labels acentuados, cores aplicadas, exclusão funciona e remove nó+arestas.

## Passo 5 — Validar fórmula de % de confiança dos insights
- **Frontend:** `insights/page.tsx:265` `Math.round((confidence||0)*100)`; idem home-view, graph-screen.
- **Ação:** auditar backend — como `confidence` é calculado (determinístico vs AI). Confirmar se é probabilidade [0,1] estatisticamente coerente ou número arbitrário. Corrigir fórmula se não seguir acurácia estatística.
- **Validar:** valores de confiança fazem sentido estatístico e são consistentes entre telas.

## Passo 6 — Abrir nota ao clicar no nó do grafo (e fechar grafo)
- **Arquivo:** `components/graph-view.tsx:374-379` (single-click só seleciona), `graph-screen.tsx:446-453`.
- `onNavigate` já fecha grafo + abre nota (`note-workspace.tsx:61`).
- **Ação:** no single-click, se nó tem `path` (nota/vault), chamar `onNavigate(node.path)` → fecha grafo e abre nota. Manter painel de detalhe para nós sem path.
- **Validar:** clicar em nó de nota abre a nota e fecha o grafo.

## Passo 7 — Embeddings NVIDIA NIM (explicação)
- **Somente explicação, sem código obrigatório.**
- `process_generate_embedding` (`worker/main.py:651`): tenta cloud se `provider=cloud` + `cloud_api_url` + `cloud_api_key` + `cloud_embedding_model`; senão Ollama; senão `status=skipped`.
- 0 embeddings hoje porque: nenhum `cloud_embedding_model` configurado e Ollama offline.
- NIM **oferece** modelos de embedding (ex.: `nvidia/nv-embedqa-e5-v5`). Necessário só se quiser busca semântica real (hoje busca é FTS5/keyword). Opcional: configurar modelo de embedding NIM.

## Passo 8 — Painel (i) com explicação completa
- **Arquivo:** `components/guide-panel.tsx` (10 Steps hardcoded pt-BR).
- **Ação:** expandir com explicação de TODAS as funções: captura de nota, pipeline de IA, grafo, tipos de nó, suggest/confirmar/ignorar, insights, busca, enrichment, validação web, settings, temas, idioma.
- **Validar:** conteúdo completo, legível, respeita i18n (passo 9).

## Passo 9 — i18n completo pt-BR/en
- Sistema em pt-BR quando `bb_lang=pt-BR`; notas do usuário NUNCA traduzidas.
- **Ação:** expandir `I18N` com todas as chaves da UI; retrofit dos componentes hardcoded: home-view, graph-screen, graph-view, note-editor, markdown-preview, command-palette, notifications, insights, activity, sidebar, guide-panel, layout.
- **Validar:** trocar idioma nas settings muda toda a UI; notas permanecem no idioma digitado.

---

## Ordem de execução
1 → 2 → 3 → 4 → 5 → 6 → 7(explicação) → 8 → 9. Validar cada um antes de seguir.
