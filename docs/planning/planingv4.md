# BerryBrain — planingv4.md

## Planejamento V4 — Validação da Home, Insights Reais, Atividade, Notificações, Monitor e Segundo Cérebro

Este documento define uma auditoria e um plano de correção para validar a Home, notificações, links, monitor, insights reais da IA, seção “Precisa de atenção” e qualidade geral do segundo cérebro do BerryBrain.

---

## 1. Contexto Atual

A Home já mostra:

- saudação;
- status Worker/Ollama/NVIDIA NIM;
- editor-first;
- Autopilot em dia;
- barra de progresso;
- Insights da IA;
- Processando agora;
- Grafo de conhecimento;
- Precisa de atenção;
- Estatísticas;
- Conexões recentes.

Porém existem problemas graves de UX e funcionalidade:

1. Ao clicar no sino/notificações, aparecem as mesmas informações do Monitor.
2. “Ver insights” não abre uma tela real de insights; redireciona ou se comporta como Monitor.
3. “Ver atividade” também parece levar para a mesma tela/experiência do Monitor.
4. A área “Precisa de atenção” talvez seja desnecessária quando está tudo certo.
5. Os insights da IA aparecem como vazios, genéricos ou sem evidência clara.
6. É necessário validar se os insights são realmente gerados pela IA configurada, local ou cloud/NVIDIA NIM.
7. Insights não podem ser apenas mensagens genéricas; precisam ser baseados em conteúdo real, fluxo de ideias, contexto, lacunas, críticas, conexões, sugestões e agregação de conhecimento.
8. O sistema mostra jobs técnicos, mas precisa mostrar resultados úteis para o usuário.
9. A Home precisa diferenciar claramente:
   - Monitor;
   - Atividade automática;
   - Notificações;
   - Insights;
   - Grafo;
   - Revisão;
   - Precisa de atenção.

---

## 2. Objetivo

Garantir que o BerryBrain funcione como um segundo cérebro real, e não apenas como uma interface visual com jobs técnicos.

O sistema deve permitir que o usuário entenda:

- o que está acontecendo;
- o que foi processado;
- quais insights foram gerados;
- quais conexões foram descobertas;
- quais lacunas existem;
- quais ações pode tomar;
- onde cada informação aparece;
- o que é técnico e o que é útil para estudo.

---

## 3. Auditoria de Rotas, Links e Navegação

Verifique todos os botões/links da Home e da sidebar:

- Ver atividade;
- Ver insights;
- Ver grafo;
- Monitor;
- Sino/notificações;
- Precisa de atenção;
- Recalcular conexões;
- Abrir grafo;
- Ver órfãs;
- Scan vault;
- Revisar hoje;
- Nova nota.

Para cada item, verificar:

- qual componente renderiza;
- qual função é chamada;
- para qual rota navega;
- se abre modal/drawer;
- se usa dados reais;
- se está duplicando comportamento de outro botão;
- se está apontando para Monitor indevidamente;
- se existe tela dedicada;
- se existe empty state correto;
- se existe loading e erro.

### Relatório obrigatório

| Ação | Status | Rota/Componente | Problema | Correção |
|---|---|---|---|---|
| Ver insights | OK/PARCIAL/ERRADO | arquivo/função | descrição | ação |
| Ver atividade | OK/PARCIAL/ERRADO | arquivo/função | descrição | ação |
| Sino/notificações | OK/PARCIAL/ERRADO | arquivo/função | descrição | ação |
| Monitor | OK/PARCIAL/ERRADO | arquivo/função | descrição | ação |
| Ver grafo | OK/PARCIAL/ERRADO | arquivo/função | descrição | ação |
| Precisa de atenção | OK/PARCIAL/ERRADO | arquivo/função | descrição | ação |

### Critério

Nenhum botão deve abrir a tela errada ou repetir o comportamento de outro sem necessidade.

---

## 4. Separação Correta das Telas

Separar claramente as telas e responsabilidades.

### 4.1 Home

Resumo inteligente do segundo cérebro.

Deve mostrar:

- status resumido;
- editor-first;
- progresso do Autopilot;
- insights recentes;
- processando agora;
- grafo resumido;
- estatísticas;
- conexões recentes;
- precisa de atenção apenas se houver algo relevante.

### 4.2 Monitor

Tela técnica de monitoramento.

Deve mostrar:

- status Worker;
- status NVIDIA NIM;
- status Ollama;
- fila;
- jobs;
- requests;
- latência;
- erros técnicos;
- logs técnicos;
- provider;
- modelo;
- retry;
- timeout.

### 4.3 Atividade Automática

Timeline legível do que o BerryBrain fez.

Deve mostrar:

- nota assimilada;
- título gerado;
- embedding criado;
- conexão encontrada;
- grafo atualizado;
- insight gerado;
- flashcard criado;
- erro e retry.

Não deve ser apenas lista crua de jobs.

### 4.4 Insights

Tela dedicada de insights reais.

Deve mostrar:

- insights por prioridade;
- tipo;
- título;
- descrição;
- evidência;
- notas relacionadas;
- conceitos relacionados;
- ação sugerida;
- status novo/aplicado/ignorado;
- botão aplicar;
- botão ignorar;
- botão ver no grafo;
- botão criar revisão;
- botão criar nota permanente.

### 4.5 Notificações

Dropdown curto e acionável.

Deve mostrar:

- eventos recentes importantes;
- erros;
- insights prontos;
- jobs concluídos;
- ações que precisam da atenção do usuário.

Não deve duplicar a tela Monitor.

### 4.6 Grafo

Tela livre de exploração do conhecimento.

Deve mostrar:

- nós;
- conexões;
- busca/inferência;
- filtros;
- resumo de nó;
- insights no grafo;
- conexões explicáveis.

---

## 5. Correção do Sino/Notificações

O sino de notificações não deve mostrar a mesma coisa que o Monitor.

Criar ou corrigir componente:

```txt
NotificationsPopover
```

Ele deve exibir somente notificações úteis e acionáveis.

### Tipos de notificação

- insight_ready;
- job_failed;
- graph_updated;
- note_assimilated;
- title_generated;
- flashcards_ready;
- review_due;
- provider_slow;
- provider_offline;
- connection_suggested;
- attention_required.

### Exemplos

```txt
Insight pronto
“Foi detectada uma lacuna sobre monitoramento distribuído.”
Botão: Ver insight
```

```txt
Grafo atualizado
“3 novas conexões foram criadas.”
Botão: Abrir grafo
```

```txt
NVIDIA NIM lento
“Uma chamada ultrapassou 60s.”
Botão: Ver monitor
```

### Critérios

- Notificações devem ser curtas.
- Cada notificação deve ter ação.
- Deve haver “Marcar como lida”.
- Deve haver “Ver todas”.
- Não mostrar lista crua de jobs técnicos.
- Não abrir Monitor por padrão, exceto em erro técnico/provider.

Criar tela opcional:

```txt
/notifications
```

ou manter apenas popover + Atividade automática.

---

## 6. Correção de “Ver Insights”

O botão “Ver insights” deve abrir uma tela real de insights, não Monitor.

Criar ou corrigir rota:

```txt
/insights
```

A tela Insights deve ser independente.

### Estrutura da tela

Topo:

- título: Insights da IA;
- status de geração;
- botão “Gerar insights agora”;
- filtros.

Filtros:

- Todos;
- Lacunas;
- Conexões;
- Críticas;
- Revisão;
- Duplicidades;
- Conceitos emergentes;
- Contexto;
- Alta prioridade;
- Aplicados;
- Ignorados.

### Cards de insight

Cada insight deve mostrar:

- tipo;
- prioridade;
- título;
- descrição;
- evidência;
- notas relacionadas;
- conceitos relacionados;
- provider/model;
- confiança;
- data;
- ação sugerida;
- botões.

### Exemplo de insight bom

```txt
Lacuna de conhecimento · Alta prioridade

Você possui notas sobre Docker, Linux shell e Python async, mas ainda não há uma nota central explicando como automação de scripts se conecta com containers e execução assíncrona.

Por que isso importa:
Esse é um ponto de integração entre infraestrutura, automação e programação concorrente. Criar uma nota permanente ajudaria a consolidar o contexto.

Evidências:
- linux-shell-scripting.md
- docker-essentials.md
- python-async-patterns.md

Ação sugerida:
Criar nota permanente: “Automação de ambientes com Shell, Docker e Async Python”

Botões:
- Criar nota permanente
- Ver no grafo
- Gerar revisão
- Ignorar
```

### Critérios

- “Ver insights” sempre abre `/insights`.
- Empty state de insights deve explicar o que falta.
- Se os insights estão processando, mostrar progresso.
- Se houve erro, mostrar erro e retry.
- Não redirecionar para Monitor.

---

## 7. Correção de “Ver Atividade”

“Ver atividade” deve abrir a tela Atividade automática, não Monitor.

Criar ou corrigir rota:

```txt
/activity
```

Essa tela deve traduzir jobs técnicos em eventos compreensíveis.

### Em vez de mostrar apenas

```txt
GENERATE_GRAPH_INSIGHTS
UPDATE_GRAPH_STATS
EXPAND_KNOWLEDGE_GRAPH
EXTRACT_CONTEXT
```

### Mostrar

```txt
Contexto extraído de linux-shell-scripting.md
Conceitos detectados em docker-essentials.md
Conexões inferidas para python-async-patterns.md
Grafo atualizado com 4 novos nós
Insights do grafo gerados
Falha ao gerar embedding — tentar novamente
```

A tela pode ter modo técnico expansível.

### Estrutura

Resumo:

- concluídos hoje;
- ativos;
- pendentes;
- erros.

Timeline:

- eventos em linguagem humana.

Modo técnico:

- job id;
- tipo;
- provider;
- modelo;
- duração;
- erro;
- payload resumido.

### Critério

Atividade automática não deve ser igual ao Monitor.

Monitor é técnico.  
Atividade é narrativa do que o BerryBrain fez.

---

## 8. Avaliação da Seção “Precisa de Atenção”

Audite a seção “Precisa de atenção”.

Ela só deve aparecer se houver algo que realmente exige atenção do usuário.

### Mostrar apenas quando existir

- job_failed;
- provider_offline;
- provider_timeout;
- insights_high_priority_unread;
- suggested_connections_waiting_approval;
- orphan_notes_above_threshold;
- unassimilated_notes_above_threshold;
- attachments_failed;
- graph_update_failed;
- review_overdue;
- storage_error;
- autosave_error.

### Se estiver tudo certo

Opção recomendada:

- ocultar completamente a seção.

Opção alternativa:

- mostrar “Tudo certo” como badge discreto no Autopilot.

### Evitar

- card grande apenas com “Tudo certo”.
- ocupar espaço da Home sem necessidade.

### Cada item deve ter

- motivo;
- impacto;
- ação.

### Exemplo

```txt
2 jobs falharam ao gerar insights

Impacto:
Algumas conexões podem não aparecer no grafo.

Ação:
Tentar novamente
```

---

## 9. Garantir Insights Reais da IA Configurada

Audite se os insights são realmente gerados pela IA configurada.

Verifique:

- provider usado;
- modelo usado;
- prompt usado;
- versão do prompt;
- notas usadas como entrada;
- conceitos usados;
- contexto usado;
- resposta bruta da IA, se armazenada;
- parsing da resposta;
- persistência no banco;
- exibição na UI.

Cada insight deve armazenar:

- id;
- type;
- title;
- description;
- reasoning;
- evidence;
- relatedNoteIds;
- relatedConceptIds;
- relatedConnectionIds;
- sourceContext;
- suggestedAction;
- priority;
- confidence;
- provider;
- model;
- promptVersion;
- generatedAt;
- status;
- appliedAt;
- ignoredAt.

### Proibido

- insights hardcoded;
- insights genéricos;
- insights sem evidência;
- insights sem nota relacionada;
- insights sem provider/model;
- insights sem ação;
- insight que só repete o título da nota;
- insight sem relação com fluxo de ideias/contexto.

### Critério

Se o insight não tiver evidência, ele deve ser marcado como inválido ou não exibido como insight real.

---

## 10. Qualidade dos Insights

Insights devem ser úteis para assimilação de conhecimento.

Eles devem incluir pelo menos um destes tipos de valor:

1. Lacuna — Algo que falta na base.
2. Crítica — Algo inconsistente, fraco, superficial ou mal conectado.
3. Conexão — Relação não óbvia entre notas/conceitos.
4. Contexto — Explicação de como um assunto se encaixa em outro.
5. Agregação — União de várias notas em uma ideia maior.
6. Sugestão — Próxima ação concreta para aprender melhor.
7. Revisão — Algo que deveria virar pergunta/flashcard.
8. Expansão — Algo que pode virar novo nó, nota permanente ou trilha.
9. Contradição — Possível conflito entre notas.
10. Fonte externa/opcional — Sugestão de pesquisa externa, se o recurso estiver habilitado.

### Observação sobre fonte externa

O BerryBrain deve continuar local por padrão.

Busca externa/internet só deve acontecer se houver configuração explícita ativada pelo usuário, como:

```txt
Enriquecimento externo
```

ou:

```txt
Research mode
```

Se habilitado, insights podem conter:

- sugestão de pesquisar fonte externa;
- termo de busca recomendado;
- referência adicionada manualmente;
- link/fonte se o sistema tiver mecanismo de busca configurado.

Se desabilitado, o insight pode sugerir:

```txt
Pesquisar externamente sobre X
```

mas não deve chamar internet automaticamente.

---

## 11. Prompt de Insight Real

Criar ou atualizar prompt versionado:

```txt
prompts/insight-generate.v1.md
```

O prompt deve instruir o modelo a gerar insights reais, não resumos genéricos.

### Prompt base sugerido

```txt
Você é o motor de insights do BerryBrain.

Seu objetivo é ajudar o usuário a assimilar conhecimento, detectar lacunas, entender conexões e expandir o grafo de conhecimento.

Não gere insights genéricos.
Não apenas resuma a nota.
Não repita o título da nota.
Não invente relações sem evidência.

Analise as notas, conceitos, conexões e contexto fornecidos.

Gere insights que sejam:
- específicos;
- baseados em evidências;
- conectados a notas reais;
- úteis para estudo;
- acionáveis;
- explicáveis;
- relacionados ao grafo de conhecimento.

Tipos permitidos:
- lacuna;
- conexão;
- crítica;
- contexto;
- agregação;
- revisão;
- contradição;
- expansão;
- nota permanente sugerida;
- trilha de estudo.

Cada insight deve retornar JSON com:

{
  "type": "...",
  "title": "...",
  "description": "...",
  "reasoning": "...",
  "evidence": [
    {
      "noteId": "...",
      "quoteOrSummary": "...",
      "whyRelevant": "..."
    }
  ],
  "relatedConcepts": [],
  "suggestedAction": {
    "type": "...",
    "label": "...",
    "payload": {}
  },
  "graphImpact": {
    "nodesToCreate": [],
    "connectionsToCreate": [],
    "notesToConnect": []
  },
  "priority": "low|medium|high",
  "confidence": 0.0
}

Se não houver evidência suficiente, retorne:
{
  "insights": [],
  "reason": "Não há evidência suficiente para gerar insights reais."
}
```

---

## 12. Insights Baseados em Fluxo de Ideias

O sistema deve considerar fluxo de ideias, não só similaridade semântica.

Para gerar insights, use:

- notas recentes;
- notas centrais;
- notas órfãs;
- conceitos recorrentes;
- conceitos sem nota permanente;
- conexões fracas;
- conexões fortes;
- histórico de revisão;
- tópicos emergentes;
- anexos processados;
- sequência temporal de estudo;
- clusters do grafo.

### Exemplo com as notas atuais

Notas:

- linux-shell-scripting.md;
- docker-essentials.md;
- python-async-patterns.md.

Insight ruim:

```txt
Essas notas são sobre tecnologia.
```

Insight bom:

```txt
As três notas indicam um fluxo de estudo sobre automação de ambientes: Shell scripting fornece automação local, Docker isola e reproduz ambientes, e Python async permite orquestrar tarefas concorrentes. Uma lacuna provável é uma nota permanente sobre automação de pipelines locais.
```

Ação:

```txt
Criar nota permanente: “Automação local com Shell, Docker e Async Python”
```

Impacto no grafo:

```txt
Criar nó conceitual “automação de ambientes” e conectar as três notas.
```

---

## 13. Insights com Ações Reais

Cada insight deve ter pelo menos uma ação.

### Ações possíveis

- criar nota permanente;
- criar conexão;
- confirmar conexão;
- ignorar conexão;
- gerar revisão;
- criar flashcards;
- abrir notas relacionadas;
- destacar no grafo;
- reprocessar com outro modelo;
- pesquisar externamente, se permitido;
- criar trilha de estudo;
- marcar como resolvido;
- ignorar.

As ações devem ter efeito real.

### Exemplos

Ação “Criar nota permanente”:

- deve criar arquivo `.md` em `permanentes/` com título sugerido e conteúdo inicial baseado no insight.

Ação “Destacar no grafo”:

- deve abrir grafo com nós relacionados em destaque.

Ação “Gerar revisão”:

- deve criar flashcards/perguntas baseados no insight.

Ação “Confirmar conexão”:

- deve transformar conexão `suggested` em `confirmed`.

Ação “Ignorar”:

- deve ocultar ou marcar insight como `ignored`.

---

## 14. Validação dos Jobs de Insight

Audite os jobs listados atualmente:

- GENERATE_GRAPH_INSIGHTS;
- EXTRACT_CONTEXT;
- DETECT_TOPICS;
- EXTRACT_ENTITIES;
- EXTRACT_CONCEPTS;
- ASSIMILATE_NOTE;
- GENERATE_INFERRED_CONNECTIONS;
- EXPAND_KNOWLEDGE_GRAPH.

Para cada job, verificar:

- entrada real;
- saída real;
- provider/model;
- status;
- erro;
- onde o resultado é salvo;
- onde aparece na UI;
- se resultado alimenta grafo;
- se resultado alimenta insights;
- se resultado alimenta Home;
- se resultado alimenta painel da nota.

### Relatório

| Job | Entrada real? | Saída real? | Persistido? | Aparece na UI? | Problema |
|---|---|---|---|---|---|

Se algum job apenas muda status, mas não salva resultado útil, corrigir.

---

## 15. Home Deve Mostrar Resultados, Não Apenas Jobs

A Home não deve mostrar apenas que jobs rodaram.

Ela deve mostrar o que foi descoberto.

### Trocar mensagens técnicas por resultados

Em vez de:

```txt
GENERATE_GRAPH_INSIGHTS concluído
```

Mostrar:

```txt
2 insights de grafo gerados
1 lacuna detectada
3 conexões sugeridas
Conceito “automação de ambientes” emergiu em 3 notas
```

### A Home deve ter

1. Insights da IA — Cards reais.
2. Conceitos emergentes — Conceitos extraídos e recorrentes.
3. Conexões recentes — Conexões reais com motivo.
4. Grafo vivo — Nós, conexões, órfãs, clusters, última atualização.
5. Processamento — Jobs apenas como status resumido.
6. Precisa de atenção — Apenas se houver problema real.

---

## 16. Monitor Não Deve Ser Destino Universal

Corrigir roteamento para que Monitor não seja destino universal.

### Regras

- Ver atividade → `/activity`
- Ver insights → `/insights`
- Ver grafo → `/graph`
- Sino → `NotificationsPopover` ou `/notifications`
- Monitor → `/monitor`
- Precisa de atenção → `/attention` ou filtro em `/activity/errors`, se existir
- Recalcular conexões → ação específica + status
- Ver órfãs → `/graph?filter=orphans`

### Critério

Cada botão deve levar ao contexto certo.

---

## 17. “Precisa de Atenção” — Decisão de UX

Avalie se “Precisa de atenção” é necessário.

### Regra recomendada

- Se não houver item real de atenção, ocultar a seção.
- Se houver, mostrar seção compacta com ações.
- Não mostrar card grande apenas com “Tudo certo.”
- “Tudo certo” pode aparecer como badge discreto no Autopilot.

### Itens que justificam “Precisa de atenção”

- erro de job;
- provider offline;
- timeout do NVIDIA NIM;
- insights críticos não lidos;
- conexões sugeridas aguardando aprovação;
- notas órfãs acima de limite;
- notas não assimiladas;
- anexos com erro;
- grafo desatualizado;
- revisões vencidas;
- erro de autosave;
- erro de vault.

Cada item deve ter:

- motivo;
- impacto;
- ação.

### Exemplo

```txt
2 jobs falharam ao gerar insights

Impacto:
Algumas conexões podem não aparecer no grafo.

Ação:
Tentar novamente
```

---

## 18. Testes Obrigatórios

Criar ou executar testes para:

### Teste 1 — Botão Ver insights

- Deve abrir `/insights`.
- Não deve abrir Monitor.

### Teste 2 — Botão Ver atividade

- Deve abrir `/activity`.
- Não deve abrir Monitor.

### Teste 3 — Sino

- Deve abrir notificações.
- Não deve mostrar Monitor completo.

### Teste 4 — Insight real

- Criar notas `linux-shell-scripting`, `docker-essentials` e `python-async-patterns`.
- Rodar assimilação.
- Gerar insights.
- Verificar que insight cita as notas.
- Verificar que insight tem reasoning/evidence/action.
- Verificar provider/model.
- Verificar que aparece na Home e `/insights`.

### Teste 5 — Insight genérico

- Se insight não tiver evidência, não exibir como insight real.

### Teste 6 — Ação do insight

- Criar nota permanente a partir de insight.
- Destacar no grafo.
- Gerar revisão.
- Ignorar insight.

### Teste 7 — Precisa de atenção

- Sem erros: seção oculta ou badge discreto.
- Com erro: seção aparece com ação.

### Teste 8 — Atividade automática

- Jobs técnicos aparecem como timeline compreensível.
- Modo técnico ainda acessível.

### Teste 9 — Monitor

- Monitor continua existindo para dados técnicos.
- Não substitui Insights/Atividade/Notificações.

---

## 19. Critérios de Pronto

A correção só está pronta se:

- Ver insights abre tela de insights real.
- Ver atividade abre tela de atividade real.
- Sino mostra notificações, não Monitor.
- Monitor é apenas monitor técnico.
- Insights são gerados pela IA configurada local/cloud.
- Insights têm provider/model/promptVersion.
- Insights têm evidência.
- Insights têm ação.
- Insights não são genéricos.
- Insights aparecem na Home.
- Insights aparecem em `/insights`.
- Insights aparecem no painel da nota quando relacionados.
- Insights podem destacar nós no grafo.
- Jobs de insight salvam resultado real.
- Home mostra descobertas, não apenas jobs.
- Precisa de atenção só aparece quando há algo relevante.
- Cada botão leva ao contexto correto.
- Nada importante é mock/hardcoded.

---

## 20. Resumo do que o Codex Deve Corrigir

```txt
1. Separar Monitor, Insights, Atividade e Notificações.
2. Fazer “Ver insights” abrir insights reais.
3. Fazer “Ver atividade” abrir timeline real.
4. Fazer o sino mostrar notificações úteis, não monitor.
5. Validar se os insights são gerados por IA real.
6. Impedir insights genéricos.
7. Exigir evidência, contexto, ação e provider/model.
8. Fazer a Home mostrar descobertas, não só jobs.
9. Ocultar “Precisa de atenção” quando não houver atenção real.
10. Garantir que cada ação da Home leve ao destino correto.
```

---

## 21. Resultado Esperado

Depois dessa correção, o usuário deve conseguir entender claramente:

- onde ficam os insights;
- quais insights são reais;
- qual modelo gerou cada insight;
- quais notas sustentam cada insight;
- quais ações podem ser tomadas;
- o que é Monitor;
- o que é Atividade;
- o que é Notificação;
- o que é Insight;
- o que realmente precisa de atenção.

A Home deve deixar de ser apenas um painel de jobs e passar a ser o resumo do que o segundo cérebro aprendeu, conectou, criticou e sugeriu.
