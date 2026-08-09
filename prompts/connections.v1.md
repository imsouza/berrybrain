# BerryBrain Connections v1

Analyze the source note and suggest connections to candidate notes.

Return only connections with clear evidence-based justification.

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
      "target": "note-slug",
      "type": "related",
      "confidence": 0.82,
      "reason": "Short justification in English."
    }
  ]
}
```
