FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FASTEMBED_CACHE_PATH=/opt/models

WORKDIR /srv

COPY requirements.txt ./
RUN pip install -r requirements.txt

# Bake the embedding model (~2.2 GB) into the image so there is no download at runtime.
COPY app/embeddings_model.py ./app/embeddings_model.py
RUN python -c "from app.embeddings_model import MODEL_NAME; from fastembed import TextEmbedding; TextEmbedding(MODEL_NAME)"

COPY app ./app
COPY scripts ./scripts
COPY data ./data
COPY log_config.json ./

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "log_config.json"]
