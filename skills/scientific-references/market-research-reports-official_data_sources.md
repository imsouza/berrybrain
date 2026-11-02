---
id: sciref-market-research-reports-official-data-sources
name: "Scientific Ref: Official Data and Filing Sources"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (market-research-reports): Official Data and Filing Sources"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "market research reports official sources"
  - "market pesquisa reports official sources"
  - "official data and filing sources"
keywords:
  - "market"
  - "research"
  - "reports"
  - "official"
  - "sources"
  - "pesquisa"
  - "specialized"
  - "scientific"
  - "reference"
---

# Official Data and Filing Sources

Reviewed against first-party guidance on 2026-10-01. API rules can change:
recheck the linked terms and limits before automated or high-volume use. The
bundled scripts do not call these services and do not require API keys.
This is a routing and metadata guide, not an executed API client: documentation
review does not establish authenticated retrieval or current service availability.

## Routing by claim

Start with the original authority most fit for the claim:

- company financials and risk disclosures: the jurisdiction's official filing
  system, then the filed document;
- establishment, employment, prices, production, trade, population, and GDP:
  the responsible national statistical office or central bank;
- rules, approvals, enforcement, licenses, and consultations: the responsible
  regulator or official legal gazette;
- cross-country indicators: the original national source when comparability is
  not required; otherwise an international harmonized dataset with metadata;
- classifications: the current official NAICS, NACE, ISIC, product, trade, or
  sector taxonomy and its correspondence tables.

Do not treat an aggregator as an independent corroborating source when it
reproduces the same underlying series.

## United States

### SEC EDGAR and company filings

- [SEC Developer Resources](https://www.sec.gov/about/developer-resources)
  documents company submissions and extracted XBRL data APIs.
- [Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)
  requires a declared user agent and states a current maximum of 10 requests per
  second across the user's machines. Download only what is needed.
- EDGAR filings can be corrected or removed after acceptance. Record accession
  number, form, filing date, reporting period, amendment status, exact table or
  XBRL fact, units, and retrieval date.
- Consolidated company revenue is not automatically market revenue. Remove
  out-of-scope products/geographies and avoid summing parent/subsidiary or
  channel/end-customer values twice.

### U.S. Census Bureau

- The [Census Data API User Guide](https://www.census.gov/data/developers/guidance/api-user-guide.html)
  links data to a geographic boundary and a dataset vintage.
- As revised 2026-05-14, the
  [query-limits page](https://www.census.gov/data/developers/guidance/api-user-guide.Query_Limits.html)
  permits up to 50 variables per query and requires a key for all data queries.
  The [key page](https://www.census.gov/data/developers/guidance/api-user-guide.API_Key.html)
  describes free registration. The key travels in the query URL; redact `key`
  before storing source URLs, logs, or request provenance. Never place a key in a
  report, source ledger, or bundled script.
- Use program-specific methodology, margins of error, universe, geography, and
  vintage. ACS estimates, Population Estimates, and decennial counts are not
  interchangeable.
- The [2022 Economic Census methodology](https://www.census.gov/programs-surveys/economic-census/year/2022/technical-documentation/methodology.html)
  defines the target population, sampling frame, exclusions, administrative
  data, imputation, disclosure avoidance, and product collection.
- The [NAICS site](https://www.census.gov/naics) identifies 2022 NAICS as the
  current published structure while a 2027 revision process is underway. Store
  the version used.

### Bureau of Labor Statistics

The [BLS API FAQ](https://www.bls.gov/developers/api_faqs.htm), last modified
2023-08-30, documents:

- registered v2: 500 queries/day, 50 series/query, 20 years/query;
- unregistered v1: 25 queries/day, 25 series/query, 10 years/query;
- both: 50 requests per 10 seconds;
- v2 registration renewal at least annually;
- v1 returns observations and footnotes without descriptive metadata.

Record series ID, survey/program, seasonal adjustment, units, frequency,
footnotes, publication date, and revision status. Consult the program's
methodology and release calendar rather than relying on the API response alone.
Inspect `message` and each series' observations even when the response says
`REQUEST_SUCCEEDED`: the FAQ shows invalid-series messages with that status.

### Bureau of Economic Analysis

The [BEA API User Guide](https://apps.bea.gov/api/_pdf/bea_web_service_api_user_guide.pdf),
dated 2026-04-20, requires a registered UserID and documents three rolling
per-minute limits:

- 100 requests;
- 100 MB retrieved;
- 30 errors.

BEA returns HTTP 429 and a `Retry-After` header when throttled. The guide warns
that limits may change. Query metadata methods before data, restrict years and
dimensions, and avoid broad `ALL` requests. Record current versus chained
dollars, reference year, table/line code, frequency, seasonality, and release
vintage. Chained-dollar components may not be additive; use published
contributions or current-dollar shares where appropriate.
Check `BEAAPI.Results.Error` as well as HTTP status; request parameters may be
echoed in the response, so redact `UserID` before archiving it.

### Federal Reserve and FRED/ALFRED

- [FRED API documentation](https://fred.stlouisfed.org/docs/api/fred/) describes
  v2 bulk release history and v1 series-level FRED/ALFRED access.
- A registered key is required under the
  [FRED API Terms](https://fred.stlouisfed.org/docs/api/terms_of_use.html).
  The reviewed terms do not state one fixed numerical request ceiling; they
  reserve the right to impose or change limits.
- The terms warn that third parties may own series and impose additional
  restrictions. Follow the original producer's rights and attribution.
- FRED normally presents latest values; ALFRED preserves real-time vintages.
  Record source, release, series ID, frequency, units, seasonal adjustment,
  notes, and vintage dates.

## International and harmonized sources

### World Bank

The [Indicators API documentation](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation)
states that v2 is current, v1 is discontinued, and API authentication is not
required. Preserve indicator code, database/source, source note, source
organization, unit, income/region classification vintage, and retrieval date.
The [WDI catalog](https://datacatalog.worldbank.org/search/dataset/0037712/world-development-indicators)
publishes metadata and revision-history resources. A World Bank indicator may
originate with a national agency or anothe

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

