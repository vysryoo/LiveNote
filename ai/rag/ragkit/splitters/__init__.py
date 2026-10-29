"""
강의 자료 분할

PDF 쪽 텍스트를 검색 단위 조각으로 나눈다. 분할 방식은 세 가지다.

- page: 쪽 하나를 조각 하나로 (기존 방식)
- recursive: 문서를 이어 붙인 뒤 토큰 수 기준으로 자르고 이웃 조각과 겹침
- semantic: 이웃 문장 묶음의 임베딩 거리가 크게 벌어지는 곳(주제 전환)에서 자르고 크기 보정·문장 겹침
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import List

TOKEN_ENCODING = "cl100k_base"
STRATEGIES = ("page", "recursive", "semantic")


@dataclass(frozen=True)
class PageText:
    """PDF 한 쪽의 원문 텍스트. 줄바꿈을 유지한다."""

    page: int
    text: str


@dataclass(frozen=True)
class Chunk:
    """저장할 조각."""

    text: str
    page_start: int
    page_end: int
    index: int


@dataclass(frozen=True)
class ChunkSettings:
    """분할 방식과 방식별 기준값."""

    strategy: str = "page"
    chunk_tokens: int = 300
    chunk_overlap_tokens: int = 50
    semantic_percentile: float = 95.0
    semantic_overlap_sentences: int = 1
    semantic_min_tokens: int = 40
    semantic_max_tokens: int = 400

    @classmethod
    def from_env(cls) -> "ChunkSettings":
        """환경변수(RAG_CHUNK_*, RAG_SEMANTIC_*)로 기본값을 덮어쓴 설정을 만든다.

        Returns:
            분할 설정
        Raises:
            ValueError: 지원하지 않는 분할 방식인 경우
        """
        defaults = cls()
        settings = cls(
            strategy=os.getenv("RAG_CHUNK_STRATEGY", defaults.strategy),
            chunk_tokens=int(os.getenv("RAG_CHUNK_TOKENS", defaults.chunk_tokens)),
            chunk_overlap_tokens=int(os.getenv("RAG_CHUNK_OVERLAP_TOKENS", defaults.chunk_overlap_tokens)),
            semantic_percentile=float(os.getenv("RAG_SEMANTIC_PERCENTILE", defaults.semantic_percentile)),
            semantic_overlap_sentences=int(os.getenv("RAG_SEMANTIC_OVERLAP_SENTENCES", defaults.semantic_overlap_sentences)),
            semantic_min_tokens=int(os.getenv("RAG_SEMANTIC_MIN_TOKENS", defaults.semantic_min_tokens)),
            semantic_max_tokens=int(os.getenv("RAG_SEMANTIC_MAX_TOKENS", defaults.semantic_max_tokens)),
        )
        if settings.strategy not in STRATEGIES:
            raise ValueError(f"지원하지 않는 분할 방식: {settings.strategy}")
        return settings


@lru_cache(maxsize=1)
def _encoding():
    import tiktoken

    return tiktoken.get_encoding(TOKEN_ENCODING)


def count_tokens(text: str) -> int:
    """임베딩 모델과 같은 인코딩으로 토큰 수를 센다.

    Args:
        text: 텍스트
    Returns:
        토큰 수
    """
    return len(_encoding().encode(text))


def normalize(text: str) -> str:
    """연속 공백과 줄바꿈을 공백 하나로 바꾼다. 저장 텍스트에 적용한다.

    Args:
        text: 원문
    Returns:
        정리한 텍스트
    """
    return re.sub(r"\s+", " ", text).strip()


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
    from .page import split_by_page
    from .recursive import split_recursive
    from .semantic import split_semantic

    if settings.strategy == "page":
        return split_by_page(pages)
    if settings.strategy == "recursive":
        return split_recursive(pages, settings)
    if embeddings is None:
        raise ValueError("semantic 분할에는 embeddings가 필요함")
    return split_semantic(pages, settings, embeddings)
