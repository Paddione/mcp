import json
import math
from typing import Dict, List, Tuple


class TfidfVectorizer:
    def __init__(self):
        self.vocabulary_: List[str] = []
        self.vocab_index: Dict[str, int] = {}
        self.idf_: List[float] = []

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        tokens: List[str] = []
        token = []
        for ch in text:
            if ch.isalnum():
                token.append(ch.lower())
            else:
                if token:
                    t = "".join(token)
                    if len(t) > 1:
                        tokens.append(t)
                    token = []
        if token:
            t = "".join(token)
            if len(t) > 1:
                tokens.append(t)
        return tokens

    def fit(self, texts: List[str]) -> None:
        df: Dict[str, int] = {}
        for text in texts:
            seen = set()
            for tok in self._tokenize(text):
                if tok not in seen:
                    df[tok] = df.get(tok, 0) + 1
                    seen.add(tok)
        # Freeze vocabulary in deterministic order
        self.vocabulary_ = sorted(df.keys())
        self.vocab_index = {t: i for i, t in enumerate(self.vocabulary_)}
        n_docs = max(1, len(texts))
        self.idf_ = [math.log((1 + n_docs) / (1 + df[t])) + 1.0 for t in self.vocabulary_]

    def transform_sparse(self, texts: List[str]) -> List[Tuple[List[int], List[float]]]:
        results: List[Tuple[List[int], List[float]]] = []
        for text in texts:
            counts: Dict[int, int] = {}
            total = 0
            for tok in self._tokenize(text):
                idx = self.vocab_index.get(tok)
                if idx is None:
                    continue
                counts[idx] = counts.get(idx, 0) + 1
                total += 1
            if total == 0:
                results.append(([], []))
                continue
            indices = sorted(counts.keys())
            values: List[float] = []
            for i in indices:
                tf = counts[i] / total
                values.append(tf * self.idf_[i])
            results.append((indices, values))
        return results

    def save(self, path: str) -> None:
        data = {"vocabulary": self.vocabulary_, "idf": self.idf_}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    @classmethod
    def load(cls, path: str) -> "TfidfVectorizer":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        obj = cls()
        obj.vocabulary_ = list(data.get("vocabulary", []))
        obj.vocab_index = {t: i for i, t in enumerate(obj.vocabulary_)}
        obj.idf_ = list(data.get("idf", [1.0] * len(obj.vocabulary_)))
        return obj

