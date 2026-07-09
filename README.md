# BerryBrain

Segundo cérebro local para estudos com IA. Escreva notas em Markdown, e o BerryBrain assimila, conecta e organiza o conhecimento automaticamente usando IA (NVIDIA NIM, OpenAI, DeepSeek ou Ollama local).

## Funcionalidades

- **Vault Markdown** — gerencie notas `.md` com detecção automática de novos arquivos
- **Assimilação automática** — parsing, classificação, resumo, embeddings e conexões entre notas
- **Grafo de conhecimento** — visualização de nós, conexões e clusters com pan, zoom e drag
- **Insights da IA** — detecção de lacunas, conclusões, hipóteses e trilhas de estudo
- **Atividade automática** — timeline em linguagem humana de tudo que o sistema processou
- **Notificações** — alertas de jobs falhos, provider offline e ações pendentes
- **Editor Markdown** — suporte a wiki links `[[nome da nota]]`, frontmatter YAML e autosave
- **Multi-provider** — NVIDIA NIM, OpenAI, DeepSeek ou Ollama local

## Estrutura

```
berrybrain/
  docker-compose.yml       # Orquestração dos serviços
  .env.example             # Template de variáveis de ambiente
  apps/
    web/                   # Next.js 15 frontend
    api/                   # FastAPI backend (SQLite)
    worker/                # Worker Python (jobs assíncronos)
  vault/                   # Pasta de notas Markdown
  prompts/                 # Prompts de IA versionados
  packages/                # Pacotes compartilhados
```

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend | Next.js 15, React, Tailwind CSS |
| API | FastAPI, SQLAlchemy, SQLite |
| Worker | Python, httpx, asyncio |
| IA | NVIDIA NIM, OpenAI, DeepSeek, Ollama |
| Infra | Docker, docker-compose |

## Como usar

### Pré-requisitos

- Docker e docker-compose
- Chave de API (NVIDIA NIM, OpenAI ou DeepSeek) **ou** Ollama rodando localmente

### Subir o projeto

```bash
cd berrybrain
cp .env.example .env
# Edite .env com sua chave de API e configurações
docker compose up -d
```

Serviços:

| Serviço | URL |
|---------|-----|
| Web | `http://localhost:3000` |
| API | `http://localhost:8000` |
| Healthcheck | `http://localhost:8000/health` |

### Configurar IA

1. Acesse `http://localhost:3000`
2. Clique em Configurações (engrenagem no canto inferior esquerdo)
3. Escolha o provedor: Cloud (NVIDIA NIM / OpenAI / DeepSeek) ou Local (Ollama)
4. Insira API URL e API Key (para cloud) ou URL do Ollama (para local)
5. Configure os modelos recomendados por função

## Endpoints principais

| Endpoint | Descrição |
|----------|-----------|
| `GET /api/v1/home/summary` | Resumo completo da Home |
| `GET /api/v1/insights` | Lista insights gerados |
| `POST /api/v1/insights/generate` | Dispara geração de insights |
| `GET /api/v1/graph` | Dados do grafo de conhecimento |
| `GET /api/v1/notes` | Lista notas do vault |
| `GET /api/v1/jobs` | Status dos jobs do worker |
| `GET /api/v1/activity` | Timeline de atividade |

## Arquitetura

```
Frontend (Next.js) → API (FastAPI) → Jobs (SQLite) → Worker (Python) → IA → API/Data
```

O frontend nunca chama a IA diretamente. Todo processamento passa pela fila de jobs assíncrona processada pelo worker.

## Licença

MIT