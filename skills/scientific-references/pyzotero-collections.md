---
id: sciref-pyzotero-collections
name: "Scientific Ref: Collection Management"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pyzotero): Collection Management"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pyzotero collections"
  - "collection management"
keywords:
  - "pyzotero"
  - "collections"
  - "specialized"
  - "scientific"
  - "reference"
  - "collection"
  - "management"
---

# Collection Management

## Reading Collections

```python
# All collections (flat list including nested)
all_cols = zot.everything(zot.collections())

# Only top-level collections
top_cols = zot.collections_top()

# Specific collection
col = zot.collection('COLKEY')

# Sub-collections of a collection
sub_cols = zot.collections_sub('COLKEY')

# All collections under a given collection (recursive)
tree = zot.all_collections('COLKEY')
# Or all collections in the library:
tree = zot.all_collections()
```

## Collection Data Structure

```python
col = zot.collection('5TSDXJG6')
name = col['data']['name']
key = col['data']['key']
parent = col['data']['parentCollection']  # False if top-level, else parent key
version = col['data']['version']
n_items = col['meta']['numItems']
n_sub_collections = col['meta']['numCollections']
```

## Creating Collections

```python
# Create a top-level collection
zot.create_collections([{'name': 'My New Collection'}])

# Create a nested collection
zot.create_collections([{
    'name': 'Sub-Collection',
    'parentCollection': 'PARENTCOLKEY'
}])

# Create a parent, inspect the result, then use its real key for a child.
result = zot.create_collections([{'name': 'Collection B'}])
if result.get('failed'):
    raise RuntimeError(result['failed'])
parent_key = result['successful']['0']['key']
child_result = zot.create_collections([{'name': 'Sub-B', 'parentCollection': parent_key}])
if child_result.get('failed'):
    raise RuntimeError(child_result['failed'])
```

## Updating Collections

```python
cols = zot.collections()
# Rename the first collection, if there is one
if cols:
    cols[0]['data']['name'] = 'Renamed Collection'
    zot.update_collection(cols[0])

# For multiple collections, use individually versioned updates.
# Re-fetch after a prior write to avoid reusing the old version.
for col in cols:
    fresh = zot.collection(col['key'])
    fresh['data']['name'] = col['data']['name']
    zot.update_collection(fresh)
```

## Deleting Collections

```python
# Delete a single collection
col = zot.collection('COLKEY')
zot.delete_collection(col)

# Delete multiple collections
cols = zot.collections(limit=50)  # review the selected keys; max 50
library_version = int(zot.request.headers['Last-Modified-Version'])
if cols:
    zot.delete_collection(cols, last_modified=library_version)
```

## Managing Items in Collections

```python
# Add an item to a collection
item = zot.item('ITEMKEY')
zot.addto_collection('COLKEY', item)

# Remove an item from a collection (re-fetch after any earlier write)
item = zot.item('ITEMKEY')
zot.deletefrom_collection('COLKEY', item)

# Move between collections with one version-checked request
item = zot.item('ITEMKEY')
zot.moveto_collection('OLDCOLKEY', 'NEWCOLKEY', item)

# Get all items in a collection
items = zot.everything(zot.collection_items('COLKEY'))

# Get only top-level items in a collection
top_items = zot.collection_items_top('COLKEY')

# Count items in a collection
n = zot.num_collectionitems('COLKEY')

# Get tags in a collection
tags = zot.collection_tags('COLKEY')
```

## Find Collection Key by Name

```python
def find_collection(zot, name):
    for col in zot.everything(zot.collections()):
        if col['data']['name'] == name:
            return col['data']['key']
    return None

key = find_collection(zot, 'Machine Learning Papers')
```

Collection deletion also removes descendant collections, but preserves their items in the library. Create and batch-update responses use the same `successful`/`success`/`unchanged`/`failed` maps as items; creation accepts at most 50 collections per request.

In Pyzotero 1.15.2, `update_collections()` routes collection dictionaries through the item-field validator and can reject `name`/`parentCollection`; the per-collection `update_collection()` example avoids that path. Its single-object precondition is the collection version; multi-delete needs the library version.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

