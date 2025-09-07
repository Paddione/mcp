from html.parser import HTMLParser
from typing import Optional
import io
import os


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._texts = []
        self._in_ignored = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):  # ignore non-content
            self._in_ignored = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._in_ignored = False

    def handle_data(self, data):
        if not self._in_ignored:
            text = data.strip()
            if text:
                self._texts.append(text)

    def get_text(self) -> str:
        return "\n".join(self._texts)


def extract_text_from_html(path: str, encoding: Optional[str] = None) -> str:
    with open(path, "r", encoding=encoding or "utf-8", errors="ignore") as f:
        content = f.read()
    parser = _HTMLTextExtractor()
    parser.feed(content)
    return parser.get_text()


def extract_text_from_pdf(path: str) -> str:
    # Try pypdf first, then PyPDF2; otherwise, skip with a note.
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except Exception:
            return ""  # No PDF parser available; caller should warn/skip

    try:
        reader = PdfReader(path)
        texts = []
        for page in getattr(reader, "pages", []):
            try:
                text = page.extract_text() or ""
                if text:
                    texts.append(text)
            except Exception:
                # Best-effort per page
                continue
        return "\n".join(texts)
    except Exception:
        return ""

