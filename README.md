# Local Vector Store & MCP Server

Lightweight vector store with TF‑IDF search, a small FastAPI HTTP API, and an MCP stdio server. Ingests documents from `input/html`, `input/md`, and `input/PDF` and stores artifacts under `data/vector_store`.

## Usage (Local)
- Install: `pip install -r requirements.txt`
- Ingest data: `make ingest` (reads `input/html`, `input/md`, and `input/PDF`)
- Query via CLI: `make query Q="security maturity" K=5`
- HTTP API (after deployment below):
  - Health: `curl localhost:8000/health`
  - Ingest: `curl -X POST localhost:8000/ingest`
  - Query: `curl -X POST localhost:8000/query -H 'Content-Type: application/json' -d '{"query":"security maturity","k":5}'`
- Vector Store Manager (interactive): `make manage`
  - Examples: `status`, `docs --limit 10`, `chunks input/PDF/example.pdf --limit 5`, `search "zero trust" --k 5`, `ingest`, `purge`, `export assets/index_backup.jsonl`, `help`, `exit`

## Deployment
### Docker (single container)
- Build: `docker build -t local/vector-mcp:latest .`
- Run: `docker run -p 8000:8000 -e AUTO_INGEST=1 -v "$PWD/input:/app/input" -v "$PWD/data:/app/data" local/vector-mcp:latest`
  - Visit `http://localhost:8000/health` or use curl examples above.

### Docker Compose
- Build images: `make docker-build`
- Start services: `make docker-up` (HTTP server on `:8000`)
- View logs: `make docker-logs`
- Ingest inside container: `make docker-ingest`
- Query inside container: `make docker-query Q="your query" K=5`
- Stop: `make docker-down`

### MCP Stdio Server
- Local: `make mcp-stdio` (runs `python -m src.mcp_server`)
- Compose service: `make mcp-stdio-up` (optional background service); `make mcp-stdio-down` to remove.

## Data Layout
- Input: `input/html/**/*.html`, `input/md/**/*.md`, `input/PDF/**/*.pdf`
- Artifacts: `data/vector_store/{vectorizer.json,index.jsonl,meta.json}`

Notes
- Ensure `input/` contains documents before running ingest.
- Set `AUTO_INGEST=1` to ingest on container start (Docker only).
