"""M8 · cleaning and chunking."""

from __future__ import annotations

from app.services.m8_generator import clean
from app.services.m8_generator.chunk import (
    OVERLAP_CHARS,
    TARGET_CHARS,
    Chunk,
    chunk_pages,
    split_sentences,
)
from app.services.m8_generator.extract import Extraction, Page

PARAGRAPH = (
    "The WHERE clause takes a condition and keeps only the rows for which that "
    "condition is true. Comparison operators are equals, not equals, greater "
    "than and less than. Conditions combine with AND, OR and NOT. "
)


def long_page(repeats: int) -> str:
    return "\n\n".join(PARAGRAPH for _ in range(repeats))


# ── sentence splitting ───────────────────────────────────────────────────────


def test_split_sentences_keeps_terminators() -> None:
    parts = split_sentences("One thing. Two things! Three things?")
    assert parts == ["One thing.", "Two things!", "Three things?"]


# ── chunk sizing ─────────────────────────────────────────────────────────────


def test_short_document_is_one_chunk() -> None:
    chunks = chunk_pages([(1, PARAGRAPH)])
    assert len(chunks) == 1
    assert chunks[0].page_no == 1


def test_long_document_splits_into_several_chunks() -> None:
    chunks = chunk_pages([(1, long_page(30))])
    assert len(chunks) > 1


def test_no_chunk_greatly_exceeds_the_target() -> None:
    """A chunk over budget risks blowing the per-minute token ceiling."""
    chunks = chunk_pages([(1, long_page(20))])
    for chunk in chunks:
        assert chunk.char_count <= TARGET_CHARS + OVERLAP_CHARS + len(PARAGRAPH)


def test_chunks_are_indexed_consecutively_from_zero() -> None:
    chunks = chunk_pages([(1, long_page(30))])
    assert [c.index for c in chunks] == list(range(len(chunks)))


# ── overlap ──────────────────────────────────────────────────────────────────


def test_consecutive_chunks_overlap() -> None:
    """Without overlap, a definition straddling a boundary is unanswerable."""
    chunks = chunk_pages([(1, long_page(16))])
    assert len(chunks) > 1
    first_sentences = set(split_sentences(chunks[0].content))
    second_sentences = set(split_sentences(chunks[1].content))
    assert first_sentences & second_sentences


def test_overlap_never_splits_a_sentence() -> None:
    chunks = chunk_pages([(1, long_page(16))])
    for chunk in chunks[1:]:
        opening = chunk.content.strip()
        # A chunk opening mid-clause would start lower-case.
        assert opening[0].isupper() or opening[0].isdigit()


# ── page numbers ─────────────────────────────────────────────────────────────


def test_page_numbers_are_preserved() -> None:
    """A trainer must be able to check an item against its source page."""
    chunks = chunk_pages([(1, PARAGRAPH), (2, PARAGRAPH), (3, PARAGRAPH)])
    assert all(c.page_no in (1, 2, 3) for c in chunks)


def test_first_chunk_reports_the_first_page() -> None:
    chunks = chunk_pages([(7, PARAGRAPH)])
    assert chunks[0].page_no == 7


# ── oversized paragraphs ─────────────────────────────────────────────────────


def test_a_paragraph_larger_than_the_budget_is_split_not_truncated() -> None:
    giant = " ".join(f"Sentence number {i} about survey data." for i in range(400))
    chunks = chunk_pages([(1, giant)])
    assert len(chunks) > 1
    recombined = " ".join(c.content for c in chunks)
    assert "Sentence number 399" in recombined


# ── trailing stub ────────────────────────────────────────────────────────────


def test_a_tiny_trailing_chunk_is_folded_into_its_predecessor() -> None:
    """A stub chunk cannot support three sound questions."""
    chunks = chunk_pages([(1, long_page(9)), (2, "A short closing note follows here.")])
    assert all(c.char_count >= 300 or len(chunks) == 1 for c in chunks)


def test_empty_input_produces_no_chunks() -> None:
    assert chunk_pages([]) == []


# ── cleaning ─────────────────────────────────────────────────────────────────


def test_repeated_headers_and_footers_are_dropped() -> None:
    """Otherwise the model writes questions about the footer."""
    pages = [
        Page(page_no=i, text=f"NSSTA TRAINING HANDOUT\n{PARAGRAPH}\nPage {i} of 4")
        for i in range(1, 5)
    ]
    cleaned = clean.clean_extraction(
        Extraction(pages=pages, page_count=4, char_count=sum(len(p.text) for p in pages))
    )
    body = "\n".join(p.text for p in cleaned.pages)
    assert "NSSTA TRAINING HANDOUT" not in body
    assert "WHERE clause" in body


def test_bare_page_numbers_are_dropped() -> None:
    pages = [Page(page_no=1, text=f"{PARAGRAPH}\n- 12 -")]
    cleaned = clean.clean_extraction(Extraction(pages=pages, page_count=1, char_count=0))
    assert "- 12 -" not in cleaned.pages[0].text


def test_bullet_glyphs_and_stray_whitespace_are_normalised() -> None:
    pages = [Page(page_no=1, text=f"•   {PARAGRAPH}")]
    cleaned = clean.clean_extraction(Extraction(pages=pages, page_count=1, char_count=0))
    text = cleaned.pages[0].text
    assert not text.startswith("•")
    assert "  " not in text


def test_page_count_reports_the_source_document_not_the_survivors() -> None:
    """The trainer is looking at the original file, not our cleaned view."""
    pages = [Page(page_no=1, text=PARAGRAPH), Page(page_no=2, text="  ")]
    cleaned = clean.clean_extraction(Extraction(pages=pages, page_count=2, char_count=0))
    assert cleaned.page_count == 2
    assert len(cleaned.pages) == 1
