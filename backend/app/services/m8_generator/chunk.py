"""Paragraph-aware chunking.

Chunks are about 800 tokens with 100 tokens of overlap, split on paragraph
boundaries and never mid-sentence. Overlap matters: a definition that straddles
a boundary would otherwise be unanswerable from either chunk, and the grounding
check would then correctly reject a question that was actually fair.

Token counting is approximate. ``tiktoken`` is not in the locked stack, and a
character heuristic is accurate enough for a size budget — the value is a
ceiling, not a contract.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: English averages close to four characters per token for prose of this kind.
CHARS_PER_TOKEN = 4

TARGET_TOKENS = 800
OVERLAP_TOKENS = 100

TARGET_CHARS = TARGET_TOKENS * CHARS_PER_TOKEN      # 3200
OVERLAP_CHARS = OVERLAP_TOKENS * CHARS_PER_TOKEN    # 400

#: A chunk below this is too thin to generate three sound questions from.
MIN_CHUNK_CHARS = 300

_SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class Chunk:
    """One window of text, with the page it started on."""

    index: int
    content: str
    page_no: int | None

    @property
    def char_count(self) -> int:
        return len(self.content)

    @property
    def approx_tokens(self) -> int:
        return len(self.content) // CHARS_PER_TOKEN


def estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN


def split_sentences(text: str) -> list[str]:
    """Split on sentence boundaries, keeping the terminator."""
    return [s.strip() for s in _SENTENCE_END_RE.split(text) if s.strip()]


def _tail_overlap(text: str, overlap_chars: int) -> str:
    """The trailing sentences of a chunk, up to the overlap budget.

    Whole sentences only, so the next chunk never opens mid-clause.
    """
    if overlap_chars <= 0 or not text:
        return ""

    sentences = split_sentences(text)
    picked: list[str] = []
    total = 0
    for sentence in reversed(sentences):
        if total + len(sentence) > overlap_chars and picked:
            break
        picked.insert(0, sentence)
        total += len(sentence) + 1
    return " ".join(picked)


def chunk_pages(
    pages: list[tuple[int, str]],
    *,
    target_chars: int = TARGET_CHARS,
    overlap_chars: int = OVERLAP_CHARS,
    min_chars: int = MIN_CHUNK_CHARS,
) -> list[Chunk]:
    """Chunk a document, preserving the page each chunk began on.

    Paragraphs are the unit of accumulation. A paragraph longer than the whole
    budget is split on sentence boundaries rather than being truncated.
    """
    chunks: list[Chunk] = []
    buffer = ""
    buffer_page: int | None = None

    def flush() -> None:
        nonlocal buffer, buffer_page
        text = buffer.strip()
        if text:
            chunks.append(Chunk(index=len(chunks), content=text, page_no=buffer_page))
        buffer = _tail_overlap(text, overlap_chars)
        # The overlap belongs to the page the next content starts on; it is
        # reassigned as soon as the next paragraph is appended.

    for page_no, page_text in pages:
        for paragraph in (p.strip() for p in page_text.split("\n\n")):
            if not paragraph:
                continue

            if len(paragraph) > target_chars:
                # Oversized paragraph: emit it in sentence-bounded pieces.
                for sentence in split_sentences(paragraph):
                    if len(buffer) + len(sentence) + 1 > target_chars and buffer.strip():
                        flush()
                    if buffer_page is None or not buffer.strip():
                        buffer_page = page_no
                    buffer = f"{buffer} {sentence}".strip() if buffer else sentence
                continue

            if len(buffer) + len(paragraph) + 2 > target_chars and buffer.strip():
                flush()
                buffer_page = page_no
            if buffer_page is None:
                buffer_page = page_no
            buffer = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph

    text = buffer.strip()
    if text:
        chunks.append(Chunk(index=len(chunks), content=text, page_no=buffer_page))

    # Fold a too-small trailing chunk back into its predecessor rather than
    # shipping a stub the model cannot write three questions from.
    if len(chunks) > 1 and chunks[-1].char_count < min_chars:
        last = chunks.pop()
        previous = chunks.pop()
        chunks.append(
            Chunk(
                index=previous.index,
                content=f"{previous.content}\n\n{last.content}",
                page_no=previous.page_no,
            )
        )

    return [Chunk(index=i, content=c.content, page_no=c.page_no) for i, c in enumerate(chunks)]
