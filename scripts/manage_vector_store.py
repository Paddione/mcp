import argparse
import os
import shlex
import sys
from typing import List, Optional

from src.vector_store import load_default_store, VectorRecord


PROMPT = "vector-store> "


def print_status():
    root = os.path.join("data", "vector_store")
    vectorizer = os.path.join(root, "vectorizer.json")
    index = os.path.join(root, "index.jsonl")
    meta = os.path.join(root, "meta.json")
    print(f"Root: {root}")
    print(f" - vectorizer.json: {'ok' if os.path.exists(vectorizer) else 'missing'}")
    print(f" - index.jsonl:     {'ok' if os.path.exists(index) else 'missing'}")
    print(f" - meta.json:       {'ok' if os.path.exists(meta) else 'missing'}")

    store = load_default_store()
    if not store.is_ready():
        print("Status: not ready (ingest required)")
        return
    print("Status: ready")
    print(f"Records: {len(store.records)}")
    by_doc = {}
    for r in store.records:
        by_doc[r.path] = by_doc.get(r.path, 0) + 1
    print(f"Documents: {len(by_doc)}")


def list_docs(limit: Optional[int] = None):
    store = load_default_store()
    if not store.is_ready():
        print("Vector store not ready. Run 'ingest' first.")
        return
    counts = {}
    for r in store.records:
        counts[r.path] = counts.get(r.path, 0) + 1
    items = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    if limit is not None:
        items = items[:limit]
    for path, cnt in items:
        print(f"{cnt:5d}  {path}")
    print(f"Total documents: {len(counts)}; total chunks: {len(store.records)}")


def list_chunks(path: str, limit: Optional[int] = None):
    store = load_default_store()
    if not store.is_ready():
        print("Vector store not ready. Run 'ingest' first.")
        return
    chunks: List[VectorRecord] = [r for r in store.records if r.path == path]
    if not chunks:
        print(f"No chunks for path: {path}")
        return
    chunks.sort(key=lambda r: r.chunk_id)
    if limit is not None:
        chunks = chunks[:limit]
    for r in chunks:
        snippet = r.text.strip().replace("\n", " ")
        if len(snippet) > 120:
            snippet = snippet[:120] + "…"
        print(f"chunk={r.chunk_id:4d}  {snippet}")
    print(f"Total chunks for {path}: {len([x for x in store.records if x.path == path])}")


def search(query: str, k: int = 5):
    store = load_default_store()
    if not store.is_ready():
        print("Vector store not ready. Run 'ingest' first.")
        return
    results = store.query(query, k=k)
    for rank, (score, rec) in enumerate(results, start=1):
        print(f"#{rank}  score={score:.4f}  path={rec.path}  chunk={rec.chunk_id}")
        snippet = rec.text.strip().replace("\n", " ")
        if len(snippet) > 200:
            snippet = snippet[:200] + "…"
        print(f"     {snippet}")


def show(path: str, chunk_id: int):
    store = load_default_store()
    if not store.is_ready():
        print("Vector store not ready. Run 'ingest' first.")
        return
    for r in store.records:
        if r.path == path and r.chunk_id == chunk_id:
            print(f"Path: {r.path}\nChunk: {r.chunk_id}\n---\n{r.text}")
            return
    print("Record not found.")


def delete(path: str, chunk_id: Optional[int], all_for_path: bool = False):
    store = load_default_store()
    if not store.is_ready():
        print("Vector store not ready. Nothing to delete.")
        return
    before = len(store.records)
    if all_for_path:
        store.records = [r for r in store.records if r.path != path]
        removed = before - len(store.records)
    elif chunk_id is not None:
        store.records = [r for r in store.records if not (r.path == path and r.chunk_id == chunk_id)]
        removed = before - len(store.records)
    else:
        print("Specify a chunk id or --all for path.")
        return
    if removed == 0:
        print("No matching records removed.")
        return
    store.save()
    print(f"Removed {removed} record(s). Updated index.jsonl and meta.json.")


def purge():
    root = os.path.join("data", "vector_store")
    if not os.path.exists(root):
        print("Vector store directory does not exist.")
        return
    print(f"About to delete all contents under {root}.")
    ans = input("Type 'yes' to confirm: ").strip().lower()
    if ans != "yes":
        print("Aborted.")
        return
    # Remove files in root (not the directory itself)
    removed = 0
    for name in os.listdir(root):
        p = os.path.join(root, name)
        try:
            if os.path.isfile(p):
                os.remove(p)
                removed += 1
        except Exception as e:
            print(f"[warn] Failed to remove {p}: {e}")
    print(f"Purged {removed} file(s). Run 'ingest' to rebuild.")


def ingest():
    from src.ingest import ingest as do_ingest

    do_ingest()


def export_index(dest_path: str):
    root = os.path.join("data", "vector_store")
    src_index = os.path.join(root, "index.jsonl")
    if not os.path.exists(src_index):
        print("No index.jsonl to export. Run 'ingest' first.")
        return
    os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
    with open(src_index, "r", encoding="utf-8") as s, open(dest_path, "w", encoding="utf-8") as d:
        for line in s:
            d.write(line)
    print(f"Exported index to {dest_path}")


def help_text():
    print(
        """
Commands:
  status                          Show store readiness and basic stats
  docs [--limit N]               List documents and their chunk counts
  chunks <path> [--limit N]      List chunks for a document path
  search <query> [--k K]         Search top-k similar chunks
  show <path> <chunk_id>         Print full text of a chunk
  delete <path> <chunk_id>       Delete a specific chunk
  delete <path> --all            Delete all chunks for a document path
  purge                          Remove all vector store files
  ingest                         Rebuild the vector store from input/
  export <dest.jsonl>            Copy index.jsonl to a target path
  help                           Show this help
  exit | quit                    Exit the manager
        """.strip()
    )


def repl():
    print("Interactive Vector Store Manager. Type 'help' for commands.")
    while True:
        try:
            line = input(PROMPT)
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line.strip():
            continue
        try:
            args = shlex.split(line)
        except ValueError as e:
            print(f"Parse error: {e}")
            continue
        cmd = args[0].lower()
        rest = args[1:]
        if cmd in ("exit", "quit"):  # exit
            break
        if cmd == "help":
            help_text()
        elif cmd == "status":
            print_status()
        elif cmd == "docs":
            limit = None
            if rest and rest[0] == "--limit" and len(rest) >= 2:
                try:
                    limit = int(rest[1])
                except ValueError:
                    print("--limit expects an integer")
                    continue
            list_docs(limit)
        elif cmd == "chunks":
            if not rest:
                print("Usage: chunks <path> [--limit N]")
                continue
            path = rest[0]
            limit = None
            if len(rest) >= 3 and rest[1] == "--limit":
                try:
                    limit = int(rest[2])
                except ValueError:
                    print("--limit expects an integer")
                    continue
            list_chunks(path, limit)
        elif cmd == "search":
            if not rest:
                print("Usage: search <query> [--k K]")
                continue
            # Collect until flag or end as query string
            k = 5
            if "--k" in rest:
                i = rest.index("--k")
                query = " ".join(rest[:i])
                try:
                    k = int(rest[i + 1])
                except Exception:
                    print("--k expects an integer")
                    continue
            else:
                query = " ".join(rest)
            search(query, k)
        elif cmd == "show":
            if len(rest) < 2:
                print("Usage: show <path> <chunk_id>")
                continue
            path = rest[0]
            try:
                cid = int(rest[1])
            except ValueError:
                print("chunk_id must be an integer")
                continue
            show(path, cid)
        elif cmd == "delete":
            if len(rest) < 2:
                print("Usage: delete <path> <chunk_id> | delete <path> --all")
                continue
            path = rest[0]
            if rest[1] == "--all":
                delete(path, None, all_for_path=True)
            else:
                try:
                    cid = int(rest[1])
                except ValueError:
                    print("chunk_id must be an integer")
                    continue
                delete(path, cid)
        elif cmd == "purge":
            purge()
        elif cmd == "ingest":
            ingest()
        elif cmd == "export":
            if len(rest) != 1:
                print("Usage: export <dest.jsonl>")
                continue
            export_index(rest[0])
        else:
            print(f"Unknown command: {cmd}. Type 'help'.")


def main():
    parser = argparse.ArgumentParser(description="Interactive vector store manager")
    parser.add_argument("--cmd", nargs=argparse.REMAINDER, help="Optional one-shot command to run")
    args = parser.parse_args()
    if args.cmd:
        # Run a single command then exit
        line = " ".join(args.cmd)
        print(f"+ {line}")
        try:
            # Minimal reuse of repl dispatch
            sys.stdin = open(os.devnull)  # avoid accidental blocking reads
        except Exception:
            pass
        # Execute via a tiny one-off repl loop
        try:
            # Simulate entering the command into the repl
            print_status if False else None  # keep linter happy if any
        finally:
            pass
        # Easiest path: just run repl once with the command by reusing dispatcher
        # but without customizing the internals; instead, interpret here:
        tokens = shlex.split(line)
        if not tokens:
            return
        cmd, rest = tokens[0], tokens[1:]
        if cmd == "status":
            print_status()
        elif cmd == "docs":
            limit = None
            if rest and rest[0] == "--limit" and len(rest) >= 2:
                limit = int(rest[1])
            list_docs(limit)
        elif cmd == "chunks":
            if not rest:
                print("Usage: chunks <path> [--limit N]")
                return
            limit = None
            if len(rest) >= 3 and rest[1] == "--limit":
                limit = int(rest[2])
            list_chunks(rest[0], limit)
        elif cmd == "search":
            k = 5
            if "--k" in rest:
                i = rest.index("--k")
                q = " ".join(rest[:i])
                k = int(rest[i + 1])
            else:
                q = " ".join(rest)
            search(q, k)
        elif cmd == "show":
            show(rest[0], int(rest[1]))
        elif cmd == "delete":
            if len(rest) >= 2 and rest[1] == "--all":
                delete(rest[0], None, all_for_path=True)
            else:
                delete(rest[0], int(rest[1]))
        elif cmd == "purge":
            purge()
        elif cmd == "ingest":
            ingest()
        elif cmd == "export":
            export_index(rest[0])
        else:
            print(f"Unknown command: {cmd}")
        return
    # Default: interactive repl
    repl()


if __name__ == "__main__":
    main()

