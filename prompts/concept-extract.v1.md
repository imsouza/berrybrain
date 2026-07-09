# BerryBrain Concept Extract v1

Extraia conceitos, entidades, topicos e contexto de uma nota.

Voce recebe o conteudo completo da nota.

Extraia:

**Conceitos** — ideias, tecnicas, frameworks, principios
**Entidades** — pessoas, organizacoes, ferramentas, tecnologias
**Topicos** — areas tematicas amplas
**Contexto** — dominio de aplicacao, pre-requisitos, ambiente

Retorne JSON valido:

```json
{
  "concepts": [
    {
      "name": "Nome do conceito",
      "description": "Definicao ou descricao curta",
      "confidence": 0.9,
      "evidence": "Trecho da nota que menciona o conceito"
    }
  ],
  "entities": [
    {
      "name": "Nome da entidade",
      "type": "tool",
      "description": "O que e esta entidade",
      "confidence": 0.85
    }
  ],
  "topics": [
    {
      "name": "Nome do topico",
      "scope": "Ambito do topico nesta nota",
      "confidence": 0.8
    }
  ],
  "context": {
    "domain": "Dominio principal da nota",
    "prerequisites": ["Conhecimento previo necessario"],
    "applications": ["Onde este conhecimento se aplica"]
  },
  "confidence": 0.85
}
```

Tipos de entidade: `tool`, `person`, `organization`, `language`, `framework`, `platform`, `protocol`, `standard`, `other`.

Nao invente conceitos. Use apenas o que esta explicitamente na nota.
Confianca minima: 0.5.
