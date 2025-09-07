from typing import List, Iterable


def _word_iter(text: str) -> Iterable[str]:
    word = []
    for ch in text:
        if ch.isalnum():
            word.append(ch.lower())
        else:
            if word:
                yield "".join(word)
                word = []
    if word:
        yield "".join(word)


def chunk_text(text: str, max_words: int = 300, overlap: int = 50) -> List[str]:
    if max_words <= 0:
        return [text]
    words = list(_word_iter(text))
    chunks: List[str] = []
    i = 0
    n = len(words)
    if n == 0:
        return []
    while i < n:
        end = min(i + max_words, n)
        chunk = " ".join(words[i:end])
        chunks.append(chunk)
        if end == n:
            break
        i = end - overlap if end - overlap > i else end
    return chunks

