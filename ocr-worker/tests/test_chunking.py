from worker.chunking import chunk_page_text


def _words(n: int, prefix: str = "w") -> str:
    return " ".join(f"{prefix}{i}" for i in range(n))


def test_short_page_is_a_single_chunk() -> None:
    text = _words(100)
    chunks = chunk_page_text(text)
    assert chunks == [text]


def test_exact_800_words_is_a_single_chunk() -> None:
    text = _words(800)
    chunks = chunk_page_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_overlap_second_chunk_starts_at_word_700() -> None:
    text = _words(1000)
    chunks = chunk_page_text(text)
    assert len(chunks) == 2
    assert chunks[0] == _words(800)
    assert chunks[1] == " ".join(f"w{i}" for i in range(700, 1000))
    # word 700 of the source text is the first word of chunk 2 (overlap = 100 words: 700-799)
    assert chunks[1].split()[0] == "w700"


def test_blank_page_yields_no_chunks() -> None:
    assert chunk_page_text("   \n\t  ") == []
    assert chunk_page_text("") == []


def test_separate_calls_never_merge_across_pages() -> None:
    page_one = chunk_page_text(_words(50, prefix="a"))
    page_two = chunk_page_text(_words(50, prefix="b"))
    assert len(page_one) == 1
    assert len(page_two) == 1
    assert "b0" not in page_one[0]
    assert "a0" not in page_two[0]
