---
id: sciref-pyzotero-files-attachments
name: "Scientific Ref: Files & Attachments"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pyzotero): Files & Attachments"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pyzotero files attachments"
  - "files & attachments"
keywords:
  - "pyzotero"
  - "files"
  - "attachments"
  - "specialized"
  - "scientific"
  - "reference"
---

# Files & Attachments

## Downloading Files

```python
# Get raw binary content of an attachment
raw = zot.file('ATTACHMENTKEY')
with open('paper.pdf', 'wb') as f:
    f.write(raw)

# Convenient wrapper: dump file to disk
# Uses stored filename, saves to current directory
zot.dump('ATTACHMENTKEY')

# Dump to a specific path and filename
zot.dump('ATTACHMENTKEY', 'renamed_paper.pdf', 'papers')
# Create the directory first. Returns None on success, not a path.
```

`dump()` uses the provided filename or stored attachment filename. For responses classified as HTML snapshots, 1.15.2 appends `.zip` to that name; ZIP/EPUB handling can return an archive member. Verify the saved bytes and type instead of assuming every snapshot is a ZIP or is named with its key. Remote `/file` downloads require stored, synced files and appropriate permissions; linked files are not uploaded to Zotero storage.

## Finding Attachments

```python
# Get child items (attachments, notes) of a parent item
children = zot.children('PARENTKEY')
attachments = [c for c in children if c['data']['itemType'] == 'attachment']

# Get the attachment key
for att in attachments:
    key = att['data']['key']
    filename = att['data'].get('filename')  # absent on linked URLs
    content_type = att['data']['contentType']
    link_mode = att['data']['linkMode']  # 'imported_file', 'linked_file', 'imported_url', 'linked_url'
```

## Uploading Attachments

**Note**: Upstream still labels attachment helpers beta. The simple/both helpers below require the remote API; local uploads need a manually built attachment dict and Zotero 10+ authorization (see [authentication.md](authentication.md)).

```python
# Simple upload: one or more files by path
result = zot.attachment_simple(['/path/to/paper.pdf', '/path/to/notes.docx'])

# Upload as child items of a parent
result = zot.attachment_simple(['/path/to/paper.pdf'], parentid='PARENTKEY')

# Upload with custom filenames: list of (name, path) tuples
result = zot.attachment_both([
    ('Paper 2024.pdf', '/path/to/paper.pdf'),
    ('Supplementary.pdf', '/path/to/supp.pdf'),
], parentid='PARENTKEY')

# Upload files to existing attachment items
result = zot.upload_attachments(attachment_items, basedir='/path/to/files/')
# Existing entries need editable attachment dicts with key + version;
# filename resolves on disk relative to basedir. Do not set parentid for existing items.
if result['failure']:
    raise RuntimeError(result['failure'])
```

Upload result structure:
```python
{
    'success': [attachment_item1, ...],
    'failure': [attachment_item2, ...],
    'unchanged': [attachment_item3, ...]
}
```

## Attachment Templates

```python
# Get template for a file attachment
template = zot.item_template('attachment', linkmode='imported_file')
# linkmode options: 'imported_file', 'linked_file', 'imported_url', 'linked_url'

# Available link modes
modes = zot.item_attachment_link_modes()
```

## Downloading All PDFs from a Collection

```python
import os

collection_key = 'COLKEY'
output_dir = '/path/to/output/'
os.makedirs(output_dir, exist_ok=True)

items = zot.everything(zot.collection_items_top(collection_key))
for item in items:
    # A top-level item can itself be a standalone attachment.
    children = ([item] if item['data']['itemType'] == 'attachment' else
                zot.everything(zot.children(item['data']['key'])))
    for child in children:
        if child['data']['itemType'] == 'attachment' and \
           child['data'].get('contentType') == 'application/pdf' and \
           child['data'].get('linkMode') in {'imported_file', 'imported_url'}:
            try:
                # Key-based filenames prevent collisions between identically named PDFs.
                zot.dump(child['key'], filename=f"{child['key']}.pdf", path=output_dir)
            except Exception as e:
                print(f"Failed to download {child['data']['key']}: {e}")
```

Upload results are distinct from `create_items()` results: lists under `success`, `failure`, and `unchanged`. Returned successful entries carry the current `version`; creation failures may include an `error` dict. The SDK manages file authorization, upload, and registration through `/items/{key}/file`, including MD5 preconditions and the storage URL returned by Zotero. A completed metadata create alone does not prove the file uploaded. See [official upload protocol](https://www.zotero.org/support/dev/web_api/v3/file_upload).

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

