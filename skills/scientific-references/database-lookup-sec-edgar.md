---
id: sciref-database-lookup-sec-edgar
name: "Scientific Ref: SEC EDGAR API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): SEC EDGAR API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup sec edgar"
  - "sec edgar api reference"
keywords:
  - "database"
  - "lookup"
  - "sec"
  - "edgar"
  - "specialized"
  - "scientific"
  - "reference"
---

# SEC EDGAR API Reference

## Overview
SEC's Electronic Data Gathering, Analysis, and Retrieval system. Provides free access to corporate filings, company data, and XBRL financial data. No API key required, but a User-Agent header identifying you is mandatory.

## Base URLs
- **Company/Filings Data:** `https://data.sec.gov`
- **EDGAR Website/Archives:** `https://www.sec.gov`
- **XBRL API:** `https://data.sec.gov/api/xbrl`

## Authentication
- **API Key:** Not required.
- **User-Agent Header:** REQUIRED on every request. Must contain company/person name and email.
  ```
  User-Agent: MyCompany admin@mycompany.com
  ```
  Requests without a proper User-Agent are blocked (403).

## Rate Limits
- **10 requests per second** per source IP.
- Exceeding this results in temporary IP-based throttling (HTTP 429).
- Use the official bulk ZIP archives for large jobs instead of querying every company separately.

---

## Key Endpoints

### Full-text discovery

Use [EDGAR full-text search](https://www.sec.gov/edgar/search/) for interactive discovery. Its `efts.sec.gov` backend is not one of the documented `data.sec.gov` public APIs; do not treat inferred UI routes, filters, or response fields as a stable retrieval contract. Use the documented submissions and XBRL routes below for reproducible API retrieval.

### 3. Company Tickers & CIK Lookup

#### `GET https://www.sec.gov/cgi-bin/browse-edgar`
Legacy EDGAR company search.

**Parameters:**
| Parameter  | Type   | Required | Description |
|-----------|--------|----------|-------------|
| `company` | string | No       | Company name search. |
| `CIK`     | string | No       | CIK number or ticker symbol. |
| `type`    | string | No       | Filing type filter (e.g., `10-K`). |
| `dateb`   | string | No       | Filed before date `YYYY-MM-DD`. |
| `owner`   | string | No       | `include`, `exclude`, or `only`. |
| `count`   | int    | No       | Number of results (max 100). |
| `action`  | string | Yes      | `getcompany` for company search. |
| `output`  | string | No       | `atom` for XML/Atom feed. |

**Example:**
```
https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=AAPL&type=10-K&dateb=&owner=include&count=10&output=atom
```

#### `GET https://www.sec.gov/files/company_tickers.json`
Returns a JSON mapping of all company tickers to CIK numbers.

**Response:**
```json
{
  "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
  "1": {"cik_str": 789019, "ticker": "MSFT", "title": "MICROSOFT CORP"},
  ...
}
```

#### `GET https://www.sec.gov/files/company_tickers_exchange.json`
Includes exchange information for each ticker.

---

### 4. Company Filings & Submissions

#### `GET https://data.sec.gov/submissions/CIK{cik_padded}.json`
Returns company metadata and recent filings for a given CIK (zero-padded to 10 digits).

**Example:**
```
https://data.sec.gov/submissions/CIK0000320193.json
```

**Response:**
```json
{
  "cik": "320193",
  "entityType": "operating",
  "sic": "3571",
  "sicDescription": "Electronic Computers",
  "name": "Apple Inc.",
  "tickers": ["AAPL"],
  "exchanges": ["Nasdaq"],
  "filings": {
    "recent": {
      "accessionNumber": ["0000320193-24-000123", ...],
      "filingDate": ["2024-11-01", ...],
      "reportDate": ["2024-09-28", ...],
      "form": ["10-K", ...],
      "primaryDocument": ["aapl-20240928.htm", ...],
      "primaryDocDescription": ["10-K", ...]
    },
    "files": [
      {"name": "CIK0000320193-submissions-001.json", "filingCount": 1000}
    ]
  }
}
```

`filings.recent` contains at least one year or 1,000 filings, whichever is larger. Retrieve older filenames from `filings.files` under the same `/submissions/` base; keep the parallel arrays aligned by index.

---

### 5. Company Concept (XBRL Data)

#### `GET https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/{taxonomy}/{tag}.json`
Returns all values reported by a company for a specific XBRL tag across all filings.

**Path Parameters:**
| Parameter   | Description |
|------------|-------------|
| `cik`      | Zero-padded CIK (10 digits). |
| `taxonomy` | XBRL taxonomy: `us-gaap`, `ifrs-full`, `dei`, `srt`. |
| `tag`      | XBRL concept tag, e.g., `RevenueFromContractWithCustomerExcludingAssessedTax`, `Assets`, `AccountsPayableCurrent`. |

**Example:**
```
https://data.sec.gov/api/xbrl/companyconcept/CIK0000320193/us-gaap/RevenueFromContractWithCustomerExcludingAssessedTax.json
```

**Response:**
```json
{
  "cik": 320193,
  "taxonomy": "us-gaap",
  "tag": "RevenueFromContractWithCustomerExcludingAssessedTax",
  "label": "Revenue",
  "description": "Amount of revenue recognized...",
  "entityName": "Apple Inc.",
  "units": {
    "USD": [
      {
        "start": "2023-10-01",
        "end": "2024-09-28",
        "val": 391035000000,
        "accn": "0000320193-24-000123",
        "fy": 2024,
        "fp": "FY",
        "form": "10-K",
        "filed": "2024-11-01"
      }
    ]
  }
}
```

---

### 6. Company Facts (All XBRL for one company)

#### `GET https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json`
Returns aggregated company concepts from non-custom taxonomies applying to the entire entity. Custom tags and dimensional/segment facts require inspecting the filing itself.

**Example:**
```
https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json
```

**Response:** Same structure as companyconcept but with all tags nested under `facts.us-gaap`, `facts.dei`, etc.

```json
{
  "cik": 320193,
  "entityName": "Apple Inc.",
  "facts": {
    "dei": {
      "EntityCommonStockSharesOutstanding": { "units": { "shares": [...] } }
    },
    "us-gaap": {
      "RevenueFromContractWithCustomerExcludingAssessedTax": { "units": { "USD": [...] } },
      "Assets": { "units": { "USD": [...] } }
    }
  }
}
```

---

### 7. Frames (Cross-Company XBRL for a period)

#### `GET https://data.sec.gov/api/xbrl/frames/{taxonomy}/{tag}/{unit}/{period}.json`
Returns the last-filed fact per reporting entity that best matches the requested calendar period. Reporting start/end dates can differ between entities; inspect them before comparing values.

**Path Parameters:**
| Parameter   | Description |
|------------|-------------|
| `taxonomy` | `us-gaap`, `ifrs-full`, `dei`, `srt`. |
| `tag`      | XBRL tag, e.g., `Assets`. |
| `unit`     | `USD`, `shares`, `pure`, etc. |
| `period`   | Instant: `CY2023Q4I`; Duration: `CY2023`, `CY2023Q1`. |

**Period format:**
- `CY2023` = calendar year 2023 (full year duration)
- `CY2023Q1` = Q1 2023 duration


*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

