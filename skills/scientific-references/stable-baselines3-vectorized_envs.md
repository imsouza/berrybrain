---
id: sciref-stable-baselines3-vectorized-envs
name: "Scientific Ref: Vectorized Environments in Stable Baselines3"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (stable-baselines3): Vectorized Environments in Stable Baselines3"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "stable baselines3 vectorized envs"
  - "vectorized environments in stable baselines3"
keywords:
  - "stable"
  - "baselines3"
  - "vectorized"
  - "envs"
  - "specialized"
  - "scientific"
  - "reference"
  - "baselines"
---

# Vectorized Environments in Stable Baselines3

Targets SB3 2.9.0 / Gymnasium 1.3.0. Code snippets are illustrative fragments
sharing imports and environment/model variables; run process-based examples in
a Python file under a main guard. The bundled training script and repository
tests exercise DummyVecEnv and SubprocVecEnv with small CPU environments.

## Overview

Vectorized environments stack multiple independent environment instances into a single environment that processes actions and observations in batches. Instead of interacting with one environment at a time, you interact with `n` environments simultaneously.

**Benefits:**
- **Speed:** Process parallelism can help expensive environments; measure IPC overhead
- **Batching:** Collect transitions from independent environments; this does not guarantee better sample efficiency
- **Required for:** Frame stacking and normalization wrappers
- **Better for:** On-policy algorithms (PPO, A2C)

## VecEnv Types

### DummyVecEnv

Executes environments sequentially on the current Python process.

```python
import gymnasium as gym
from stable_baselines3.common.vec_env import DummyVecEnv

# Method 1: Using make_vec_env
from stable_baselines3.common.env_util import make_vec_env

env = make_vec_env("CartPole-v1", n_envs=4, vec_env_cls=DummyVecEnv)

# Method 2: Manual creation
def make_env():
    def _init():
        return gym.make("CartPole-v1")
    return _init

env = DummyVecEnv([make_env() for _ in range(4)])
```

**When to use:**
- Lightweight environments (CartPole, simple grids)
- When multiprocessing overhead > computation time
- Debugging (easier to trace errors)
- Single-threaded environments

**Performance:** No actual parallelism (sequential execution).

### SubprocVecEnv

Executes each environment in a separate process, enabling true parallelism.

```python
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.env_util import make_vec_env

env = make_vec_env("CartPole-v1", n_envs=8, vec_env_cls=SubprocVecEnv)
```

**When to use:**
- Computationally expensive environments (physics simulations, 3D games)
- When environment computation time justifies multiprocessing overhead
- When you need true parallel execution

**Important:** Requires wrapping code in `if __name__ == "__main__":` when using forkserver or spawn:

```python
if __name__ == "__main__":
    env = make_vec_env("CartPole-v1", n_envs=8, vec_env_cls=SubprocVecEnv)
    model = PPO("MlpPolicy", env)
    model.learn(total_timesteps=100000)
```

**Performance:** True parallelism across CPU cores.

## Quick Setup with make_vec_env

The easiest way to create vectorized environments:

```python
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import SubprocVecEnv

# Basic usage
env = make_vec_env("CartPole-v1", n_envs=4)

# With SubprocVecEnv
env = make_vec_env("CartPole-v1", n_envs=8, vec_env_cls=SubprocVecEnv)

# With custom environment kwargs
env = make_vec_env(
    "MyEnv-v0",
    n_envs=4,
    env_kwargs={"difficulty": "hard", "max_steps": 500}
)

# With custom seed
env = make_vec_env("CartPole-v1", n_envs=4, seed=42)
```

## API Differences from Gymnasium

SB3 VecEnv is not Gymnasium VectorEnv. Do not pass a Gymnasium vector environment
directly to an SB3 algorithm or reuse its autoreset/info conventions:

### reset()

**Gymnasium Env:**
```python
obs, info = env.reset()
```

**VecEnv:**
```python
obs = env.reset()  # Returns only observations (numpy array)
# Access info via env.reset_infos (list of dicts)
infos = env.reset_infos
```

**Seeding and options:** Call `vec_env.seed(seed=seed)` and/or `vec_env.set_options(options)` before the initial `reset()`. Seed and options are discarded after each `reset()` call.

**Truncation vs termination:** When an episode ends, check `infos[env_idx]["TimeLimit.truncated"]` to distinguish timeout/truncation from natural termination. It is computed as `truncated and not terminated`, so simultaneous flags count as
termination for bootstrapping. Bootstrap through pure truncation using the
`terminal_observation`, not the auto-reset observation; do not bootstrap through
termination. SB3 algorithms implement this handling internally.

### step()

**Gymnasium Env:**
```python
obs, reward, terminated, truncated, info = env.step(action)
```

**VecEnv:**
```python
obs, rewards, dones, infos = env.step(actions)
# Returns 4-tuple instead of 5-tuple
# dones = terminated | truncated
# actions is an array of shape (n_envs,) or (n_envs, action_dim)
```

### Auto-reset

**VecEnv automatically resets environments when episodes end:**

```python
import numpy as np

obs = env.reset()  # Shape: (n_envs, obs_dim)
for _ in range(1000):
    actions = np.array([env.action_space.sample() for _ in range(env.num_envs)])
    obs, rewards, dones, infos = env.step(actions)
    # If dones[i] is True, env i was automatically reset
    # Final observation before reset available in infos[i]["terminal_observation"]
```

### Terminal Observations

When an episode ends, access the true final observation:

```python
obs, rewards, dones, infos = env.step(actions)

for i, done in enumerate(dones):
    if done:
        # The obs[i] is already the reset observation
        # True terminal observation is in info
        terminal_obs = infos[i]["terminal_observation"]
        print(f"Episode ended with terminal observation: {terminal_obs}")
```

## Training with Vectorized Environments

### On-Policy Algorithms (PPO, A2C)

On-policy algorithms benefit greatly from vectorization:

```python
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import SubprocVecEnv

# Create vectorized environment
env = make_vec_env("CartPole-v1", n_envs=8, vec_env_cls=SubprocVecEnv)

# Train
model = PPO("MlpPolicy", env, verbose=1, n_steps=128)
model.learn(total_timesteps=100000)

# With n_envs=8 and n_steps=128:
# - Collects 8*128=1024 steps per rollout
# - Updates after every 1024 steps
```

Benchmark environment count and keep `n_steps * n_envs` and PPO minibatch
divisibility explicit; changing rollout size also changes optimization.

### Off-Policy Algorithms (SAC, TD3, DQN)

Off-policy algorithms can use vectorization but benefit less:

```python
from stable_baselines3 import SAC
from stable_baselines3.common.env_util import make_vec_env

# Use fewer environments (1-4)
env = make_vec_env("Pendulum-v1", n_envs=4)

# Set gradient

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

