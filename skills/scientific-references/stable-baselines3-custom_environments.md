---
id: sciref-stable-baselines3-custom-environments
name: "Scientific Ref: Creating Custom Environments for Stable Baselines3"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (stable-baselines3): Creating Custom Environments for Stable Baselines3"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "stable baselines3 custom environments"
  - "creating custom environments for stable baselines3"
keywords:
  - "stable"
  - "baselines3"
  - "custom"
  - "environments"
  - "specialized"
  - "scientific"
  - "reference"
  - "baselines"
  - "creating"
---

# Creating Custom Environments for Stable Baselines3

Targets Gymnasium 1.3.0 and SB3 2.9.0. Partial classes/methods below are
illustrative design fragments; the executable complete template is
[custom_env_template.py](../scripts/custom_env_template.py). The template observes
both agent and random goal, and the registered environment has a 100-step limit.
A hidden random goal makes a different, partially observable problem; an API
checker cannot detect that scientific error.

## Environment Structure

### Required Methods

Every custom environment must inherit from `gymnasium.Env` and implement:

```python
import gymnasium as gym
from gymnasium import spaces
import numpy as np

class CustomEnv(gym.Env):
    def __init__(self):
        """Initialize environment, define action_space and observation_space"""
        super().__init__()
        self.action_space = spaces.Discrete(4)
        self.observation_space = spaces.Box(low=0, high=1, shape=(4,), dtype=np.float32)

    def reset(self, seed=None, options=None):
        """Reset environment to initial state"""
        super().reset(seed=seed)
        observation = self.np_random.random(4).astype(np.float32)
        info = {}
        return observation, info

    def step(self, action):
        """Execute one timestep"""
        observation = self.np_random.random(4).astype(np.float32)
        reward = 0.0
        terminated = False  # Episode ended naturally
        truncated = False   # Episode ended due to time limit
        info = {}
        return observation, reward, terminated, truncated, info

    def render(self):
        """Visualize environment (optional)"""
        pass

    def close(self):
        """Cleanup resources (optional)"""
        pass
```

### Method Details

#### `__init__(self, ...)`

**Purpose:** Initialize the environment and define spaces.

**Requirements:**
- Must call `super().__init__()`
- Must define `self.action_space`
- Must define `self.observation_space`

**Example:**
```python
def __init__(self, grid_size=10, max_steps=100):
    super().__init__()
    self.grid_size = grid_size
    self.max_steps = max_steps
    self.current_step = 0

    # Define spaces
    self.action_space = spaces.Discrete(4)
    self.observation_space = spaces.Box(
        low=0, high=grid_size-1, shape=(4,), dtype=np.float32
    )
```

#### `reset(self, seed=None, options=None)`

**Purpose:** Reset the environment to an initial state.

**Requirements:**
- Must call `super().reset(seed=seed)`
- Must return `(observation, info)` tuple
- Observation must match `observation_space`
- Info must be a dictionary (can be empty)

**Example:**
```python
def reset(self, seed=None, options=None):
    super().reset(seed=seed)

    # Initialize state
    self.agent_pos = self.np_random.integers(0, self.grid_size, size=2)
    self.goal_pos = self.np_random.integers(0, self.grid_size, size=2)
    self.current_step = 0

    observation = self._get_observation()
    info = {"reset_complete": True}  # "episode" is reserved for Monitor summaries

    return observation, info
```

#### `step(self, action)`

**Purpose:** Execute one timestep in the environment.

**Requirements:**
- Must return 5-tuple: `(observation, reward, terminated, truncated, info)`
- Action must be valid according to `action_space`
- Observation must match `observation_space`
- Reward should be a float
- Terminated: True if episode ended naturally (goal reached, failure, etc.)
- Truncated: True if episode ended due to time limit
- Info must be a dictionary

**Example:**
```python
def step(self, action):
    # Apply action
    self.agent_pos += self._action_to_direction(action)
    self.agent_pos = np.clip(self.agent_pos, 0, self.grid_size - 1)
    self.current_step += 1

    # Calculate reward
    distance = np.linalg.norm(self.agent_pos - self.goal_pos)
    goal_reached = distance < 1.0

    if goal_reached:
        reward = 100.0
    else:
        reward = float(-distance * 0.1)

    # Check termination conditions
    terminated = bool(goal_reached)
    truncated = bool(self.current_step >= self.max_steps)

    observation = self._get_observation()
    info = {"distance": distance, "steps": self.current_step}

    return observation, reward, terminated, truncated, info
```

## Space Types

### Discrete

For discrete actions (e.g., {0, 1, 2, 3}).

```python
self.action_space = spaces.Discrete(4)  # 4 actions: 0, 1, 2, 3
```

**Important:** SB3 does NOT support `Discrete` spaces with `start != 0`. Always start from 0.

### Box (Continuous)

For continuous values within a range.

```python
# 1D continuous action in [-1, 1]
self.action_space = spaces.Box(low=-1, high=1, shape=(1,), dtype=np.float32)

# 2D position observation
self.observation_space = spaces.Box(
    low=0, high=10, shape=(2,), dtype=np.float32
)

# 3D RGB image (channel-first format)
self.observation_space = spaces.Box(
    low=0, high=255, shape=(3, 84, 84), dtype=np.uint8
)
```

**Important for default CNN image preprocessing:**
- Standard images are `dtype=np.uint8` in range [0, 255]
- Use **channel-first** format: (channels, height, width)
- SB3 automatically normalizes by dividing by 255
- For pre-normalized float images, use CHW and `policy_kwargs={"normalize_images": False}`

### MultiDiscrete

For multiple discrete variables.

```python
# Two discrete variables: first with 3 options, second with 4 options
self.action_space = spaces.MultiDiscrete([3, 4])
```

**Important:** If your `MultiDiscrete` space uses multi-dimensional arrays (not a flat vector), the env checker will warn you. Use a wrapper to flatten the space or reshape observations/actions to match SB3's expected 1D layout. See the [SB3 custom env guide](https://stable-baselines3.readthedocs.io/en/v2.9.0/guide/custom_env.html) for the recommended wrapper pattern.

### MultiBinary

For binary vectors.

```python
# 5 binary flags
self.action_space = spaces.MultiBinary(5)  # e.g., [0, 1, 1, 0, 1]
```

### Dict

For dictionary observations (e.g., combining image with sensors).

```python
self.observation_space = spaces.Dict({
    "image": spaces.Box(low=0, high=255, shape=(3, 64, 64), dtype=np.uint8),
    "vector": spaces.Box(low=-10, high=10, shape=(4,), dtype=np.float32),
    "discrete": spaces.Discrete(3),
})
```

**Important:** When using Dict observations, use `"MultiInputPolicy"` instead of `"MlpPolicy"`.

```python
model = PPO("MultiInputPolicy", env, verbose=1)
```

### Tuple

Tuple observations are not supported by SB3 policies. Conv

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

