"""쪽 단위 분할 (기존 방식)."""
from __future__ import annotations

from typing import List

from . import Chunk, PageText, normalize


def split_by_page(pages: List[PageText]) -> List[Chunk]:
    """쪽 하나를 조각 하나로 만든다. 빈 쪽은 건너뛴다.

    Args:
        pages: 쪽 원문 목록
    Returns:
        조각 목록
    """
    chunks: List[Chunk] = []
    for page in pages:
        text = normalize(page.text)
        if text:
            chunks.append(Chunk(text=text, page_start=page.page, page_end=page.page, index=len(chunks)))
    return chunks
