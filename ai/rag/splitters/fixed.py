"""글자 수 기준 고정 길이 분할."""
from __future__ import annotations

from typing import List

from .base import Chunk, ChunkSettings, PageText, normalize
from .recursive import join_pages, page_at


def split_fixed(pages: List[PageText], settings: ChunkSettings) -> List[Chunk]:
    """문서를 이어 붙인 뒤 앞에서부터 같은 글자 수마다 자른다. 문장·단어·쪽 경계를 보지 않고 겹침도 없다.

    Args:
        pages: 쪽 원문 목록
        settings: chunk_chars(조각 글자 수)
    Returns:
        조각 목록
    """
    text, starts, numbers = join_pages(pages)
    chunks: List[Chunk] = []
    for start in range(0, len(text), settings.chunk_chars):
        piece = text[start:start + settings.chunk_chars]
        content = normalize(piece)
        if content:
            chunks.append(Chunk(
                text=content,
                page_start=page_at(start, starts, numbers),
                page_end=page_at(start + len(piece) - 1, starts, numbers),
                index=len(chunks),
            ))
    return chunks
