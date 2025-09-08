import os
import json
from glob import glob
from typing import List, Tuple

from .text_extraction import (
    extract_text_from_html,
    extract_text_from_pdf,
    extract_text_from_markdown,
)
from .chunking import chunk_text
from .tfidf import TfidfVectorizer
from .vector_store import _sparse_norm


def find_input_files() -> Tuple[List[str], List[str], List[str]]:
    html_files = glob(os.path.join("input", "html", "**", "*.html"), recursive=True)
    md_files = glob(os.path.join("input", "md", "**", "*.md"), recursive=True)
    pdf_files = []
    pdf_files += glob(os.path.join("input", "PDF", "**", "*.pdf"), recursive=True)
    pdf_files += glob(os.path.join("input", "PDF", "**", "*.PDF"), recursive=True)
    return html_files, md_files, pdf_files


def ensure_dirs():
    for p in [
        "input",
        os.path.join("input", "html"),
        os.path.join("input", "md"),
        os.path.join("input", "PDF"),
        os.path.join("data", "vector_store"),
    ]:
        os.makedirs(p, exist_ok=True)


def ingest():
    ensure_dirs()
    html_files, md_files, pdf_files = find_input_files()
    docs: List[Tuple[str, str]] = []  # (path, text)

    # HTML
    for path in html_files:
        try:
            text = extract_text_from_html(path)
        except Exception:
            text = ""
        if text.strip():
            docs.append((path, text))

    # Markdown
    for path in md_files:
        try:
            text = extract_text_from_markdown(path)
        except Exception:
            text = ""
        if text.strip():
            docs.append((path, text))

    # PDF
    for path in pdf_files:
        text = extract_text_from_pdf(path)
        if not text:
            print(f"[warn] Skipping PDF (no parser available or empty): {path}")
            continue
        docs.append((path, text))

    # Chunk
    chunked_texts: List[str] = []
    chunk_meta: List[Tuple[str, int]] = []  # (path, chunk_id)
    for path, text in docs:
        chunks = chunk_text(text, max_words=300, overlap=50)
        for i, ch in enumerate(chunks):
            if ch.strip():
                chunked_texts.append(ch)
                chunk_meta.append((path, i))

    if not chunked_texts:
        print("[info] No text chunks found. Place files under input/html, input/md, or input/PDF.")
        return

    # Fit TF-IDF and transform
    vectorizer = TfidfVectorizer()
    vectorizer.fit(chunked_texts)
    sparse_vecs = vectorizer.transform_sparse(chunked_texts)

    # Persist vectorizer
    root = os.path.join("data", "vector_store")
    vectorizer.save(os.path.join(root, "vectorizer.json"))

    # Persist index as JSONL
    index_path = os.path.join(root, "index.jsonl")
    with open(index_path, "w", encoding="utf-8") as f:
        for (indices, values), (path, cid), text in zip(sparse_vecs, chunk_meta, chunked_texts):
            rec = {
                "path": path,
                "chunk_id": cid,
                "text": text,
                "embedding": {
                    "indices": indices,
                    "values": values,
                    "norm": _sparse_norm(values),
                },
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # Meta
    meta = {
        "total_files": len(docs),
        "total_chunks": len(chunked_texts),
    }
    with open(os.path.join(root, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f)

    print(f"[ok] Ingested {len(docs)} files into {len(chunked_texts)} chunks.")
    print(f"[ok] Vector store ready at {root}")


if __name__ == "__main__":
    ingest()
