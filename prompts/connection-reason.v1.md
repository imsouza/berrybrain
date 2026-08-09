# BerryBrain Connection Reason v1

Explain whether two knowledge-graph nodes should be connected.

You receive:
- A source node with its label, type, summary, and source notes
- A target node with its label, type, summary, and source notes
- Additional graph context, including existing connections and nearby topics

Determine:
1. Whether the connection is meaningful and why
2. The most appropriate canonical connection type
3. The connection confidence
4. The evidence supporting the connection

Return valid JSON:

```json
{
  "should_connect": true,
  "edge_type": "semantic_relation",
  "reason": "Both concepts address...",
  "confidence": 0.82,
  "evidence": [
    "Both source notes mention X",
    "They share context Y"
  ],
  "notes": "Optional additional observation about the connection"
}
```

When no meaningful connection exists, return:

```json
{
  "should_connect": false,
  "reason": "The evidence does not establish a meaningful relationship between these concepts.",
  "confidence": 0
}
```

Valid canonical connection types: `explicit_link`, `semantic_relation`, `prerequisite`, `example_of`, `contrasts_with`, `duplicates`, `applies_to`, `derived_from`, `mentions`, `supports`, and `contradicts`.
