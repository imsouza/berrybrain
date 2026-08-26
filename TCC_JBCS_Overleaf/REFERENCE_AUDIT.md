# Reference Authenticity Audit

## Status

Audit date: 25 August 2026.

All 45 BibTeX entries cited by `main.tex` passed bibliographic-existence checks. The audit found
28 DOI-bearing references and 17 references identified by stable official URLs. No citation key is
missing, duplicated, or unused in the manuscript.

## Method

1. Parse every BibTeX entry and every citation key used by `main.tex`.
2. Decode LaTeX escapes in DOI strings before lookup.
3. Query Crossref first and DataCite when Crossref has no record.
4. Require DOI metadata to agree with the cited title, publication year, and first-author surname.
   A one-year tolerance is allowed only for edition or online-record differences when title and
   author agree.
5. Request every non-DOI URL and require a successful response from the standards body, publisher,
   software project, or stable bibliographic host.
6. Treat existence as distinct from claim support. Claim-to-artifact traceability remains covered
   by `EVIDENCE_AUDIT.md` and the manuscript's limitations.

## Results

| Authority | Count | Citation keys |
| --- | ---: | --- |
| Crossref structured metadata | 22 | `audibert2009exploration`, `balog2019pkg`, `brier1950`, `brooke1996sus`, `chakraborty2023survey`, `cormack2009rrf`, `efron1993bootstrap`, `es2024ragas`, `fraga2023automatic`, `fraga2024connections`, `gutierrez2024hipporag`, `hart1988nasatlx`, `hevner2004design`, `karpukhin2020dpr`, `kim2024prometheus`, `liu2023geval`, `peffers2007dsrm`, `saadfalcon2024ares`, `shi2025judges`, `skjaeveland2024ecosystem`, `trivedi2022musique`, `yang2018hotpotqa` |
| DataCite structured metadata | 6 | `edge2024graphrag`, `guo2017calibration`, `guo2024lightrag`, `gutierrez2025hipporag2`, `lewis2020rag`, `thakur2021beir` |
| W3C Recommendations | 5 | `rdf11`, `owl2`, `skos`, `prov`, `wcag22` |
| Official software documentation | 11 | `docker`, `fastapi`, `nextjs`, `playwright`, `pydantic`, `pytest`, `python`, `react`, `ruff`, `sqlalchemy`, `uv` |
| Stable JSTOR record | 1 | `holm1979procedure` |

## Findings and Boundaries

- All 28 DOI strings resolved to matching structured metadata: 22 through Crossref and six through
  DataCite.
- All 17 non-DOI URLs returned successful responses from their retained official or stable hosts.
- The Efron and Tibshirani book is commonly cited as the 1993 original publication, while the
  Crossref DOI record reports 1994. The cited title and authors match; the manuscript retains 1993
  and records the registry-year difference here instead of silently rewriting the source.
- `holm1979procedure` has no confirmed DOI in the retained record. Its JSTOR stable identifier is
  therefore used rather than an invented DOI.
- Software documentation uses an access-year style because the cited pages are living technical
  documentation. Version evidence used in the experiment is reported separately in Table 2.
- A successful authenticity check does not establish that a source proves every nearby claim.
  Claims remain bounded by the wording, evidence tables, and threats-to-validity section.
