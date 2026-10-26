---
id: sci-ontology-term-resolution
name: "Scientific: ontology-term-resolution"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Resolves free-text scientific labels to ontology term IDs and validates existing CURIEs against the EBI Ontology Lookup Service (OLS4). Also looks up prefixes in Bioregistry, resolves compact identifiers via Identifiers.org, maps lab shorthand with ZOOMA, and builds Ontobee term "
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "ontology term resolution"
  - "ontologia term resolution"
  - "ontology-term-resolution"
keywords:
  - "ontology"
  - "term"
  - "resolution"
  - "ontologia"
  - "resolves"
  - "free"
  - "text"
  - "scientific"
  - "labels"
---

# Ontology Term Resolution

## When to use

Any time an ontology identifier is about to be written down or trusted: annotating a metadata
column, filling a submission template, auditing a table someone else produced, or checking whether
an ID in an old file is still current.

## The rule

**Never write an ontology ID from memory, and never accept one without checking it.**

Ontology IDs are memorable in form and arbitrary in detail. A plausible-looking `UBERON:0002108`
is a real term (small intestine) that is not the liver, and nothing downstream will catch the
substitution — the ID is well-formed, the ontology is right, and the metadata is silently wrong.
Reviewers cannot spot it either, which is why these errors persist into published datasets.

OLS search and ZOOMA emit **candidates**. Validate each selected ID with OLS term detail,
then check its definition against the sample and the target schema before accepting it.
Bioregistry, Identifiers.org, ZOOMA, and Ontobee answer prefix, landing-page, and shorthand
questions — they do not replace that OLS check.

## Which service

| Question | Script | Authority |
| --- | --- | --- |
| What is the term for "left ventricle"? | `scripts/resolve_terms.py` | OLS |
| OLS missed lab shorthand (`PBMC`, `WT`) | `scripts/map_terms.py`, then `validate_terms.py` | ZOOMA proposes; OLS validates the term |
| Is `EFO:0001067` real, current, correctly labelled? | `scripts/validate_terms.py` | OLS |
| Is `HPO` a real prefix? Does `HP:notanid` match the pattern? | `scripts/lookup_prefix.py` | Bioregistry |
| Which landing page should this CURIE open? | `scripts/lookup_prefix.py` | Identifiers.org + Ontobee URLs |

All four scripts take single values or files, emit TSV or JSON, and need no packages beyond the
standard library. Full traps for the non-OLS services are in `references/companion-apis.md`.

## Resolve text to terms

```bash
cd skills/ontology-term-resolution/scripts

# one string, constrained to the ontology that should define it
python3 resolve_terms.py "liver" --ontology uberon
```

```
query   rank  curie           iri                                               label  ontology  match_type   strategy  defining_ontology
liver   1     UBERON:0002107  http://purl.obolibrary.org/obo/UBERON_0002107       liver  uberon    exact_label  exact     true
```

```bash
# a column of tissue names; anything not an exact hit is reported, not guessed
python3 resolve_terms.py --input tissues.txt --ontology uberon \
    --exact-only --format tsv -o resolved.tsv

# accept fuzzy fallbacks, then review the partial hits by hand
python3 resolve_terms.py "left ventrical of heart" --ontology uberon --top 3
```

The search escalates `exact` (label and synonym) → `token` → `fulltext` and stops at the first
strategy that returns candidates, reporting which one fired. `--exact-only` disables the ladder
and locally rejects partial, related, broad, narrow, and unscoped synonym matches. Searches
are bounded candidate lists (`--top`), not exhaustive ambiguity checks.
`--branch UBERON:0000465` uses OLS hierarchical ancestry, including part-of/develops-from.

**Read `match_type` before using a result.** `exact_label` and `exact_synonym` establish lexical
agreement (the latter also requires an exact synonym annotation), not correct sample context.
`related_synonym`, `broad_synonym`, `narrow_synonym`, `unspecified_synonym`, and `partial` require
curation. Validate every selected ID; search does not expose obsolescence in its records.
`unresolved` is a legitimate output. See `references/curation-rules.md` before normalising input.

## Validate existing IDs

```bash
python3 validate_terms.py UBERON:0002107 EFO:0001067 UBERON:9999999
```

```
id              status     actual_label                  ontology  replacement     detail
UBERON:0002107  ok         liver                         uberon
EFO:0001067     obsolete   obsolete_parasitic infection  efo       MONDO:0005135   obsolete; replaced by MONDO:0005135
UBERON:9999999  not_found                                                          no such term in the ontology this prefix names
```

Exit code is 1 if anything failed, 0 otherwise, 2 on usage or network trouble — so it works as a
CI gate on a metadata file:

```bash
# id + label columns; catches IDs that exist but are labelled as something else
python3 validate_terms.py --input metadata.tsv --strict

# a tissue column must hold UBERON anatomical entities and nothing else
python3 validate_terms.py --input tissue_ids.tsv \
    --branch UBERON:0000465 --expect-ontology uberon
```

| Status | Meaning | Verdict |
| --- | --- | --- |
| `ok` | Exists, current, consistent with everything asserted | pass |
| `matched_synonym` | Claimed label is a synonym; primary label differs | warn |
| `imported_only` | No defining copy was verified in OLS | warn |
| `not_a_class` | Term is a property or individual | warn |
| `not_found` | No such term | fail |
| `obsolete` | Obsoleted; `replacement` gives the successor when one exists | fail |
| `label_mismatch` | Claimed label matches neither primary label nor recorded synonyms | fail |
| `wrong_ontology` | Right kind of ID, wrong ontology for this column | fail |
| `wrong_branch` | Not a descendant of the required root | fail |
| `malformed_curie` | Not of the form `PREFIX:local` | fail |

`--strict` promotes warnings to failures. `--expect-ontology` checks the identifier namespace,
so a CL term imported into UBERON cannot pass a UBERON-only column. OLS ontology ids and
Bioregistry preferred prefixes are not interchangeable (ORPHA/Orphanet uses OLS `ordo`).
Use `--branch-relation is-a` for subclass-only validation; the default `hierarchical` also
includes part-of/develops-from. A missing/obsolete branch root is a usage error, not a negative
scientific result. `not_found` means absent from this OLS lookup, not proof of global nonexistence.

## Check a prefix or compact identifier

```bash
python3 lookup_prefix.py HP HPO HP:0001250 HPO:0001250
```

```
query        status          preferred_prefix  canonical_curie  pattern    detail
HP           ok              HP                                 ^\d{7}$
HPO          synonym_prefix  HP                                 ^\d{7}$    'HPO' is a synonym of preferred prefix HP
HP:0001250   ok              HP                HP:0001250       ^\d{7}$
HPO:0001250  synonym_prefix  HP                HP:0001250       ^\d{7}$    'HPO' is a synonym of preferred prefix HP
```

Bioregistry accepts synonym p

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

