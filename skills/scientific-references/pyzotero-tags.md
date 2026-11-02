---
id: sciref-pyzotero-tags
name: "Scientific Ref: Tag Management"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pyzotero): Tag Management"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pyzotero tags"
  - "tag management"
keywords:
  - "pyzotero"
  - "tags"
  - "specialized"
  - "scientific"
  - "reference"
  - "management"
---

# Tag Management

## Retrieving Tags

```python
# All tags in the library
tags = zot.everything(zot.tags())
# Returns list of strings: ['climate change', 'machine learning', ...]

# Tags for a specific item
item_tags = zot.item_tags('ITEMKEY')

# Tags in a specific collection
col_tags = zot.collection_tags('COLKEY')

# Filter tags by prefix (e.g. all tags starting with 'bio')
filtered = zot.tags(q='bio', qmode='startsWith')
```

## Adding Tags to Items

```python
# Add one or more tags to an item (retrieves item first)
item = zot.item('ITEMKEY')
success = zot.add_tags(item, 'tag1', 'tag2', 'tag3')  # Boolean, not updated data

# Add a list of tags
tag_list = ['reviewed', 'high-priority', '2024']
item = zot.item('ITEMKEY')  # re-fetch after the earlier write
success = zot.add_tags(item, *tag_list)
```

## Deleting Tags

```python
# Delete specific tags from the library
zot.delete_tags('old-tag', 'unused-tag')

# Delete a list of tags
tags_to_remove = ['deprecated', 'temp']
zot.delete_tags(*tags_to_remove)
```

## Searching Items by Tag

```python
# Items with a single tag
items = zot.items(tag='machine learning')

# Items with multiple tags (AND logic)
items = zot.items(tag=['climate', 'adaptation'])

# Items with any of these tags (OR logic)
items = zot.items(tag='climate || sea level')

# Items NOT having a tag
items = zot.items(tag='-retracted')
```

## Batch Tag Operations

```python
# Add a tag to all items in a collection
items = zot.everything(zot.collection_items('COLKEY'))
for item in items:
    zot.add_tags(item, 'collection-reviewed')

# Find all items with a specific tag and retag them
old_tag_items = zot.everything(zot.items(tag='old-name'))
for item in old_tag_items:
    # Add new tag
    item['data']['tags'].append({'tag': 'new-name'})
    # Remove old tag
    item['data']['tags'] = [t for t in item['data']['tags'] if t['tag'] != 'old-name']
# Capture per-object status rather than update_items()'s coarse Boolean.
for start in range(0, len(old_tag_items), 50):
    result = zot.create_items([i['data'] for i in old_tag_items[start:start + 50]])
    if result.get('failed'):
        raise RuntimeError(result['failed'])
```

## Tag Types

Zotero has two tag types stored in `tag['type']`:
- `0` — User-added tags (default)
- `1` — Automatically imported tags (from bibliographic databases)

```python
item = zot.item('ITEMKEY')
for tag in item['data']['tags']:
    print(tag['tag'], tag.get('type', 0))
```

Tag deletion removes the named tags throughout the library (up to 50 per call); it does not delete the items. `tags()` returns strings and discards API tag metadata. Use each item's `data.tags` to inspect tag types.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

