import asyncio
import json
from typing import Any, Dict, List

from mcp.server import Server
from mcp import types
from mcp.server.stdio import stdio_server

from .ingest import ingest as run_ingest
from .vector_store import load_default_store


server = Server("vector-store")


@server.list_tools()
def list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name="ingest",
            description="Scan input/html and input/PDF, build TF-IDF vector store.",
            inputSchema={"type": "object"},
        ),
        types.Tool(
            name="query",
            description="Query the vector store and return top-k chunks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "k": {"type": "integer", "default": 5, "minimum": 1, "maximum": 50},
                },
                "required": ["query"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(
    name: str,
    arguments: Dict[str, Any] | None,
    *,
    request,
):
    arguments = arguments or {}
    if name == "ingest":
        # Run synchronously; ingestion may take time
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, run_ingest)
        return [types.CallToolResult(content=[types.TextContent(type="text", text="ingest: ok")])]

    if name == "query":
        q = str(arguments.get("query", "")).strip()
        k = int(arguments.get("k", 5))
        store = load_default_store()
        if not store.is_ready():
            return [
                types.CallToolResult(
                    isError=True,
                    content=[
                        types.TextContent(
                            type="text", text="vector store not ready; run ingest first"
                        )
                    ],
                )
            ]
        results = store.query(q, k=max(1, min(50, k)))
        payload = [
            {
                "score": float(score),
                "path": rec.path,
                "chunk_id": rec.chunk_id,
                "text": rec.text,
            }
            for score, rec in results
        ]
        return [types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(payload))])]

    return [
        types.CallToolResult(
            isError=True, content=[types.TextContent(type="text", text=f"unknown tool: {name}")]
        )
    ]


async def main() -> None:
    async with stdio_server() as (read, write):
        await server.run(read, write, {"name": "vector-store", "version": "0.1.0"})


if __name__ == "__main__":
    asyncio.run(main())
