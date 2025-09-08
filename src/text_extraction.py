from html.parser import HTMLParser
from typing import Optional
import io
import os
import re


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


def extract_text_from_markdown(path: str, encoding: Optional[str] = None) -> str:
    """Best-effort Markdown to plain text extraction.

    Keeps visible text while stripping common Markdown syntax such as code fences,
    inline code markers, emphasis markers, and link targets. Headings are kept as text.
    """
    try:
        with open(path, "r", encoding=encoding or "utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return ""

    # Remove fenced code blocks ```...``` (including info string)
    content = re.sub(r"```[\s\S]*?```", "\n", content)

    # Remove inline code markers `code`
    content = content.replace("`", "")

    # Convert links/images: [text](url) and ![alt](url) -> text/alt
    content = re.sub(r"!\[([^\]]*)\]\([^\)]*\)", r"\1", content)  # images
    content = re.sub(r"\[([^\]]+)\]\([^\)]*\)", r"\1", content)    # links

    lines = []
    for raw in content.splitlines():
        line = raw.rstrip()
        # Strip leading heading markers and blockquotes
        line = re.sub(r"^\s{0,3}#{1,6}\s*", "", line)  # headings
        line = re.sub(r"^\s{0,3}>\s?", "", line)       # blockquote

        # Remove unordered list markers and ordered list indices
        line = re.sub(r"^\s*[-*+]\s+", "", line)
        line = re.sub(r"^\s*\d+\.[\)\s]+", "", line)

        # Drop table rule lines (---|:---:)
        if re.match(r"^\s*[:\-\|\s]+$", line):
            continue

        # Strip emphasis markers
        line = line.replace("**", "").replace("__", "")
        line = line.replace("*", "").replace("_", "")
        line = line.replace("~~", "")

        if line.strip():
            lines.append(line.strip())

    return "\n".join(lines)
