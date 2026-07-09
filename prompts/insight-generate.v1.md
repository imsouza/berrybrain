# BerryBrain Insight Generate v1

Gere insights reais sobre o segundo cerebro do usuario. Analise notas, vertices e conexoes para encontrar padroes, lacunas e oportunidades.

REGRAS ESTRITAS:
- Use APENAS as evidencias fornecidas. Nao invente.
- Cada insight DEVE ter type, title, description, priority, confidence E evidence.
- NAO repita o mesmo tipo para todos os insights. Varie entre context, conclusion, hypothesis, premise, assertion, knowledge_gap, new_connection, study_path.
- Priority: 1-10. Nao use o mesmo valor para todos. Use 10 apenas para insights muito urgentes, 5 para medio, 1-3 para interessantes.
- Confidence: 0.1 a 0.99. Avalie honestamente quao seguro voce esta. 0.5 = moderado. 0.8+ = muito confiante. 0.3- = especulativo.
- Title: frase descritiva e especifica em portugues. NUNCA use o tipo como titulo.
- Description: 2-3 frases explicando o insight com clareza.

Tipos de insight — use PELO MENOS 3 tipos diferentes por chamada:

- **context** — O pano de fundo comum entre notas. Ex: "Cluster DevOps: Docker, Shell e Python formam o nucleo de automacao do usuario."
- **conclusion** — O que os dados permitem afirmar com seguranca. Ex: "Python aparece como linguagem de orquestracao entre Docker e scripts."
- **hypothesis** — Relacao plausivel mas nao confirmada. Ex: "O usuario pode estar migrando de scripts shell para automacao em Python."
- **premise** — Ideia-base recorrente nas notas. Ex: "Containerizacao e tratada como padrao em todas as notas de infra."
- **assertion** — Proposicao sustentada por ao menos 2 evidencias. Ex: "Backlinks confirmam que o usuario conecta Docker a Linux Shell."
- **knowledge_gap** — Conhecimento ausente ou fragil. Ex: "Falta nota sobre orquestracao com docker-compose ou Kubernetes."
- **new_connection** — Relacao nao obvia com motivo. Ex: "Async Python conecta-se a Docker via conceito de escalabilidade."
- **study_path** — Sequencia logica de estudo. Ex: "Trilha sugerida: Shell basico → Docker essentials → Python async → FastAPI deploy."

Retorne JSON valido:

```json
{
  "insights": [
    {
      "type": "context",
      "title": "Titulo descritivo em portugues — NAO use o tipo como titulo",
      "description": "2-3 frases de analise",
      "priority": 7,
      "why_it_matters": "Por que este insight importa para o aprendizado",
      "evidence": ["nota/caminho.md", "conexao X-Y", "vertice: nome"],
      "suggested_action": "Acao concreta: criar nota X, revisar Y, conectar A com B",
      "graph_impact": "Como afeta o grafo (fortalece nos, cria conexoes, preenche lacunas)",
      "confidence": 0.82,
      "related_notes": ["caminho-da-nota.md"]
    }
  ]
}
```

Maximo 5 insights por chamada. Apenas insights com confidence >= 0.3.
Prioridade e confianca DEVEM ser numeros, nunca strings.
Todo insight deve ter pelo menos 2 evidences.
Se nao houver dados suficientes, retorne `{"insights":[]}`.