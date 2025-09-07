import argparse
from src.vector_store import load_default_store


def main():
    p = argparse.ArgumentParser(description="Query the local vector store")
    p.add_argument("query", type=str, help="Query text")
    p.add_argument("--k", type=int, default=5, help="Top-k results to return")
    args = p.parse_args()

    store = load_default_store()
    if not store.is_ready():
        print("Vector store not ready. Run `make ingest` first.")
        return

    results = store.query(args.query, k=args.k)
    for rank, (score, rec) in enumerate(results, start=1):
        print(f"#{rank} score={score:.4f} path={rec.path} chunk={rec.chunk_id}")
        snippet = rec.text
        if len(snippet) > 240:
            snippet = snippet[:240] + "…"
        print(f"  {snippet}\n")


if __name__ == "__main__":
    main()

