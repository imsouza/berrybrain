# BerryBrain Connection Reason v1

Explique por que dois nos do grafo devem ser conectados.

Voce recebe:
- No de origem com label, tipo, resumo e notas fonte
- No de destino com label, tipo, resumo e notas fonte
- Contexto adicional do grafo (conexoes existentes, topicos proximos)

Determine:
1. Se a conexao faz sentido e por que
2. O tipo mais adequado de conexao
3. A confianca da conexao
4. Evidencias que sustentam a conexao

Retorne JSON valido:

```json
{
  "should_connect": true,
  "edge_type": "similar_a",
  "reason": "Ambos os conceitos tratam de...",
  "confidence": 0.82,
  "evidence": [
    "Ambos mencionam X em suas notas fonte",
    "Compartilham o mesmo contexto Y"
  ],
  "notes": "Observacao adicional sobre a conexao (opcional)"
}
```

Se a conexao nao fizer sentido:

```json
{
  "should_connect": false,
  "reason": "Nao ha relacao significativa entre os conceitos.",
  "confidence": 0
}
```

Tipos de conexao validos: `similar_a`, `contem`, `contexto_de`, `referencia`, `evidencia_para`, `preenche`, `derivado_de`, `pre_requisito`, `relacionado_a`.
