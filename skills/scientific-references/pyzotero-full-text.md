---
id: sciref-pyzotero-full-text
name: "Scientific Ref: Full-Text Content"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pyzotero): Full-Text Content"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pyzotero full text"
  - "full-text content"
keywords:
  - "pyzotero"
  - "full"
  - "text"
  - "specialized"
  - "scientific"
  - "reference"
---

# Full-Text Content

Pyzotero can retrieve and set full-text index content for attachment items.

## Retrieving Full-Text Content

```python
# Get full-text content for a specific attachment item
data = zot.fulltext_item('ATTACHMENTKEY')
# Returns:
# {
#   "content": "Full text of the document...",
#   "indexedPages": 50,
#   "totalPages": 50
# }
# For text docs: indexedChars/totalChars instead of pages

text = data['content']
unit = 'Pages' if 'totalPages' in data else 'Chars'
total = data.get('total' + unit, 0)
coverage = data.get('indexed' + unit, 0) / total if total else None
```

## Finding Items with New Full-Text Content

```python
# Get item keys with full-text updated since a library version
new_fulltext = zot.new_fulltext(since=1085)
# Returns dict: {'KEY1': 1090, 'KEY2': 1095, ...}
# Values are the library version at which full-text was indexed
```

## Setting Full-Text Content

```python
# Set full-text for a PDF attachment
payload = {
    'content': 'The full text content of the document.',
    'indexedPages': 50,
    'totalPages': 50
}
zot.set_fulltext('ATTACHMENTKEY', payload)

# For text documents use indexedChars/totalChars
payload = {
    'content': 'Full text here.',
    'indexedChars': len('Full text here.'),
    'totalChars': len('Full text here.')
}
zot.set_fulltext('ATTACHMENTKEY', payload)
```

## Full-Text Search via CLI

The CLI provides full-text search across locally indexed PDFs:

```bash
# Search full-text content
pyzotero search -q "CRISPR gene editing" --fulltext

# Output as JSON (retrieves parent bibliographic items for attachments)
pyzotero search -q "climate tipping points" --fulltext --json
```

## Search in API (qmode=everything)

```python
# Search in titles/creators + full-text content
results = zot.items(q='protein folding', qmode='everything', limit=20)
```

`fulltext_item()` sends GET to `/items/{attachmentKey}/fulltext`; a 404 can mean missing indexed content as well as a missing item. `new_fulltext()` uses `/fulltext?since=<version>` and returns a key-to-version dict. `set_fulltext()` PUTs the supplied index and returns Boolean success; it does not extract text from a PDF. Supply the actual extracted content and coverage, not guessed counts. Remote search sees synced indexed content; local search sees the local index and can differ. Keep local server versions separate from Web API versions. [Official full-text contract](https://www.zotero.org/support/dev/web_api/v3/fulltext_content).

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

