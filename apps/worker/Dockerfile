FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
COPY apps/worker ./apps/worker
RUN pip install --no-cache-dir ./apps/worker

WORKDIR /app
COPY prompts ./prompts
COPY scripts/validate-env.sh scripts/prepare-runtime-dirs.sh ./scripts/
RUN mkdir -p /app/data/sqlite /app/data/jobs /app/data/logs /app/data/backups /app/vault

CMD ["sh", "-c", "sh /app/scripts/validate-env.sh worker && sh /app/scripts/prepare-runtime-dirs.sh && python -u -m berrybrain_worker.main"]
