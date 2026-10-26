---
id: sciref-pkpd-modeling-ddi-and-qt
name: "Scientific Ref: DDI screening and concentration-QTc"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pkpd-modeling): DDI screening and concentration-QTc"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pkpd modeling ddi"
  - "ddi screening and concentration-qtc"
keywords:
  - "pkpd"
  - "modeling"
  - "ddi"
  - "specialized"
  - "scientific"
  - "reference"
  - "screening"
---

# DDI screening and concentration-QTc

## ICH M12 basic models

Use the current [M12 guideline](https://www.pmda.go.jp/files/000268574.pdf), with measured inputs,
units and assay binding basis recorded. A positive screen calls for further evaluation; it is not a
predicted clinical effect size. A negative screen does not exclude unmodeled mechanisms.

| Mechanism | Quantity | Screening trigger |
| --- | --- | --- |
| Reversible CYP | `1+Cmax,u/Ki,u` | >=1.02 |
| Oral gut CYP | `1+(dose/0.25L)/Ki,u` | >=11 |
| Time-dependent inhibition | `1+(kinact*I/(KI,u+I))/kdeg`, I=5*Cmax,u | >=1.25 |
| Kinetic induction | `1/(1+Emax*I/(EC50,u+I))`, I=10*Cmax,u | <=0.8 |
| OAT1/3, OCT2 | `Cmax,u/IC50,u` | >=0.1 |
| MATE1/2-K; systemic P-gp/BCRP | `Cmax,u/IC50,u` | >=0.02 |
| Intestinal P-gp/BCRP, oral | `(dose/0.25L)/IC50` | >=10 |
| OATP1B1/1B3 | `Iin,max,u/IC50,u` | >=0.1 |

Induction also requires interpretation of the experimental mRNA concentration-response evidence;
the kinetic formula alone is not a complete induction assessment. For measured plasma fu<0.01,
use 0.01 unless reliability at the low fraction has been demonstrated.

## Mechanistic static model and units

The CLI's ka is per minute and Qh=97 L/hour, so multiply ka by 60 before combining them.
`Ih=fu*(Cmax+Fa*Fg*ka_hour*dose/(Qh*RB))`; `Ig=Fa*ka_hour*dose/Qen`, Qen=18 L/hour.
These inlet/enterocyte values differ from basic luminal `dose/0.25L`.
Dose must use the same amount unit as concentration times liters (micromolar -> micromoles).
The model separates hepatic/gut reversible inhibition, inactivation and induction:

```
AUCR = 1/(Ag*Bg*Cg*(1-Fg)+Fg) / (Ah*Bh*Ch*fm + 1-fm)
```

Its full-inhibition ceiling is `1/((1-fm)*Fg)`, while `1/(1-fm)` is hepatic only. Run inhibition
alone, induction alone and combined so cancellation cannot hide a signal. This implementation
uses shared illustrative kinetic inputs and fixed adult flows; it does not implement every M12
case, metabolite contribution, transporter-enzyme coupling or time-dependent dosing profile.
Escalate to qualified PBPK/clinical evaluation when the question needs those features.

## QT concentration-response

The CLI regresses supplied placebo-corrected change from baseline QTc on concentration and reports
a two-sided 90% CI at a specified exposure. Verify correction, units, timing, delayed effects,
linearity, range coverage and influence. It assumes independent observations and is not the mixed
model normally needed for repeated trial data. A nonzero intercept needs explanation, but is not
an automatic model rejection rule.

The relevant E14 exclusion threshold is an upper confidence bound **below 10 ms**, in a study with
adequate exposure/design and model assessment. A result meeting that threshold is not proof of no
arrhythmia risk. Integrated nonclinical evidence has additional best-practice requirements.
[E14/S7B Q&A](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/e14-and-s7b-clinical-and-nonclinical-evaluation-qtqtc-interval-prolongation-and-proarrhythmic).

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

