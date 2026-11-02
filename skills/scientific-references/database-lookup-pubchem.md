---
id: sciref-database-lookup-pubchem
name: "Scientific Ref: PubChem PUG REST API"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): PubChem PUG REST API"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup pubchem"
  - "pubchem pug rest api"
keywords:
  - "database"
  - "lookup"
  - "pubchem"
  - "specialized"
  - "scientific"
  - "reference"
---

# PubChem PUG REST API

## Base URL

```
https://pubchem.ncbi.nlm.nih.gov/rest/pug
```

## URL Pattern

```
/{domain}/{namespace}/{identifiers}/{operation}/{output}
```

- **domain**: `compound`, `substance`, `assay`
- **namespace**: `cid`, `name`, `smiles`, `inchi`, `inchikey`, `fastformula`
- **operation**: `record`, `property`, `synonyms`, `description`, `cids`, `xrefs`
- **output**: `JSON`, `XML`, `CSV`, `TXT`, `SDF`, `PNG`

## Key Endpoints

### Search by name
```
GET /compound/name/{name}/JSON
```
Example: `/compound/name/aspirin/JSON`

### Search by CID
```
GET /compound/cid/{cid}/JSON
```
Example: `/compound/cid/2244/JSON`

Multiple CIDs: `/compound/cid/2244,5988,3672/JSON`

### Search by SMILES
```
GET /compound/smiles/{smiles}/JSON
```
For SMILES with special characters, use POST:
```
POST /compound/smiles/JSON
Content-Type: application/x-www-form-urlencoded
smiles=CC(=O)OC1=CC=CC=C1C(=O)O
```

### Search by InChIKey
```
GET /compound/inchikey/{inchikey}/JSON
```

### Search by InChI (POST only — InChI strings are too long for URLs)
```
POST /compound/inchi/JSON
Content-Type: application/x-www-form-urlencoded
inchi=InChI=1S/C9H8O4/...
```

### Search by molecular formula
```
GET /compound/fastformula/{formula}/JSON
```
Example: `/compound/fastformula/C9H8O4/JSON`

### Property retrieval
```
GET /compound/{namespace}/{id}/property/{property_list}/JSON
```
Properties are comma-separated. Available properties:

`MolecularFormula`, `MolecularWeight`, `ConnectivitySMILES`, `SMILES`, `InChI`, `InChIKey`, `IUPACName`, `XLogP`, `ExactMass`, `MonoisotopicMass`, `TPSA`, `Complexity`, `Charge`, `HBondDonorCount`, `HBondAcceptorCount`, `RotatableBondCount`, `HeavyAtomCount`, `CID`

Example:
```
/compound/cid/2244/property/MolecularFormula,MolecularWeight,ConnectivitySMILES,IUPACName/JSON
```

Response:
```json
{
  "PropertyTable": {
    "Properties": [
      {
        "CID": 2244,
        "MolecularFormula": "C9H8O4",
        "MolecularWeight": "180.16",
        "IUPACName": "2-acetyloxybenzoic acid",
        "ConnectivitySMILES": "CC(=O)OC1=CC=CC=C1C(O)=O"
      }
    ]
  }
}
```

### Synonym lookup
```
GET /compound/{namespace}/{id}/synonyms/JSON
```

### Compound description
```
GET /compound/cid/{cid}/description/JSON
```

### Get just CIDs from a name
```
GET /compound/name/{name}/cids/JSON
```

### Cross-references (patents, registry IDs)
```
GET /compound/cid/{cid}/xrefs/PatentID/JSON
GET /compound/cid/{cid}/xrefs/RegistryID/JSON
```

### Fast similarity search (synchronous CID result)
```
POST /compound/fastsimilarity_2d/smiles/cids/JSON
smiles=CC(=O)OC1=CC=CC=C1C(=O)O&Threshold=90
```

### 2D structure image
```
GET /compound/cid/{cid}/PNG
GET /compound/cid/{cid}/PNG?image_size=300x300
```

## Rate Limits

- Max **5 requests per second**
- Max **400 requests per minute**
- Batch CIDs with commas; use POST when the URL becomes long and keep batches small enough to meet time/payload limits. Endpoint-specific limits differ.
- Throttle error returns `PUGREST.ServerBusy` fault code

## Error Format

```json
{
  "Fault": {
    "Code": "PUGREST.NotFound",
    "Message": "No CID found",
    "Details": ["..."]
  }
}
```

`fastsimilarity_2d` returns `IdentifierList.CID` synchronously; do not look for an
asynchronous ListKey in a successful fast-search response. Older SMILES property
aliases may still be accepted but returned JSON keys use the current names above.
Official contract: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

