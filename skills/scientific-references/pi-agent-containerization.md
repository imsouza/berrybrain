---
id: sciref-pi-agent-containerization
name: "Scientific Ref: Containerization"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pi-agent): Containerization"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "agent containerization"
  - "containerization"
keywords:
  - "agent"
  - "containerization"
  - "specialized"
  - "scientific"
  - "reference"
---

# Containerization

Source: https://pi.dev/docs/latest/containerization

Reviewed against Pi 0.99.2 and the package versions listed in `../SKILL.md` on 2026-09-30.

Pi runs with all permissions by default. Two general approaches: run the whole `pi` process inside an isolated environment, or run `pi` on the host and route tool execution into an isolated environment.

| Pattern | What is isolated | Best for | Notes |
|---|---|---|---|
| Gondolin extension | Built-in tools and `!` commands | Local micro-VM isolation while keeping auth on host | `examples/extensions/gondolin/` |
| Plain Docker | Whole `pi` process | Simplest local container boundary | Provider API keys enter the container |
| OpenShell | Whole `pi` process | Local or remote policy-controlled sandbox | Requires an OpenShell gateway |

Extensions run wherever the `pi` process runs. If host Pi routes built-ins into a VM, other custom extension tools still run on the host unless they delegate too.

The commands below follow Pi 0.99.2 documentation and are illustrative: Docker, Gondolin, and OpenShell runtimes were not started during this review.

## Gondolin

[Gondolin](https://github.com/earendil-works/gondolin) is a local Linux micro-VM.

```bash
cp -R packages/coding-agent/examples/extensions/gondolin ~/.pi/agent/extensions/gondolin
cd ~/.pi/agent/extensions/gondolin
npm install --ignore-scripts

cd /path/to/project
pi -e ~/.pi/agent/extensions/gondolin
```

The extension mounts the host cwd at `/workspace` in the VM and overrides `read`, `write`, `edit`, `bash`, `grep`, `find`, and `ls`. User `!` commands are routed into the VM as well, and file changes under `/workspace` write through to the host.

Requirements: Node.js >= 23.6.0 for `@earendil-works/gondolin`, plus QEMU installed through your package manager.

## Plain Docker

`Dockerfile.pi`:

```dockerfile
FROM node:24-bookworm-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends bash ca-certificates git ripgrep \
  && rm -rf /var/lib/apt/lists/*
RUN npm install -g --ignore-scripts @earendil-works/pi-coding-agent

WORKDIR /workspace
ENTRYPOINT ["pi"]
```

```bash
docker build -t pi-sandbox -f Dockerfile.pi .

docker run --rm -it \
  -e ANTHROPIC_API_KEY \
  -v "$PWD:/workspace" \
  -v pi-agent-home:/root/.pi/agent \
  pi-sandbox
```

`-v "$PWD:/workspace"` means reads and writes inside `/workspace` affect host files directly. Use a named volume for `/root/.pi/agent` if you want container-local settings and sessions — mounting host `~/.pi/agent` exposes host auth and session files to the container.

## OpenShell

[NVIDIA OpenShell](https://docs.nvidia.com/openshell/about/overview) provides a policy-controlled sandbox with filesystem, process, network, credential, and inference controls. It runs sandboxes through a local gateway backed by Docker, Podman, or a VM runtime, or through a remote Kubernetes gateway. Every sandbox requires an active gateway:

```bash
openshell gateway add <gateway-url> --name <name>
openshell gateway select <name>

openshell sandbox create --name pi-sandbox --from pi -- pi
```

The whole `pi` process runs inside the sandbox, so built-in tools, `!` commands, and extension tools all execute inside the boundary.

Remote gateways do not bind-mount host project files, so sandbox writes are not reflected on your machine. Clone the repository inside the sandbox or transfer files explicitly:

```bash
openshell sandbox upload pi-sandbox ./repo /workspace
openshell sandbox download pi-sandbox /workspace/repo ./repo-out
```

OpenShell providers can keep raw model API keys outside the sandbox: with inference routing configured, code inside the sandbox calls `https://inference.local` and the gateway injects provider credentials upstream. Point Pi at the corresponding OpenAI-compatible or Anthropic-compatible endpoint to use that route.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

