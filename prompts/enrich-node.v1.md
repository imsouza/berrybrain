You are enriching a knowledge graph node with semantic context.

## Node to enrich

- **Label**: {label}
- **Type**: {node_type}
- **Title**: {title}
- **Source**: {source}
- **Existing summary**: {summary}
- **Why this node exists**: {why_this_exists}
- **Source evidence**: {source_evidence}
- **Related source notes**: {source_notes}
- **Explained connections**: {connections}

## Your task

Generate enrichment data for this node. Return ONLY valid JSON. Use the provided source notes, source evidence, and connections. Do not answer from general knowledge alone.

```json
{{
  "ai_summary": "A 1-2 sentence summary of what this concept/node represents in the user's knowledge base",
  "ai_context": "Why this concept matters and how it connects to the broader knowledge domain",
  "source_evidence": ["Key evidence, note title, path, or connection reason that justifies this node's existence"],
  "learning_value": "high|medium|low — how valuable is this concept for the user to retain?",
  "source_quality": "verified|plausible|uncertain — how reliable is the source information?",
  "reasoning": "Brief explanation of why you assigned this learning_value"
}}
```

## Rules

- ai_summary must be concrete, not generic. Reference the specific source if available.
- ai_context should explain the concept's relevance, not restate the label.
- source_evidence must be a non-empty array.
- If there is no source evidence, set source_quality to "uncertain" and explain the missing evidence in ai_context.
- learning_value: high = core concept worth memorizing, medium = useful context, low = reference only.
- Be honest about uncertainty. If the label is ambiguous, say so in ai_context.
- Never return empty strings for ai_summary, ai_context, or source_evidence.
