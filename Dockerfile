FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps (optional: add build tools if needed)
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

# Expose FastAPI server
EXPOSE 8000

# Set a non-root user for safety
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Default command runs the HTTP server; call /ingest afterward or set AUTO_INGEST=1.
ENV AUTO_INGEST="0"
CMD ["sh", "-c", "if [ \"$AUTO_INGEST\" = \"1\" ]; then python -m src.ingest; fi && uvicorn src.web:app --host 0.0.0.0 --port 8000"]

