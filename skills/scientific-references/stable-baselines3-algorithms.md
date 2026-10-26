---
id: sciref-stable-baselines3-algorithms
name: "Scientific Ref: Stable Baselines3 Algorithm Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (stable-baselines3): Stable Baselines3 Algorithm Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "stable baselines3 algorithms"
  - "stable baselines3 algorithm reference"
keywords:
  - "stable"
  - "baselines3"
  - "algorithms"
  - "specialized"
  - "scientific"
  - "reference"
  - "baselines"
---

# Stable Baselines3 Algorithm Reference

Targets SB3/SB3-Contrib 2.9.0. Algorithm performance and tuning suggestions below
are task-dependent starting points, not guarantees or benchmark results.
Sources: [action support](https://stable-baselines3.readthedocs.io/en/v2.9.0/guide/algos.html),
[algorithm APIs](https://stable-baselines3.readthedocs.io/en/v2.9.0/modules/ppo.html),
[RL experiment guidance](https://stable-baselines3.readthedocs.io/en/v2.9.0/guide/rl_tips.html).

## Algorithm Comparison Table

| Algorithm | Type | Action Space | Sample Efficiency | Training Speed | Use Case |
|-----------|------|--------------|-------------------|----------------|----------|
| **PPO** | On-Policy | Box/Discrete/MultiDiscrete/MultiBinary | Medium | Fast | General-purpose, stable |
| **A2C** | On-Policy | Box/Discrete/MultiDiscrete/MultiBinary | Low | Very Fast | Quick prototyping, multiprocessing |
| **SAC** | Off-Policy | Continuous | High | Medium | Continuous control, sample-efficient |
| **TD3** | Off-Policy | Continuous | High | Medium | Continuous control, deterministic |
| **DDPG** | Off-Policy | Continuous | High | Medium | Continuous control (use TD3 instead) |
| **DQN** | Off-Policy | Discrete | Medium | Medium | Discrete actions, Atari games |
| **HER** | Replay buffer | Box or Discrete, per underlying algorithm | Task-dependent | Task-dependent | Goal-conditioned tasks |
| **RecurrentPPO** | On-Policy | Box/Discrete/MultiDiscrete/MultiBinary | Medium | Slow | Partial observability (POMDP) |

## Detailed Algorithm Characteristics

### PPO (Proximal Policy Optimization)

**Overview:** General-purpose on-policy algorithm with good performance across many tasks.

**Strengths:**
- Stable and reliable training
- Works with supported action space types (Discrete, Box, MultiDiscrete, MultiBinary)
- Good balance between sample efficiency and training speed
- Excellent for multiprocessing with vectorized environments
- Easy to tune

**Weaknesses:**
- Less sample-efficient than off-policy methods
- Requires many environment interactions

**Best For:**
- General-purpose RL tasks
- When stability is important
- When you have cheap environment simulations
- Tasks with continuous or discrete actions

**Hyperparameter Guidance:**
- `n_steps`: 2048-4096 for continuous, 128-256 for Atari
- `learning_rate`: 3e-4 is a good default
- `n_epochs`: 10 for continuous, 4 for Atari
- `batch_size`: 64
- `gamma`: 0.99 (0.995-0.999 for long episodes)

### A2C (Advantage Actor-Critic)

**Overview:** Synchronous variant of A3C, simpler than PPO but less stable.

**Strengths:**
- Very fast training (simpler than PPO)
- Works with supported action space types
- Good for quick prototyping
- Memory efficient

**Weaknesses:**
- Less stable than PPO
- Requires careful hyperparameter tuning
- Lower sample efficiency

**Best For:**
- Quick experimentation
- When training speed is critical
- Simple environments

**Hyperparameter Guidance:**
- `n_steps`: 5-256 depending on task
- `learning_rate`: 7e-4
- `gamma`: 0.99

### SAC (Soft Actor-Critic)

**Overview:** Off-policy algorithm with entropy regularization, widely used for continuous control.

**Strengths:**
- Excellent sample efficiency
- Very stable training
- Automatic entropy tuning
- Good exploration through stochastic policy
- Suitable baseline for robotics

**Weaknesses:**
- Only supports continuous action spaces (Box)
- Slower wall-clock time than on-policy methods
- More complex hyperparameters

**Best For:**
- Continuous control (robotics, physics simulations)
- When sample efficiency is critical
- Expensive environment simulations
- Tasks requiring good exploration

**Hyperparameter Guidance:**
- `learning_rate`: 3e-4
- `buffer_size`: 1M for most tasks
- `learning_starts`: 10000
- `batch_size`: 256
- `tau`: 0.005 (target network update rate)
- `train_freq`: 1 with `gradient_steps=-1` as one update-to-data ratio to evaluate

### TD3 (Twin Delayed DDPG)

**Overview:** Improved DDPG with double Q-learning and delayed policy updates.

**Strengths:**
- High sample efficiency
- Deterministic policy (good for deployment)
- More stable than DDPG
- Good for continuous control

**Weaknesses:**
- Only supports continuous action spaces (Box)
- Less exploration than SAC
- Requires careful tuning

**Best For:**
- Continuous control tasks
- When deterministic policies are preferred
- Sample-efficient learning

**Hyperparameter Guidance:**
- `learning_rate`: 1e-3
- `buffer_size`: 1M
- `learning_starts`: 10000
- `batch_size`: 256 (current TD3 default)
- `policy_delay`: 2 (update policy every 2 critic updates)

### DDPG (Deep Deterministic Policy Gradient)

**Overview:** Early off-policy continuous control algorithm.

**Strengths:**
- Continuous action space support
- Off-policy learning

**Weaknesses:**
- Less stable than TD3 or SAC
- Sensitive to hyperparameters
- Generally outperformed by TD3

**Best For:**
- Legacy compatibility
- **Recommendation:** Use TD3 instead for new projects

### DQN (Deep Q-Network)

**Overview:** Classic off-policy algorithm for discrete action spaces.

**Strengths:**
- Sample-efficient for discrete actions
- Experience replay enables reuse of past data
- Proven success on Atari games

**Weaknesses:**
- Only supports discrete action spaces
- Can be unstable without proper tuning
- Overestimation bias

**Best For:**
- Discrete action tasks
- Atari games and similar environments
- When sample efficiency matters

**Hyperparameter Guidance:**
- `learning_rate`: 1e-4
- `buffer_size`: 100K-1M depending on task
- `learning_starts`: 50000 for Atari
- `batch_size`: 32
- `exploration_fraction`: 0.1
- `exploration_final_eps`: 0.05

**Variants:**
- **QR-DQN**: Distributional RL version for better value estimates (SB3-Contrib)
- **MaskablePPO**: Contrib supports invalid action masking with PPO; there is no released `MaskableDQN` in contrib 2.9.0.

### HER (Hindsight Experience Replay)

**Overview:** Not a standalone algorithm but a replay buffer strategy for goal-conditioned tasks.

**Strengths:**
- Dramatically improves learning in sparse reward settings
- Learns from failures by relabeling goals
- Supports SB3 off-policy algorithms using compatible Dict replay buffers (SAC, TD3, DDPG, DQN)

**Weaknesses:**
- Only for goal-conditioned environments
- Requires specific observation structure (Dict with "observation", "achieved_goal", "desired_goal")

**Best For:**
- Goal-conditioned tasks (robotics manipulation, navigation)
- Sparse reward environments
- 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

