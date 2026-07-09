# BerryBrain Node Summary v1

Gere um resumo inteligente para um no do grafo de conhecimento.

Voce recebe:
- O no (tipo, label, notas fonte, metadata)
- Conexoes do no com outros nos
- Notas relacionadas

Gere um resumo que:
1. Explique o que este no representa no contexto do grafo
2. Destaque as conexoes mais relevantes
3. Identifique lacunas de conhecimento relacionadas
4. Sugira quais notas expandir ou criar

Retorne JSON valido:

```json
{
  "summary": "Resumo de 2-3 frases em portugues do Brasil explicando o que este no representa.",
  "key_connections": [
    {
      "target_label": "Nome do no conectado",
      "type": "tipo da conexao",
      "significance": "Por que esta conexao e importante"
    }
  ],
  "gaps": [
    "Lacuna de conhecimento identificada"
  ],
  "suggested_actions": [
    "Criar nota sobre X para fortalecer este no",
    "Conectar com topico Y"
  ],
  "centrality_estimate": 0.75
}
```

Seja conciso. Centralidade estimada entre 0 e 1, baseada no numero e relevancia das conexoes.
