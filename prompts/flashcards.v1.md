# BerryBrain Flashcards v1

Gere flashcards de estudo ativo a partir da nota.

Regras:

- perguntas claras;
- respostas curtas, mas completas;
- evitar perguntas triviais;
- preservar termos tecnicos em ingles quando fizer sentido;
- priorizar conceitos, relacoes e aplicacoes.

Formato esperado:

```json
{
  "flashcards": [
    {
      "question": "Pergunta",
      "answer": "Resposta",
      "difficulty": "medium",
      "topic": "Tópico ou conceito principal"
    }
  ]
}

O campo "topic" deve ser o nome do conceito, área ou categoria do flashcard (ex: "K-Means", "Regressão Linear", "Python Decorators"). Agrupe flashcards por tópico quando possível.
```
