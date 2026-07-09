# BerryBrain Graph Expand v1

Expanda o grafo de conhecimento a partir de notas e metadados.

Voce recebe uma ou mais notas com conteudo, frontmatter, links e metadados gerados (classificacao, assimilacao, topicos).

Extraia nos e conexoes nos seguintes tipos:

**Nos:**
- `topico` — temas amplos ou areas de estudo
- `contexto` — circunstancias, pre-requisitos ou ambiente de aplicacao
- `entidade` — pessoas, organizacoes, ferramentas, tecnologias especificas
- `insight` — descobertas, conclusoes ou padroes
- `lacuna` — ausencia de conhecimento ou pergunta nao respondida
- `fonte` — origem da informacao (livro, artigo, curso, pessoa)

**Conexoes:**
- `contem` — topico contem conceito ou subtopico
- `contexto_de` — contexto se aplica a conceito
- `referencia` — nota referencia entidade
- `evidencia_para` — nota fornece evidencia para insight
- `preenche` — nota preenche lacuna
- `derivado_de` — conceito deriva de fonte
- `similar_a` — conceitos similares
- `pre_requisito` — conceito depende de outro

Retorne JSON valido:

```json
{
  "nodes": [
    {
      "type": "topico",
      "label": "Nome do topico",
      "summary": "Descricao curta do que este topico representa",
      "confidence": 0.85,
      "evidence": ["trecho da nota que justifica este no"]
    }
  ],
  "edges": [
    {
      "source_label": "Nome do no origem",
      "target_label": "Nome do no destino",
      "type": "contem",
      "reason": "Justificativa curta da conexao",
      "confidence": 0.78,
      "evidence": ["trecho que justifica a conexao"]
    }
  ]
}
```

Nao invente nos ou conexoes sem evidencia real nas notas.
Confianca minima: 0.5. Abaixo disso, nao inclua.
