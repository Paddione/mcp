from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from .ingest import ingest as run_ingest
from .vector_store import load_default_store


app = FastAPI(title="Local Vector Store Server", version="0.1.0")


class QueryRequest(BaseModel):
    query: str
    k: int = 5


class QueryResult(BaseModel):
    score: float
    path: str
    chunk_id: int
    text: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
def ingest():
    run_ingest()
    return {"status": "ok"}


@app.post("/query", response_model=List[QueryResult])
def query(req: QueryRequest):
    store = load_default_store()
    if not store.is_ready():
        return []
    results = store.query(req.query, k=req.k)
    out: List[QueryResult] = []
    for score, rec in results:
        out.append(QueryResult(score=score, path=rec.path, chunk_id=rec.chunk_id, text=rec.text))
    return out

