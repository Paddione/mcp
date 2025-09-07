PYTHON := python3

.PHONY: ingest query manage build test lint fmt run docker-build docker-up docker-down docker-logs docker-ingest docker-query mcp-stdio mcp-stdio-up mcp-stdio-down

ingest:
	$(PYTHON) -m src.ingest

query:
	@if [ -z "$(Q)" ]; then echo "Usage: make query Q=\"your query\" [K=5]"; exit 1; fi
	$(PYTHON) -m scripts.query "$(Q)" --k $${K:-5}

manage:
	$(PYTHON) -m scripts.manage_vector_store

build:
	@echo "No build step required (pure Python)."

test:
	@echo "No tests defined yet."

lint:
	@echo "Add lint tools (ruff/eslint) as needed."

fmt:
	@echo "Add formatters (black/prettier) as needed."

run: ingest
	@echo "Run queries with: make query Q=\"hello world\""

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-ingest:
	docker compose exec -T mcp-server python -m src.ingest || docker compose exec -T vector-mcp python -m src.ingest

# Usage: make docker-query Q="your query" K=5
docker-query:
	@if [ -z "$(Q)" ]; then echo "Usage: make docker-query Q=\"your query\" [K=5]"; exit 1; fi
	docker compose exec -T mcp-server python -m scripts.query "$(Q)" --k $${K:-5} || \
	  docker compose exec -T vector-mcp python -m scripts.query "$(Q)" --k $${K:-5}

# Run MCP stdio server directly (foreground)
mcp-stdio:
	python -m src.mcp_server

# Run MCP stdio server inside Docker (service)
mcp-stdio-up:
	docker compose up -d mcp-stdio

mcp-stdio-down:
	docker compose rm -sf mcp-stdio || true
