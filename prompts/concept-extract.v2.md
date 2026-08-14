# BerryBrain Grounded Knowledge Extraction v2

Extract reusable knowledge artifacts from the supplied note. Generate names and descriptions in English. Preserve exact source wording only inside evidence fields.

## Exclude

- navigation such as `Skip to content`, menus, breadcrumbs, sign-in controls, and buttons;
- cookie notices, footers, legal boilerplate, advertisements, and import scaffolding;
- generic verbs, isolated UI words, filenames, paths, and formatting fragments;
- a single ambiguous word unless the note defines or discusses it as a domain concept;
- inferred relationships or meanings that the note does not explicitly support.

## Types

- `concepts`: reusable ideas, techniques, frameworks, principles, or named mechanisms;
- `entities`: people, organizations, tools, technologies, products, places, or named works;
- `topics`: broad subject areas that organize the note;
- `context`: application domain, prerequisites, and explicit applications.

Every concept and entity must include an exact content-bearing excerpt from the note. The excerpt cannot be navigation or generated restatement. Prefer no candidate over a weak candidate.

Return JSON only:

```json
{
  "concepts": [
    {
      "name": "Concept name",
      "description": "Short grounded description",
      "confidence": 0.9,
      "evidence": "Exact source excerpt"
    }
  ],
  "entities": [
    {
      "name": "Entity name",
      "type": "tool",
      "description": "Grounded role in this note",
      "confidence": 0.85,
      "evidence": "Exact source excerpt"
    }
  ],
  "topics": [
    {
      "name": "Topic name",
      "scope": "Grounded scope within this note",
      "confidence": 0.8,
      "evidence": "Exact source excerpt"
    }
  ],
  "context": {
    "domain": "Primary domain supported by the note",
    "prerequisites": [],
    "applications": [],
    "evidence": "Exact source excerpt"
  },
  "confidence": 0.85
}
```

Allowed entity types: `tool`, `person`, `organization`, `language`, `framework`, `platform`, `protocol`, `standard`, `product`, `place`, `work`, and `other`.

Minimum candidate confidence: 0.6.
