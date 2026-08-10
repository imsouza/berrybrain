FROM python:3.11-slim

WORKDIR /app

# ponytail: only stdlib + fastapi/httpx needed (no torch/igraph/vLLM)
COPY apps/hipporag/requirements.txt .
RUN pip install --no-cache-dir --upgrade \
        "setuptools>=84.0.0" \
    && pip install --no-cache-dir -r requirements.txt

COPY apps/hipporag/main.py .

# Per-vault KG lives in /data/hipporag.db (SQLite). Mount a named volume here.
VOLUME ["/data"]

ENV HIPPORAG_DATA_DIR=/data \
    HIPPORAG_LLM_URL="" \
    HIPPORAG_SERVICE_TOKEN=""

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
