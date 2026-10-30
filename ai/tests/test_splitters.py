from __future__ import annotations

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding

from rag.splitters import ChunkSettings, PageText, split_document
from rag.splitters.semantic import (
    breakpoints,
    cosine_distances,
    fit_sizes,
    group_by_breakpoints,
    join_wrapped_lines,
    split_sentences,
)


def test_recursive_split_records_page_range():
    pages = [PageText(page=0, text="가나다 " * 40), PageText(page=1, text="라마바 " * 40)]

    chunks = split_document(pages, ChunkSettings(strategy="recursive", chunk_tokens=30, chunk_overlap_tokens=0))

    assert chunks[0].page_start == 0
    assert chunks[-1].page_end == 1
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_join_wrapped_lines_only_on_paragraph_pages():
    paragraph = ["가" * 60 + " 이어지는", "문장의 끝입니다.", "짧은 줄"]
    slide = ["제목", "항목 하나", "항목 둘"]

    assert join_wrapped_lines(paragraph) == ["가" * 60 + " 이어지는 문장의 끝입니다.", "짧은 줄"]
    assert join_wrapped_lines(slide) == slide


def test_split_sentences_strips_bullets_and_splits_sentence_ends():
    sentences = split_sentences([PageText(page=3, text="* 첫 항목\n- 둘째 항목\n문장 하나. 문장 둘?")])

    assert [s.text for s in sentences] == ["첫 항목", "둘째 항목", "문장 하나.", "문장 둘?"]
    assert {s.page for s in sentences} == {3}


def test_breakpoints_cut_only_above_percentile():
    distances = [0.1, 0.1, 0.9, 0.1, 0.8]

    assert breakpoints(distances, 60) == [2, 4]
    assert group_by_breakpoints(6, [2]) == [[0, 1, 2], [3, 4, 5]]


def test_cosine_distances_of_identical_and_orthogonal_vectors():
    distances = cosine_distances([[1, 0], [1, 0], [0, 1]])

    assert distances[0] == pytest.approx(0.0)
    assert distances[1] == pytest.approx(1.0)


def test_fit_sizes_merges_short_and_splits_long_groups():
    tokens = [5, 5, 50, 50, 50, 3]
    groups = [[0], [1, 2], [3, 4], [5]]

    fitted = fit_sizes(groups, tokens, min_tokens=20, max_tokens=60)

    assert fitted == [[0, 1, 2], [3], [4, 5]]


def test_semantic_split_adds_previous_sentence_as_overlap():
    pages = [PageText(page=0, text="\n".join(f"문장 {i}번 내용입니다." for i in range(12)))]
    settings = ChunkSettings(
        strategy="semantic", semantic_percentile=50, semantic_overlap_sentences=1, semantic_min_tokens=1, semantic_max_tokens=500
    )

    chunks = split_document(pages, settings, DeterministicFakeEmbedding(size=16))

    assert len(chunks) > 1
    previous_last = chunks[0].text.split(". ")[-1]
    assert chunks[1].text.startswith(previous_last.rstrip("."))
