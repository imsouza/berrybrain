# BerryBrain Classify Note v1

Classify the supplied note.

Expected fields:

```json
{
  "language": "en",
  "note_type": "study",
  "tags": ["tag"],
  "aliases": ["alias"],
  "technical_terms": ["embedding"],
  "confidence": 0.9
}
```

Use simple `note_type` values: `study`, `permanent`, `reference`, `fleeting`, `review`, or `unknown`.
