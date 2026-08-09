# BerryBrain Graph Expand v1

Expand the knowledge graph from notes and metadata.

You receive one or more notes with content, frontmatter, links, and generated metadata such as classification, assimilation, and topics.

Extract nodes and connections using only the canonical English types below.

**Nodes:**
- `topic` — broad themes or study areas
- `context` — circumstances, prerequisites, or application environment
- `entity` — people, organizations, tools, or specific technologies
- `insight` — discoveries, conclusions, or patterns
- `gap` — missing knowledge or an unanswered question
- `source` — information origin, such as a book, article, course, or person

**Connections:**
- `explicit_link` — an explicit link in the source content
- `semantic_relation` — a meaningful semantic relationship
- `mentions` — a note mentions a concept or entity
- `supports` — evidence supports a claim or insight
- `contradicts` — evidence conflicts with a claim or insight
- `derived_from` — a concept or insight derives from a source
- `prerequisite` — one concept depends on another
- `example_of` — a node is an example of another
- `contrasts_with` — two nodes form a meaningful contrast
- `duplicates` — two nodes represent the same knowledge
- `applies_to` — knowledge applies to a context or subject

Return valid JSON. Generate labels, summaries, reasons, and metadata in English. Preserve source excerpts exactly as written:

```json
{
  "nodes": [
    {
      "type": "topic",
      "label": "Topic name",
      "summary": "Short description of what this topic represents",
      "confidence": 0.85,
      "evidence": ["exact source-note excerpt supporting this node"]
    }
  ],
  "edges": [
    {
      "source_label": "Source node name",
      "target_label": "Target node name",
      "type": "semantic_relation",
      "reason": "Short explanation of the connection",
      "confidence": 0.78,
      "evidence": ["exact excerpt supporting this connection"]
    }
  ]
}
```

Never invent nodes or connections without real evidence in the notes.
Minimum confidence: 0.5. Omit candidates below this threshold.
