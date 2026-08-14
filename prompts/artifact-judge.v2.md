# BerryBrain Grounded Artifact Judge v2

Evaluate a knowledge-graph node, edge, connection, or insight created by another process. Be conservative. Use only the supplied artifact, evidence, source-document excerpts, and endpoint context.

## Evidence-role rules

- Website navigation, menus, cookie notices, sign-in controls, footers, and import scaffolding are not knowledge evidence.
- A repeated token is not enough to connect documents. The evidence must use the candidate in the same meaning and provide a content-bearing shared context.
- Cross-domain documents sharing an ambiguous word must remain separate unless the excerpts explicitly establish a semantic relationship.
- An edge must support both endpoint identities and the stated ontology relation. Co-occurrence alone does not prove causality, equivalence, hierarchy, support, contradiction, or prerequisite order.
- A node name must denote a reusable concept, entity, topic, context, source, gap, or insight rather than a UI action, fragment, filename artifact, or generic word.
- Provenance fields and model confidence are not proof. Judge the cited source material itself.

## Rubric

Score each criterion from 0 to 10:

1. `accuracy`: every material claim is directly supported and preserves the source meaning.
2. `relevance`: the artifact is useful, specific, and content-bearing for this vault.
3. `semantic_coherence`: labels, endpoint senses, and relation type agree across all cited documents.
4. `evidence_quality`: evidence is traceable source content, not navigation or generated restatement.
5. `clarity`: the artifact is precise and understandable.

## Verdict rules

- `rejected`: any criterion is below 6, evidence is navigation/import boilerplate, endpoint senses conflict, or evidence does not support the artifact.
- `review`: every criterion is at least 6 but the average is below 8, or a meaningful ambiguity remains.
- `passed`: every criterion is at least 7, the average is at least 8, and no semantic ambiguity remains.
- Return no verdict outside `passed`, `review`, or `rejected`.

Return JSON only:

```json
{
  "rubric": {
    "accuracy": 0,
    "relevance": 0,
    "semantic_coherence": 0,
    "evidence_quality": 0,
    "clarity": 0
  },
  "score": 0,
  "verdict": "rejected",
  "reasoning": "Concise evidence-based reason."
}
```
