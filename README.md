# BerryBrain

<img src="apps/web/public/berrylogo.png" alt="BerryBrain" width="96" align="right">

**Segundo cérebro local para estudos com IA.**  
Escreva notas em Markdown — o BerryBrain assimila, conecta e organiza o conhecimento automaticamente.

---

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.12+-3670A0?logo=python)
![Next.js](https://img.shields.io/badge/next.js-15-black?logo=next.js)
![FastAPI](https://img.shields.io/badge/fastapi-0.115-009688?logo=fastapi)
![Docker](https://img.shields.io/badge/docker-✓-2496ED?logo=docker)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Funcionalidades

| Funcionalidade | Descrição |
|---------------|-----------|
| **Vault Markdown** | Gerencie notas `.md` com detecção automática de novos arquivos |
| **Assimilação automática** | Parsing, classificação, resumo, embeddings vetoriais e conexões entre notas |
| **Grafo de conhecimento** | Visualização interativa de nós e conexões com pan, zoom e drag |
| **Insights da IA** | Detecção de padrões, lacunas, relações e trilhas de estudo |
| **Atividade automática** | Timeline em linguagem humana do que o sistema processou |
| **Notificações** | Alertas de jobs falhos, provider offline e ações pendentes |
| **Editor Markdown** | Wiki links `[[nota]]`, frontmatter YAML, autosave, preview |
| **Multi-provider IA** | NVIDIA NIM, OpenAI, DeepSeek ou Ollama local |

## Arquitetura

```
Frontend (Next.js 15)  →  API (FastAPI)  →  Jobs (SQLite)  →  Worker (Python)  →  IA
                                                                                      ↓
                                                                                  API / Data
```

O frontend nunca chama a IA diretamente. Todo processamento passa pela fila de jobs assíncrona.

### Estrutura do projeto

```
berrybrain/
  docker-compose.yml
  apps/
    web/          # Next.js 15 + React + Tailwind
    api/          # FastAPI + SQLAlchemy + SQLite
    worker/       # Worker Python assíncrono
  vault/          # Suas notas Markdown
  prompts/        # Prompts de IA versionados
```

## Stack

| Camada | Principais tecnologias |
|--------|----------------------|
| Frontend | React 19, Next.js 15, Tailwind CSS, TypeScript |
| Backend | FastAPI, SQLAlchemy, SQLite, Pydantic |
| Worker | Python 3.12+, httpx, asyncio |
| IA | NVIDIA NIM, OpenAI, DeepSeek, Ollama |
| Infra | Docker, docker-compose |

## Como usar

### Pré-requisitos

- Docker e docker-compose
- Chave de API (NVIDIA NIM, OpenAI ou DeepSeek) **ou** Ollama rodando

```bash
git clone https://github.com/imsouza/berrybrain.git
cd berrybrain
cp .env.example .env
# edite .env com sua chave
docker compose up -d
```

| Serviço | URL |
|---------|-----|
| Web | `http://localhost:3000` |
| API | `http://localhost:8000` |
| Health | `http://localhost:8000/health` |

## API

| Endpoint | Descrição |
|----------|-----------|
| `GET /api/v1/home/summary` | Resumo da Home com status, jobs, insights e grafo |
| `GET /api/v1/insights` | Insights gerados pela IA |
| `POST /api/v1/insights/generate` | Dispara geração de novos insights |
| `POST /api/v1/insights/sync` | Sincroniza insights do worker |
| `GET /api/v1/graph` | Dados do grafo de conhecimento |
| `POST /api/v1/graph/expand` | Expande o grafo com novos nós |
| `GET /api/v1/notes` | Lista notas do vault |
| `POST /api/v1/notes` | Cria nova nota |
| `GET /api/v1/jobs` | Status dos jobs |

## Modelos cloud recomendados

| Provedor | Modelo | Uso |
|----------|--------|-----|
| NVIDIA NIM | `qwen/qwen3.5-397b-a17b` | Insights de grafo, raciocínio profundo |
| NVIDIA NIM | `qwen/qwen3.5-32b-a17b` | Assimilação, classificação |
| NVIDIA NIM | `meta/llama-3.3-70b-instruct` | Títulos e conexões |
| NVIDIA NIM | `nvidia/nv-embedqa-e5-v5` | Embeddings vetoriais |
| OpenAI | `gpt-4o` | Uso geral, alta qualidade |
| OpenAI | `gpt-4o-mini` | Rápido, baixo custo |
| DeepSeek | `deepseek-chat` | Raciocínio e análise |
| DeepSeek | `deepseek-reasoner` | Insights complexos |

## Plano de versionamento

| Versão | Status | Descrição |
|--------|--------|-----------|
| `1.0.0` | atual | Fundação: vault, autopilot, grafo, insights, atividade, notificações |
| `1.1.0` | planejada | Busca semântica, embeddings cloud, flashcards |
| `1.2.0` | planejada | Revisão espaçada, plugins, exportação |
| `2.0.0` | planejada | Colaboração em tempo real, multi-vault, sincronização Git |

Versões seguem [SemVer](https://semver.org/lang/pt-BR/).  
`MAJOR.MINOR.PATCH` — quebra de compatibilidade, novas funcionalidades, correções.

## Licença

MIT © 2025 BerryBrain