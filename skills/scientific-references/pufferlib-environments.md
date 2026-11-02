---
id: sciref-pufferlib-environments
name: "Scientific Ref: Environment Contracts and Native Environments"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pufferlib): Environment Contracts and Native Environments"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pufferlib environments"
  - "environment contracts and native environments"
keywords:
  - "pufferlib"
  - "environments"
  - "specialized"
  - "scientific"
  - "reference"
  - "environment"
  - "contracts"
---

# Environment Contracts and Native Environments

Review: **2026-10-01**. Native 5.0 guidance is in [native-5.md](native-5.md);
3.0 and the pinned 4.0 snapshot below are historical profiles.

## Start from the Gymnasium contract

A current single-agent Gymnasium environment defines `observation_space` and
`action_space`, then implements:

```python
def reset(self, *, seed=None, options=None):
    super().reset(seed=seed)
    return observation, info

def step(self, action):
    return observation, reward, terminated, truncated, info
```

Contract requirements:

- `observation` must be contained in `observation_space` after reset and every
  step, with the documented shape and dtype.
- `action` must be contained in `action_space`.
- `reward` is a finite scalar for ordinary single-agent tasks.
- `terminated` means the task's MDP reached a terminal state.
- `truncated` means an external limit ended the episode, commonly a time limit.
- `info` is a dictionary; never hide the only termination signal in it.
- Call `reset()` after either `terminated` or `truncated`.
- Seed the environment through `reset(seed=...)`. Seed the action space
  separately when sampled actions must be reproducible.
- Always call `close()`.

Both flags can be true in Gymnasium (for example a terminal at a time limit).
The synthetic helper deliberately makes its own flags mutually exclusive; that
is not a universal Gymnasium requirement.

Do not collapse `terminated` and `truncated` during learning. A time-limit
truncation can still permit value bootstrapping; a true terminal state does not.

Run the local contract tool before involving PufferLib:

```bash
python3 scripts/env_contract_validator.py
```

It validates only the bundled synthetic environment. It intentionally has no
module-path option, so it cannot dynamically import an untrusted package.

## Autoreset and final observations

Gymnasium 1.3's built-in vector APIs default to `NEXT_STEP`. A reset-only call
ignores that slot's action and must be excluded from learning transitions.
`SAME_STEP` returns the reset observation; the terminal observation is in
`infos["final_obs"]` with the `_final_obs` validity mask. `DISABLED` requires an
explicit boolean `reset_mask`. Record `metadata["autoreset_mode"]`, wrapper
compatibility and the resolved version. Bootstrap truncations from the final
pre-reset observation, not the next episode; terminals suppress bootstrapping.

PufferLib 3.0 pins Gymnasium `<=0.29.1`, and its own `Serial`/worker machinery
resets an already-done adapter on the next send. This is not Gymnasium 1.3's
VectorEnv contract. Do not inject a current Gymnasium vectorizer or assume its
`final_obs` key exists in PufferLib. Inspect returned arrays and exclude
reset-only transitions. Native PufferEnv implementations own their autoresets.
The bundled validator checks only the synthetic single-environment contract.

## Published PufferLib 3.0.0 native contract

For a native Python `PufferEnv`, assign these attributes **before** calling
`super().__init__(buf)`:

```python
import gymnasium
import numpy as np
import pufferlib


class ReviewedEnv(pufferlib.PufferEnv):
    def __init__(self, buf=None, seed=0):
        self.single_observation_space = gymnasium.spaces.Box(
            low=-1.0, high=1.0, shape=(4,), dtype=np.float32
        )
        self.single_action_space = gymnasium.spaces.Discrete(3)
        self.num_agents = 2
        super().__init__(buf)
```

The stable base accepts a Box observation space and Discrete, MultiDiscrete, or
Box action space. It allocates or attaches:

- `observations`
- `actions`
- `rewards`
- `terminals`
- `truncations`
- `masks`

Native methods operate on those buffers:

```python
def reset(self, seed=None):
    # update self.observations in place
    return self.observations, []

def step(self, actions):
    # update all buffers in place
    return (
        self.observations,
        self.rewards,
        self.terminals,
        self.truncations,
        [],
    )
```

The `infos` value for native Puffer environments is a list of dictionaries.
PufferLib's native interface expects vector rows for agents, even when there is
one agent. Native environments handle their own resets; clear rewards,
terminals, truncations, masks, and partially written observations explicitly.
Never leave a previous step's buffer values in place.

### Native shape checklist

For `A = num_agents` and single observation shape `S`:

- observations: `(A, *S)`
- rewards: `(A,)`
- terminals: `(A,)`
- truncations: `(A,)`
- masks: `(A,)`
- actions: joint shape derived from the single action space and `A`

Validate the exact allocated action shape rather than assuming `(A,)`, especially
for MultiDiscrete and Box actions.

## Stable Gymnasium and PettingZoo adaptation

PufferLib 3.0 uses explicit adapters:

```python
import pufferlib.emulation

wrapped = pufferlib.emulation.GymnasiumPufferEnv(reviewed_gymnasium_instance)
```

or:

```python
wrapped = pufferlib.emulation.PettingZooPufferEnv(reviewed_parallel_instance)
```

There is no supported 3.0 `pufferlib.emulate(...)` convenience function matching
the old skill examples. Pass either an `env` instance or an `env_creator`
callable according to the class signature; do not pass both.

The Gymnasium adapter:

- maps structured observation/action spaces to flat arrays;
- checks the first observation and action against the original spaces;
- returns separate terminal and truncation values;
- requires reset before step and reset after episode end.

The PettingZoo adapter:

- targets the Parallel API;
- uses `possible_agents` as the fixed slot set;
- pads missing agents and exposes masks;
- canonicalizes per-agent spaces and flattened buffers.

Validate heterogeneous-agent spaces before use. The adapter derives its single
spaces from the first possible agent, so environments with incompatible spaces
need an explicit reviewed transformation.

### Structured spaces

Stable emulation supports Box, Discrete, MultiDiscrete, Tuple, and Dict patterns
through a packed NumPy dtype. This is byte-layout conversion, not semantic
feature engineering. Check:

- deterministic Dict key order;
- leaf shape and dtype;
- finite numeric values;
- lossless action reconstruction;
- policy-side unflattening;
- padding/mask handling for variable populations.

## Historical 4.0 Ocean contract

The reviewed 4.0 source focuses on first-party C environments. It no longer
provides the 3.0 Python emulation/vector modules. The official s

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

