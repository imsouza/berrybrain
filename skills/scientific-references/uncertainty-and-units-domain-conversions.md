---
id: sciref-uncertainty-and-units-domain-conversions
name: "Scientific Ref: Domain conversions and dimensional blind spots"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (uncertainty-and-units): Domain conversions and dimensional blind spots"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "uncertainty units domain conversions"
  - "domain conversions and dimensional blind spots"
keywords:
  - "uncertainty"
  - "units"
  - "domain"
  - "conversions"
  - "specialized"
  - "scientific"
  - "reference"
---

# Domain conversions and dimensional blind spots

Values below were produced with pint 0.26.1 and SciPy 1.18.1 (CODATA 2022). Anything
marked *exact* is fixed by definition and carries zero uncertainty.

## Dimensional analysis does not catch these

Two quantities with the same dimensions convert freely, whether or not the conversion
means anything.

| Pair | Shared dimension | What pint does | Why it matters |
| --- | --- | --- | --- |
| gray and sievert | L²T⁻² | converts 1:1, silently | equivalent/effective dose uses radiation/tissue weighting; a unit conversion cannot supply these factors |
| newton-metre and joule | ML²T⁻² | converts 1:1, silently | torque is a vector product, energy a scalar; adding them is meaningless |
| hertz and becquerel | T⁻¹ | converts 1:1, silently | one is periodic, the other stochastic |
| radian and dimensionless | none | radians vanish | `sin(x)` needs radians; a degrees value that lost its unit is silently wrong |
| mol/L and mol/kg | different | raises | molarity and molality are genuinely different quantities |
| mg/L and ppm | different | raises | equal only for dilute aqueous solutions near 1 g/mL |

The last two raise because they *are* dimensionally distinct. The first four are the
dangerous ones: no tool will warn you.

## Energy ladder

Molecular science quotes the same energy in at least six units, three of which are
per-mole and therefore need the Avogadro constant.

| From | To | Factor |
| --- | --- | --- |
| 1 eV | kJ/mol | 96.48533212331002 |
| 1 hartree | eV | 27.21138624598103 |
| 1 hartree | kcal/mol | 627.5094740628942 |
| 1 cm⁻¹ | eV | 1.2398419843320026e-4 |
| 1 cm⁻¹ | K (as E/k_B) | 1.4387768775039336 |
| k_B T at 298.15 K | eV | 0.02569257912108585 |
| k_B T at 298.15 K | kJ/mol | 2.478957029602389 |
| 1 cal (thermochemical) | J | 4.184 (exact) |
| 1 cal_it | J | 4.1868 (exact) |

Two traps. First, **per-mole and per-particle units are not dimensionally
interchangeable**: eV is an energy, kJ/mol is an energy per amount of substance, and the
conversion needs N_A. Pint will refuse `Q(1, "eV").to("kJ/mol")` and accept
`Q(1, "eV * N_A").to("kJ/mol")`. Second, **there are two calories** and a factor of
1.00067 between them; thermochemical is the default in chemistry, IT in engineering.

```python
Q(1, "eV * N_A").to("kJ/mol")            # 96.48533212331002 kilojoule / mole
Q(1, "1/cm").to("eV", "sp")              # 0.00012398419843320026 electron_volt
Q(298.15, "K").to("eV", "boltzmann")     # 0.02569257912108585 electron_volt
```

## Spectroscopy

Wavelength, frequency, wavenumber, and photon energy are related by physics, not by
dimensional analysis, and wavelength-frequency/energy relations are *reciprocal* — an uncertainty does not
convert by the same factor as the value.

```python
Q(532, "nm").to("THz", "sp")     # 563.5196578947367 terahertz
Q(532, "nm").to("1/cm", "sp")    # 18796.992481203004 / centimeter
Q(532, "nm").to("eV", "sp")      # 2.3305300457368467 electron_volt
```

Because E = hc/λ, a constant wavelength uncertainty becomes an energy uncertainty that
scales as 1/λ². Propagate through the relation, do not scale the uncertainty by the
value's conversion factor. `scripts/convert_units.py --uncertainty` does this with the
conversion's local derivative.

The `sp` context assumes vacuum unless given a refractive index. With `n=1.33`,
532 nm is interpreted as the wavelength **in that medium**, giving 423.7 THz.
A photon crossing an interface retains its frequency; its wavelength changes. Do not
apply n to a vacuum wavelength merely because the experiment contains water.

## Concentration

| Quantity | Unit | Depends on |
| --- | --- | --- |
| Molarity | mol/L | temperature, through solution volume |
| Molality | mol/kg solvent | composition and solvent basis, not thermal expansion alone |
| Mole fraction | dimensionless | composition and entity definition |
| Mass fraction, ppm(m/m) | dimensionless | composition and mass basis |
| Volume fraction, ppm(v/v) | dimensionless | temperature |
| Mass concentration | mg/L, g/L | temperature |

"ppm" alone is ambiguous: mass/mass, volume/volume, and mol/mol differ by the ratio of
densities or molar masses. In environmental water chemistry ppm conventionally means
mg/L, which equals mg/kg only because dilute water is close to 1 kg/L. In gas analysis
it conventionally means volume/volume. State which.

Pint treats `ppm` and `percent` as plain dimensionless scale factors (1e-6 and 0.01),
which is right for arithmetic and gives no protection against mixing the three senses.
Defining `ureg.define("ppm_v = 1e-6 = ppmv")` only adds an alias-like scale; it
provides **no** dimensional protection. To enforce semantic separation, use a custom
base dimension (for example `volume_fraction_kind = [volume_fraction_kind]`, then
`ppm_v = 1e-6 * volume_fraction_kind`) and explicit adapters to physical dimensionless
fractions. This is an application convention, not a new SI dimension.

Mass and amount of substance need the `chemistry` context and a molar mass:

```python
Q(1, "g").to("mol", "chemistry", mw=Q(180.156, "g/mol"))   # 0.005550744909966918 mole
```

## Pressure

| From | To Pa | Note |
| --- | --- | --- |
| 1 atm | 101325 | exact |
| 1 bar | 100000 | exact |
| 1 torr | 133.32236842105263 | atm/760, exact by definition |
| 1 psi | 6894.7572931683635 | |
| 1 mmHg | 133.322387415 | *not* identical to torr, differs by about 1.4e-7 relatively |

**Gauge and absolute pressure need an explicit reference pressure.** Pint can define
custom offset units, but a static offset cannot infer the actual ambient pressure. "psig" and "psia" have the same dimensions; a gauge reading needs the
ambient pressure added before it can be used in a gas law. Vacuum work, autoclave
protocols, and chromatography backpressures are where this bites.

## Radiation, magnetism, rotation

```python
Q(1, "Ci").to("Bq")               # 37000000000.0 becquerel   (exact by definition)
Q(1, "gauss").to("T", "Gaussian") # 9.999999999338245e-05 tesla
Q(1, "rpm").to("rad/s")           # 0.10471975511965977 radian / second
```

Gauss fails *without* the Gaussian context: CGS electromagnetic units have different
dimensions from SI ones, not merely different scales. Magnetic field strength H (A/m,
oersted) and magnetic flux density B (T, gauss) are distinct quantities that literature
routinely calls "the field".

## Mass spectrometry

The unified atomic mass unit and the dalton are the same thing:
1 Da = 1.66053906892e-27

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

