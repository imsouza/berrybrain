# BerryBrain Node Summary v1

Generate an intelligent summary for a knowledge-graph node.

You receive:
- The node, including its type, label, source notes, and metadata
- Connections from the node to other nodes
- Related notes

Generate a summary that:
1. Explains what the node represents in the graph context
2. Highlights its most relevant connections
3. Identifies related knowledge gaps
4. Suggests notes to expand or create

Return valid JSON in English:

```json
{
  "summary": "A two- or three-sentence English explanation of what this node represents.",
  "key_connections": [
    {
      "target_label": "Connected node name",
      "type": "canonical connection type",
      "significance": "Why this connection matters"
    }
  ],
  "gaps": [
    "Identified knowledge gap"
  ],
  "suggested_actions": [
    "Create a note about X to strengthen this node",
    "Connect it to topic Y"
  ],
  "centrality_estimate": 0.75
}
```

Be concise. Estimate centrality from zero to one using the number and relevance of connections.
