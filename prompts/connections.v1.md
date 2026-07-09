# BerryBrain Connections v1

Analise a nota de origem e sugira conexoes com outras notas candidatas.

Retorne apenas conexoes que tenham justificativa clara.

Tipos permitidos:

- semantic
- prerequisite
- related
- duplicate
- contrast
- example
- application

Formato esperado:

```json
{
  "connections": [
    {
      "target": "slug-da-nota",
      "type": "related",
      "confidence": 0.82,
      "reason": "Justificativa curta em portugues do Brasil."
    }
  ]
}
```
