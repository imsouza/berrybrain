---
id: sciref-pufferlib-integration
name: "Scientific Ref: Integration, Security, and Migration Guide"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pufferlib): Integration, Security, and Migration Guide"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pufferlib integration"
  - "integration, security, and migration guide"
keywords:
  - "pufferlib"
  - "integration"
  - "specialized"
  - "scientific"
  - "reference"
  - "security"
---

# Integration, Security, and Migration Guide

Review: **2026-10-01**. Native 5.0 guidance is in [native-5.md](native-5.md);
3.0 and the pinned 4.0 snapshot below are historical profiles.

## Compatibility matrix

| Need | Published `pufferlib==3.0.0` | Historical `4.0` source |
|---|---|---|
| Gymnasium instance adaptation | `pufferlib.emulation.GymnasiumPufferEnv` | Removed from reviewed 4.0 source |
| PettingZoo Parallel adaptation | `pufferlib.emulation.PettingZooPufferEnv` | Removed from reviewed 4.0 source |
| Python vector backends | `pufferlib.vector` | Removed from reviewed 4.0 source |
| Native Python `PufferEnv` | Supported | Replaced by historical C/Ocean interface |
| Trainer | `pufferlib.pufferl.PuffeRL` | Native backend or `pufferlib.torch_pufferl.PuffeRL` |
| External logging | W&B; Neptune historical/shut down | W&B in historical CLI |
| Primary config | merged INI sections | different INI schema |
| Checkpoints | Torch state dict plus trainer state | native `.bin`; Torch fallback state dict |

Pin a profile. Do not import from a floating branch or blend examples across
columns.

## Correct stable adaptation patterns

### Gymnasium

```python
import gymnasium
import pufferlib.emulation
import pufferlib.vector


def make_env(buf=None, seed=0):
    raw = gymnasium.make("CartPole-v1")
    return pufferlib.emulation.GymnasiumPufferEnv(raw, buf=buf, seed=seed)


vecenv = pufferlib.vector.make(
    make_env,
    backend=pufferlib.vector.Serial,
    num_envs=2,
    seed=42,
)
try:
    observations, infos = vecenv.reset(seed=42)
    vecenv.action_space.seed(43)
    actions = vecenv.action_space.sample()
    observations, rewards, terminals, truncations, infos = vecenv.step(actions)
finally:
    vecenv.close()
```

This source-reviewed pattern is illustrative, not a native PufferLib runtime
test. The vectorizer injects `buf` and `seed` into creators; a zero-argument
factory fails. Use Gymnasium 0.29.1/NumPy <2 with the published package, not
the current Gymnasium 1.3 vector API.

### PettingZoo

Use a reviewed Parallel environment instance:

```python
wrapped = pufferlib.emulation.PettingZooPufferEnv(reviewed_parallel_env)
```

The stable source does not document automatic AEC-to-Parallel conversion in
this adapter. Convert explicitly with PettingZoo's supported utilities only
when the environment's turn semantics permit it, then test action ordering,
dead-agent handling, masks, and termination/truncation dictionaries.

### Native stable environment

Subclass `pufferlib.PufferEnv`, define `single_observation_space`,
`single_action_space`, and `num_agents` before `super().__init__`, then update
the provided arrays in place. Native Puffer environments are already vector
interfaces; do not return Gym's scalar four-tuple.

## Unsupported shortcuts from the old skill

Remove or migrate these historical patterns:

| Historical pattern | Current guidance |
|---|---|
| `pufferlib.make("name", ...)` | Stable: import an audited creator and use `pufferlib.vector.make`; 4.0: build/configure a named native environment |
| `pufferlib.emulate(...)` | Stable: instantiate `GymnasiumPufferEnv` or `PettingZooPufferEnv` explicitly |
| `pufferlib.vectorization.Serial` | Stable module is `pufferlib.vector.Serial` |
| `from pufferlib import PuffeRL` | Stable trainer is `pufferlib.pufferl.PuffeRL`; 4.0 fallback is in `torch_pufferl` |
| define native `observation_space`/`action_space` | Stable native class requires `single_observation_space`/`single_action_space` before `super()` |
| return `(obs, reward, done, info)` | Return separate termination and truncation values |
| native multi-agent dictionaries and `dones["__all__"]` | Use stable vector buffers or a reviewed PettingZoo Parallel adapter |
| arbitrary dotted `entry_point` registration | Import an audited callable directly; bundled tools reject dotted paths |
| top-level `WandbLogger`/`NeptuneLogger` | Stable logger classes live in `pufferlib.pufferl`; prefer the CLI and sanitized config |
| assume Atari/Procgen/NetHack names exist everywhere | Verify the chosen version's config/source and install the separately reviewed environment |

## Migrating 3.0 to 4.0

This is a redesign, not a drop-in upgrade:

1. Preserve the 3.0 lock, source digest, config, checkpoint hashes, and baseline
   evaluation before changing anything.
2. Inventory use of `emulation`, `vector`, `PufferEnv`, third-party environments,
   policy wrappers, INI keys, logger flags, and Torch checkpoints.
3. Decide whether the application should stay on published 3.0.0 or port to a
   historical 4.0 C environment. The pinned 4.0 package tree has no Python
   emulation/vector modules. For a new native port, use the separate 5.0 guide.
4. Port environment logic to the reviewed Squared/Target C binding contract.
5. Recreate configuration using 4.0 `[vec]`, `[policy]`, `[torch]`, and `[train]`
   keys. Do not mechanically rename old keys.
6. Rebuild policy composition around 4.0 encoder/decoder/network modules or the
   native backend.
7. Treat old `.pt` and new `.bin` files as incompatible unless an official,
   tested converter says otherwise. Do not improvise binary conversion.
8. Re-run contract, same-seed trace, throughput, and held-out learning
   baselines. Attribute behavior changes; do not compare headline SPS alone.

The historical 4.0 snapshot contains some stale 3.0-style examples even though the
corresponding modules are absent. Prefer current implementation and docs over
those copied examples.

## Third-party environments and native code

Environment extras can pull old Gym versions, native libraries, renderers,
emulators, datasets, model opponents, and ROM tooling. A package name in a
PufferLib optional extra is not a security or license endorsement.

Before install/import/build:

1. Identify the official repository and immutable revision.
2. Read build/install hooks and all network downloads.
3. Verify licenses for code and assets separately.
4. Verify hashes/attestations; record missing provenance.
5. Use a disposable sandbox without credentials, home-directory mounts, or
   network after required artifacts are staged.
6. Cap processes, threads, memory, disk, render resolution, agents, and steps.
7. Do not execute bundled native extensions, ROMs, checkpoints, or pickle files
   until separately trusted.

For Atari and similar systems, the user must supply legally obtained assets.
Never download ROM sets or auto-accept a license on the user's behalf.

## Logging 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

