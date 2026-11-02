---
id: sciref-pacsomatic-agent-playbook
name: "Scientific Ref: Operator playbook"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pacsomatic): Operator playbook"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pacsomatic agent playbook"
  - "operator playbook"
keywords:
  - "pacsomatic"
  - "agent"
  - "playbook"
  - "specialized"
  - "scientific"
  - "reference"
  - "operator"
---

# Operator playbook

1. Establish one true matched PacBio HiFi tumor/normal pair from acquisition
   metadata. Require patient and sample IDs; do not invent clinical identifiers.
2. Select a reference with exact assembly, contig naming and resource provenance.
   FASTA alone does not supply VEP, SV annotation, clonality or signature resources.
3. Prepare artifacts with the helper's `--dry-run` and `--use-current-path`.
   Report each warning and separate file/name checks from unperformed BAM,
   schema, network, container and scheduler checks.
4. Review `samplesheet.csv`: tumor status 1, normal status 0, same patient,
   distinct samples/files. Confirm that optional `.pbi` indexes correspond to
   their BAM. Confirm that MM/ML modification tags survived input processing
   before expecting methylation results.
5. Review commit pin, params, profiles and generated shell script. Read local
   infrastructure configuration before launch. `--executor slurm` by itself
   does not set the task executor to Slurm. Default `config.yaml` is descriptive
   and is not loaded by Python.
6. Execute only when requested. A new run uses `--run`; reusing generated
   artifacts needs `--overwrite`. If using a local checkout, record git HEAD and
   any uncommitted diff separately and omit `--pipeline-version`.
7. Return the exact artifact/script paths, run type and checked scope, requested
   pipeline revision, submission job ID if parsed, and one next QC/triage action.
   Do not label a queued job complete or helper dry-run as pipeline validation.
8. On failure, preserve the driver log, `.nextflow.log`, work task logs, params
   and samplesheet. Do not delete work/cache before deciding whether to resume.
   Keep secrets and identifiable sequencing metadata out of shared logs/reports.

All example commands in [the main skill](../SKILL.md) use repository-root paths.
When the skill is installed elsewhere, resolve `scripts/run_pacsomatic.py`
relative to its skill directory; `.github/skills/pacsomatic` is not this
repository's layout.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

