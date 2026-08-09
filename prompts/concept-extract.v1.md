# BerryBrain Concept Extract v1

Extract concepts, entities, topics, and context from a note.

You receive the note's complete content.

Extract:

**Concepts** — ideas, techniques, frameworks, and principles
**Entities** — people, organizations, tools, and technologies
**Topics** — broad subject areas
**Context** — application domain, prerequisites, and environment

Return valid JSON. Keep all generated names and descriptions in English, while quoting source evidence exactly as written:

```json
{
  "concepts": [
    {
      "name": "Concept name",
      "description": "Short definition or description",
      "confidence": 0.9,
      "evidence": "Exact excerpt from the note"
    }
  ],
  "entities": [
    {
      "name": "Entity name",
      "type": "tool",
      "description": "What this entity is",
      "confidence": 0.85
    }
  ],
  "topics": [
    {
      "name": "Topic name",
      "scope": "The topic's scope within this note",
      "confidence": 0.8
    }
  ],
  "context": {
    "domain": "The note's primary domain",
    "prerequisites": ["Required prior knowledge"],
    "applications": ["Where this knowledge applies"]
  },
  "confidence": 0.85
}
```

Entity types: `tool`, `person`, `organization`, `language`, `framework`, `platform`, `protocol`, `standard`, and `other`.

Do not invent concepts. Extract only what the note explicitly supports.
Minimum confidence: 0.5.
