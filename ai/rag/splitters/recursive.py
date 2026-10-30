"""토큰 수 기준 재귀 분할."""
from __future__ import annotations

import bisect
from typing import List, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter

from .base import TOKEN_ENCODING, Chunk, ChunkSettings, PageText, normalize

PAGE_SEPARATOR = "\n\n"


def join_pages(pages: List[PageText]) -> Tuple[str, List[int], List[int]]:
    """쪽 원문을 이어 붙이고 글자 위치 → 쪽 번호 대응표를 만든다.

    Args:
        pages: 쪽 원문 목록
    Returns:
        (이어 붙인 텍스트, 쪽별 시작 위치 목록, 쪽 번호 목록)
    """
    starts, numbers, parts = [], [], []
    offset = 0
    for page in pages:
        starts.append(offset)
        numbers.append(page.page)
        parts.append(page.text)
        offset += len(page.text) + len(PAGE_SEPARATOR)
    return PAGE_SEPARATOR.join(parts), starts, numbers


def page_at(position: int, starts: List[int], numbers: List[int]) -> int:
    """글자 위치가 속한 쪽 번호를 찾는다.

    Args:
        position: 이어 붙인 텍스트 안의 글자 위치
        starts: 쪽별 시작 위치 (오름차순)
        numbers: 쪽 번호
    Returns:
        쪽 번호
    """
    return numbers[max(bisect.bisect_right(starts, position) - 1, 0)]


def split_recursive(pages: List[PageText], settings: ChunkSettings) -> List[Chunk]:
    """문단 → 줄 → 문장 → 공백 순으로 구분자를 바꿔 가며 목표 토큰 수 이하로 자른다. 쪽 경계는 무시한다.

    Args:
        pages: 쪽 원문 목록
        settings: chunk_tokens(조각 크기), chunk_overlap_tokens(겹침)
    Returns:
        조각 목록
    """
    text, starts, numbers = join_pages(pages)
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name=TOKEN_ENCODING,
        chunk_size=settings.chunk_tokens,
        chunk_overlap=settings.chunk_overlap_tokens,
        separators=["\n\n", "\n", ". ", " ", ""],
        add_start_index=True,
    )
    chunks: List[Chunk] = []
    for document in splitter.create_documents([text]):
        start = document.metadata["start_index"]
        end = start + len(document.page_content) - 1
        content = normalize(document.page_content)
        if content:
            chunks.append(Chunk(
                text=content,
                page_start=page_at(start, starts, numbers),
                page_end=page_at(end, starts, numbers),
                index=len(chunks),
            ))
    return chunks
