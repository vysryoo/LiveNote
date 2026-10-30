"""
강의 자료 분할

PDF 쪽 텍스트를 검색 단위 조각으로 나눈다. 분할 방식은 세 가지다.

- page: 쪽 하나를 조각 하나로 (기존 방식)
- recursive: 문서를 이어 붙인 뒤 토큰 수 기준으로 자르고 이웃 조각과 겹침
- semantic: 이웃 문장 묶음의 임베딩 거리가 크게 벌어지는 곳(주제 전환)에서 자르고 크기 보정·문장 겹침
"""
from __future__ import annotations

from typing import List

from .base import STRATEGIES, Chunk, ChunkSettings, PageText, count_tokens, normalize
from .page import split_by_page
from .recursive import split_recursive
from .semantic import split_semantic

__all__ = ["STRATEGIES", "Chunk", "ChunkSettings", "PageText", "count_tokens", "normalize", "split_document"]


def split_document(pages: List[PageText], settings: ChunkSettings, embeddings=None) -> List[Chunk]:
    """쪽 목록을 설정한 방식으로 조각낸다.

    Args:
        pages: 쪽 원문 목록 (쪽 순서)
        settings: 분할 설정
        embeddings: semantic 방식에 쓰는 LangChain Embeddings. 다른 방식이면 None 허용
    Returns:
        조각 목록 (index는 0부터 순서대로)
    Raises:
        ValueError: semantic 방식인데 embeddings가 없는 경우
    """
    if settings.strategy == "page":
        return split_by_page(pages)
    if settings.strategy == "recursive":
        return split_recursive(pages, settings)
    if embeddings is None:
        raise ValueError("semantic 분할에는 embeddings가 필요함")
    return split_semantic(pages, settings, embeddings)
