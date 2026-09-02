"""Text cleaning before chunking.

Training handouts carry a lot of text that is not content: running headers,
page footers, slide numbers, stray bullet glyphs. Left in, they pollute chunks
and the model writes questions about the footer. Removing them is cheap and
makes a visible difference to item quality.
"""

from __future__ import annotations

import re
from collections import Counter

from app.services.m8_generator.extract import Extraction, Page

#: A line shorter than this carries no content worth asking about.
MIN_LINE_CHARS = 3

#: A line repeated on at least this share of pages is chrome, not content.
REPEAT_THRESHOLD = 0.5

#: Only consider the first and last few lines of a page as header/footer
#: candidates, so a genuinely repeated definition mid-page is not stripped.
EDGE_LINES = 3

#: A running header or footer is short. A long line repeated across pages is
#: body text — a boilerplate definition, a repeated worked example — and
#: stripping it would silently delete the content questions are written from.
MAX_CHROME_CHARS = 120

_WHITESPACE_RE = re.compile(r"[ \t ]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
_PAGE_NUMBER_RE = re.compile(r"^\s*(?:page\s*)?[-–—]?\s*\d{1,4}\s*(?:of\s*\d{1,4})?\s*[-–—]?\s*$", re.I)
_BULLET_RE = re.compile(r"^\s*[•▪◦‣·*]\s*")


def find_repeated_lines(pages: list[Page]) -> set[str]:
    """Lines appearing at the edge of many pages: headers and footers."""
    if len(pages) < 3:
        return set()

    counter: Counter[str] = Counter()
    for page in pages:
        lines = [ln.strip() for ln in page.text.splitlines() if ln.strip()]
        edges = lines[:EDGE_LINES] + lines[-EDGE_LINES:]
        for line in set(edges):
            if len(line) <= MAX_CHROME_CHARS:
                counter[line] += 1

    threshold = max(2, int(len(pages) * REPEAT_THRESHOLD))
    return {line for line, count in counter.items() if count >= threshold}


def clean_line(line: str) -> str:
    line = _BULLET_RE.sub("", line)
    line = _WHITESPACE_RE.sub(" ", line)
    return line.strip()


def clean_page(text: str, repeated: set[str]) -> str:
    """Drop chrome and normalise whitespace on one page."""
    kept: list[str] = []
    for raw in text.splitlines():
        line = clean_line(raw)
        if not line:
            kept.append("")
            continue
        if line in repeated:
            continue
        if _PAGE_NUMBER_RE.match(line):
            continue
        if len(line) < MIN_LINE_CHARS:
            continue
        kept.append(line)

    joined = "\n".join(kept)
    return _MULTI_NEWLINE_RE.sub("\n\n", joined).strip()


def clean_extraction(extraction: Extraction) -> Extraction:
    """Clean every page, dropping any that end up empty."""
    repeated = find_repeated_lines(extraction.pages)

    cleaned: list[Page] = []
    for page in extraction.pages:
        text = clean_page(page.text, repeated)
        if text:
            cleaned.append(Page(page_no=page.page_no, text=text))

    return Extraction(
        pages=cleaned,
        # Report the source document's page count, not the count after empty
        # pages were dropped — the trainer is looking at the original file.
        page_count=extraction.page_count,
        char_count=sum(len(p.text) for p in cleaned),
    )
