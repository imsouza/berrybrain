---
id: sciref-clinical-decision-support-security-validation
name: "Scientific Ref: Security Validation Record"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (clinical-decision-support): Security Validation Record"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "clinical decision support security validation"
  - "clinico decision support seguranca validation"
  - "security validation record"
keywords:
  - "clinical"
  - "decision"
  - "support"
  - "security"
  - "validation"
  - "clinico"
  - "seguranca"
  - "specialized"
  - "scientific"
  - "reference"
---

# Security Validation Record

Validation date: **2026-07-23** (local project date).

## Baseline

The repository `SECURITY.md` section recorded 11 findings:

- 3 CRITICAL findings for cross-file environment-variable/network exfiltration behavior;
- 1 HIGH finding for transmitting a credential to an external service;
- 5 MEDIUM findings for command chaining, credential flow, undeclared network use, and environment harvesting;
- 2 LOW findings for mandatory cross-skill invocation and dependency concerns.

The affected external schematic wrappers were the now-deleted files
`generate_schematic.py` and `generate_schematic_ai.py`.

## Remediation

- Deleted both schematic-generation scripts.
- Removed all external service, LLM, image, credential, and environment-variable behavior.
- Removed mandatory figures and cross-skill calls.
- Replaced unsafe person-level classification and care-pathway helpers with aggregate or planning-only tools.
- Added bounded local JSON handling, person-level-key rejection, output limits, and deterministic schemas.
- Added static AST tests that reject network libraries, dynamic code execution, credential access, and executable serialization.

## Historical July 2026 Scan Results

- Direct behavioral scan: **SAFE, 0 findings**.
- Pull-request gate with `--fail-on HIGH`: **passed** with 0 CRITICAL and
  0 HIGH. Repeated LLM-assisted runs returned 2–3 LOW findings because the
  analyzer is nondeterministic.

## Accepted LOW Findings

Across repeated runs, the nondeterministic analyzer reported different subsets of
these LOW observations:

1. **Optional `allowed-tools` field absent** — accepted as informational. The
   Agent Skills specification does not require it; compatibility and runtime
   instructions explicitly prohibit network and credential access.
2. **Broad description** — accepted. The scope intentionally covers the related research-evaluation artifacts requested for this safety refresh, while the frontmatter and first body section explicitly exclude care and live operation.
3. **Person-level key filtering uses a denylist** — accepted as a documented limitation, not a privacy guarantee. Input is contractually restricted to synthetic or aggregate schemas, common person-level fields are rejected as defense in depth, and the documentation repeatedly requires qualified privacy review. The filter cannot detect every identifier name or sensitive value and is never presented as de-identification.
4. **Occasional missing-file report** — accepted as an analyzer false
   positive. Some runs invented a `templates/` directory and nonexistent
   `assets/*.md` references. The deterministic
   `test_documented_local_paths_exist` check resolves every documented local
   path and passes.

None of the accepted findings permits network access, sensitive-data handling, or clinical action.

## September 2026 Maintenance

The 2.4 refresh keeps all runtime helpers offline. Invalid aggregate/matrix inputs now withhold results or exports; denominator checks run before suppression; undefined balanced accuracy stays null; CSV text is escaped and dangling output symlinks are rejected. Synthetic regression tests cover these cases and the updated GRADE imprecision label. The July scanner results above are historical, not a claim about a new scan of version 2.4.

## Reproduction

```bash
uv run skill-scanner scan skills/clinical-decision-support --use-behavioral

uv run python scan_pr_skills.py \
  --fail-on HIGH \
  --output /tmp/clinical-decision-support-pr-scan.md \
  skills/clinical-decision-support
```

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

