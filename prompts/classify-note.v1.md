# BerryBrain Classify Note v1

Classifique a nota informada.

Campos esperados:

```json
{
  "language": "pt-BR",
  "note_type": "study",
  "tags": ["tag"],
  "aliases": ["alias"],
  "technical_terms": ["embedding"],
  "confidence": 0.9
}
```

Use `note_type` com valores simples, como `study`, `permanent`, `reference`, `fleeting`, `review` ou `unknown`.
