import json
import math
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .tfidf import TfidfVectorizer


@dataclass
class VectorRecord:
    path: str
    chunk_id: int
    text: str
    indices: List[int]
    values: List[float]
    norm: float


def _sparse_norm(values: List[float]) -> float:
    return math.sqrt(sum(v * v for v in values)) if values else 1e-12


def _cosine_sim(a_idx: List[int], a_val: List[float], a_norm: float,
                b_idx: List[int], b_val: List[float], b_norm: float) -> float:
    i = j = 0
    dot = 0.0
    while i < len(a_idx) and j < len(b_idx):
        if a_idx[i] == b_idx[j]:
            dot += a_val[i] * b_val[j]
            i += 1
            j += 1
        elif a_idx[i] < b_idx[j]:
            i += 1
        else:
            j += 1
    denom = (a_norm or 1e-12) * (b_norm or 1e-12)
    return dot / denom


class VectorStore:
    def __init__(self, root: str):
        self.root = root
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.records: List[VectorRecord] = []

    @property
    def vectorizer_path(self) -> str:
        return os.path.join(self.root, "vectorizer.json")

    @property
    def index_path(self) -> str:
        return os.path.join(self.root, "index.jsonl")

    def load(self) -> None:
        self.vectorizer = TfidfVectorizer.load(self.vectorizer_path)
        self.records = []
        if not os.path.exists(self.index_path):
            return
        with open(self.index_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                obj = json.loads(line)
                self.records.append(
                    VectorRecord(
                        path=obj["path"],
                        chunk_id=int(obj["chunk_id"]),
                        text=obj["text"],
                        indices=list(obj["embedding"]["indices"]),
                        values=list(obj["embedding"]["values"]),
                        norm=float(obj["embedding"]["norm"]),
                    )
                )

    def is_ready(self) -> bool:
        return self.vectorizer is not None and len(self.records) > 0

    def query(self, text: str, k: int = 5) -> List[Tuple[float, VectorRecord]]:
        if self.vectorizer is None:
            raise RuntimeError("Vectorizer not loaded.")
        (q_idx, q_val) = self.vectorizer.transform_sparse([text])[0]
        q_norm = _sparse_norm(q_val)
        scored: List[Tuple[float, VectorRecord]] = []
        for rec in self.records:
            s = _cosine_sim(q_idx, q_val, q_norm, rec.indices, rec.values, rec.norm)
            scored.append((s, rec))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:k]

    def save(self) -> None:
        os.makedirs(self.root, exist_ok=True)
        # Persist index.jsonl
        with open(self.index_path, "w", encoding="utf-8") as f:
            for rec in self.records:
                obj = {
                    "path": rec.path,
                    "chunk_id": rec.chunk_id,
                    "text": rec.text,
                    "embedding": {
                        "indices": rec.indices,
                        "values": rec.values,
                        "norm": rec.norm,
                    },
                }
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        # Persist meta.json
        meta = {
            "total_files": len({r.path for r in self.records}),
            "total_chunks": len(self.records),
        }
        with open(os.path.join(self.root, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f)


def load_default_store() -> VectorStore:
    root = os.path.join("data", "vector_store")
    vs = VectorStore(root)
    vs.load()
    return vs
