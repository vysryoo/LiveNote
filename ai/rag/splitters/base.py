"""
분할 공용 타입과 함수
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.config import Settings

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

    strategy: str = "semantic"
    chunk_tokens: int = 300
    chunk_overlap_tokens: int = 50
    semantic_percentile: float = 95.0
    semantic_overlap_sentences: int = 1
    semantic_min_tokens: int = 40
    semantic_max_tokens: int = 200

    def __post_init__(self) -> None:
        if self.strategy not in STRATEGIES:
            raise ValueError(f"지원하지 않는 분할 방식: {self.strategy}")

    @classmethod
    def from_settings(cls, settings: "Settings") -> "ChunkSettings":
        """서버 설정(RAG_CHUNK_*, RAG_SEMANTIC_*)으로 기본값을 덮어쓴 분할 설정을 만든다.

        Args:
            settings: 서버 설정. 값이 None인 항목은 기본값 사용
        Returns:
            분할 설정
        Raises:
            ValueError: 지원하지 않는 분할 방식인 경우
        """
        values = {
            "strategy": settings.rag_chunk_strategy,
            "chunk_tokens": settings.rag_chunk_tokens,
            "chunk_overlap_tokens": settings.rag_chunk_overlap_tokens,
            "semantic_percentile": settings.rag_semantic_percentile,
            "semantic_overlap_sentences": settings.rag_semantic_overlap_sentences,
            "semantic_min_tokens": settings.rag_semantic_min_tokens,
            "semantic_max_tokens": settings.rag_semantic_max_tokens,
        }
        return cls(**{name: value for name, value in values.items() if value is not None})


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
