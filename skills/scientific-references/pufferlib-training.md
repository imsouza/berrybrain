---
id: sciref-pufferlib-training
name: "Scientific Ref: Training, Evaluation, Configuration, and Logging"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pufferlib): Training, Evaluation, Configuration, and Logging"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pufferlib training"
  - "training, evaluation, configuration, and logging"
keywords:
  - "pufferlib"
  - "training"
  - "specialized"
  - "scientific"
  - "reference"
  - "evaluation"
---

# Training, Evaluation, Configuration, and Logging

Review: **2026-10-01**. Native 5.0 guidance is in [native-5.md](native-5.md);
3.0 and the pinned 4.0 snapshot below are historical profiles.

## Choose a version profile first

### Published stable package

PyPI's latest stable `pufferlib` release is **3.0.0**, published
**2025-06-23**. It declares Python `>=3.9` and is distributed only as a
60.7 MB source archive:

```text
pufferlib-3.0.0.tar.gz
sha256: 7df3a3e3f5f894d78d2a1f5374097890aec01473183e748abefe4f3faa10eaa9
```

The uploaded metadata depends on NumPy `<2.0`, Gym `<=0.23`, Gymnasium
`<=0.29.1`, PettingZoo `<=1.24.1`, Shimmy, Torch, Neptune, W&B, and other
packages without a complete transitive lock. It does not declare a CUDA
version or a minimum Torch version. Do not invent compatibility guarantees.

### Reviewed 4.0 source line

The historical branch is `4.0`; its `pyproject.toml` says version `4.0.0`,
Python `>=3.10`, and Torch `>=2.9`. As of the research date, this source line
is not the latest stable PyPI artifact.

The historical PufferTank 4.0 Dockerfile uses:

- Ubuntu 24.04
- NVIDIA CUDA `13.0.2` cuDNN development image
- Python 3.12
- the CUDA 13.0 PyTorch wheel index
- Nsight Systems `2025.6.3`

The Dockerfile does **not** pin an exact Torch wheel, uv version, PufferLib
commit, or every apt package. It is an upstream convenience environment, not a
complete reproducibility lock.

## Reproducible uv workflow

Installation/native training commands in this reference are illustrative and
were not executed in this review. Source signatures below were checked against
the hash-verified PyPI sdist, which differs from branch `3.0`.

Do not use an unpinned `uv pip install pufferlib`. Work in a disposable,
project-specific environment and commit `pyproject.toml` plus `uv.lock`.

For the published profile, after reviewing the source archive and build:

```bash
uv venv --python 3.11
uv add --exact --no-sync "pufferlib==3.0.0"
uv lock
uv sync --frozen
```

Confirm the lock records the published SHA-256 above and review every resolved
dependency. The 3.0.0 source build can compile native code and may fetch build
assets. Resolve and build in a sandbox with no credentials or sensitive mounts.
Do not treat a successful resolver run as a security review.

For 4.0 source work, pin an immutable revision rather than branch `4.0`:

```bash
uv add --no-sync \
  "pufferlib @ git+https://github.com/PufferAI/PufferLib.git@25647630e1b15330bb3153a5a0d3ff8d234c3acf"
uv lock
```

The commit above is the reviewed 4.0 branch head on 2026-07-23. Re-review before
updating it. Native training still requires an audited build of a specific
environment; uv locking does not lock compilers, CUDA, NCCL, cuDNN, Raylib, or
system libraries.

Never run remote install scripts directly from a pipe. Download, inspect, pin,
verify, and execute only in an appropriate sandbox.

## Published 3.0.0 training

### CLI

The 3.0 console entry point is `puffer = pufferlib.pufferl:main`:

```bash
puffer train ENV_NAME [OPTIONS]
puffer eval ENV_NAME [OPTIONS]
puffer sweep ENV_NAME [OPTIONS]
puffer autotune ENV_NAME [OPTIONS]
puffer profile ENV_NAME [OPTIONS]
puffer export ENV_NAME [OPTIONS]
```

Environment, vector, policy, recurrent, training, and sweep values come from
INI sections. Overrides use section-qualified flags:

```bash
puffer train puffer_breakout \
  --train.device cpu \
  --train.total-timesteps 100000 \
  --vec.backend Serial \
  --vec.num-envs 2
```

Run `puffer train ENV_NAME --help` against the exact locked environment because
available options are generated from merged INI files.

### Python API

The stable trainer is `pufferlib.pufferl.PuffeRL`, not a top-level
`pufferlib.PuffeRL`:

```python
from pufferlib import pufferl

args = pufferl.load_config("puffer_breakout")
vecenv = pufferl.load_env("puffer_breakout", args)
policy = pufferl.load_policy(args, vecenv)
train_config = dict(args["train"], env="puffer_breakout")
trainer = pufferl.PuffeRL(train_config, vecenv, policy)

try:
    while trainer.epoch < trainer.total_epochs:
        trainer.evaluate()
        trainer.train()
finally:
    trainer.close()
```

The exact public methods include `evaluate`, `train`, `mean_and_log`,
`save_checkpoint`, `print_dashboard`, and `close`. Use the CLI when possible;
the Python trainer is a relatively low-level implementation surface.

### Stable configuration checks

- Make rollout/batch relationships explicit; do not rely on `auto` in a
  published experiment.
- Record environment, vector, policy, recurrent, and train sections verbatim.
- Seed Python, NumPy and Torch **before constructing the policy**, in addition
  to environment/action-space seeds. The sdist trainer reads `[train] seed` for
  vector reset but leaves Python/NumPy/Torch seeding commented out. A config seed
  alone does not seed initial weights.
- Record `torch_deterministic`, precision, compile settings, optimizer, horizon,
  minibatch, and total timesteps.
- Keep evaluation seeds, instances, and metrics separate from training.

### Important 3.0 learner limitations

The sdist allocates a truncation tensor but does not populate it in rollouts;
it leaves a TODO for separate truncation handling and explicitly notes that
masks are not yet handled in the learner. Preserving adapter flags does not
prove correct time-limit targets or exclusion of inactive PettingZoo slots.
Audit/fix the learner and run a short analytic terminal/truncation/mask test
before using those cases for scientific conclusions. `evaluate()` collects
training rollouts; it is not held-out evaluation. The stock `puffer eval` path
is a rendering loop, not a bounded multi-episode statistical evaluator.

The planner's `horizon` maps to `--train.bptt-horizon` in 3.0 and
`--train.horizon` in 4.0. Its preview leaves environment-specific rollout size,
zero-copy/start-method selection and native build/device selection to the
caller. In 3.0, record `batch_size` explicitly, ensure it is at least the
minibatch and provides enough horizon segments for every agent. CLI booleans
in the historical parsers use Python `bool(string)`: `False` is truthy. Set
false-valued booleans in INI or the Python argument mapping, not textual CLI
`False`, then inspect the resolved config.

## Historical 4.0 training

Build one audited environment, then use:

```bash
puffer train breakout
puffer eval breakout --load-model-path checkpoints/.../weights.bin
puffer sweep breakout
puffer match breakout \
  --load-

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

