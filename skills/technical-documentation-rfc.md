---
id: technical-documentation-rfc
name: Technical Documentation, Architecture Spec, RFC & ADR
category: engineering
description: Redige documentação técnica de engenharia, especificações de arquitetura, RFCs (Request for Comments), ADRs (Architecture Decision Records) e manuais operacionais baseados nas evidências do Vault.
task_types:
  - ask
  - draft
recommended_max_tokens: 4096
triggers:
  - documentacao tecnica
  - documentação técnica
  - technical documentation
  - rfc
  - adr
  - architecture decision record
  - especificacao tecnica
  - especificação técnica
  - documento de arquitetura
  - manual tecnico
  - manual técnico
  - design doc
keywords:
  - documentacao
  - documentação
  - rfc
  - adr
  - especificacao
  - especificação
  - arquitetura
  - runbook
---

# Skill: Technical Documentation, Architecture Spec, RFC & ADR

## 1. Diretrizes de Engenharia Baseadas em Evidências
1. Extraia componentes, contratos, fluxos de dados, invariantes, configurações e decisões técnicas diretamente das notas e entidades do grafo (`[Título](bbref:<evidenceId>)`).
2. Nunca invente endpoints, parâmetros ou comportamentos não sustentados pelas evidências fornecidas.

## 2. Estrutura Obrigatória

### `# [Título da Especificação / Documentação Técnica]`
### `## 1. Visão Geral e Contexto Técnico (Overview & Context)`
### `## 2. Arquitetura, Componentes e Fluxo de Dados`
- Inclua descrição clara dos módulos/entidades e relação entre eles conforme o grafo.
### `## 3. Decisões de Projeto, Invariantes e Contratos (Design Decisions & Contracts)`
### `## 4. Operação, Segurança, Confiabilidade e Trade-offs`
### `## 5. Limitações Conhecidas e Questões em Aberto`
### `## Fontes Técnicas Citadas`
