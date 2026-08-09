FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    BERRYBRAIN_PROJECT_ROOT=/app
ARG BERRYBRAIN_PREFETCH_WHISPER_MODEL=false

WORKDIR /build
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*
COPY apps/api/pyproject.toml /tmp/berrybrain-api/pyproject.toml
RUN mkdir -p /tmp/berrybrain-api/src/berrybrain_api \
    && touch /tmp/berrybrain-api/src/berrybrain_api/__init__.py \
    && pip install --no-cache-dir /tmp/berrybrain-api
COPY apps/api ./apps/api
RUN pip install --no-cache-dir --no-deps --force-reinstall ./apps/api
RUN if [ "$BERRYBRAIN_PREFETCH_WHISPER_MODEL" = "true" ]; then \
      python -c "from huggingface_hub import snapshot_download; snapshot_download('Systran/faster-whisper-tiny.en', revision='0d3d19a32d3338f10357c0889762bd8d64bbdeba', local_dir='/opt/berrybrain/models/faster-whisper-tiny.en')"; \
    else \
      mkdir -p /opt/berrybrain/models; \
    fi

WORKDIR /app
COPY prompts ./prompts
COPY scripts/validate-env.sh scripts/prepare-runtime-dirs.sh ./scripts/
COPY apps/api/scripts/seed_admin.py apps/api/scripts/delete_owner.py ./scripts/
RUN mkdir -p /app/data/sqlite /app/data/jobs /app/data/logs /app/data/backups /app/vault

EXPOSE 8000
CMD ["sh", "-c", "sh /app/scripts/validate-env.sh api && sh /app/scripts/prepare-runtime-dirs.sh && uvicorn berrybrain_api.main:app --host 0.0.0.0 --port 8000"]
