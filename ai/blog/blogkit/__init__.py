"""
GoogleKit - Google Custom Search 기반 검색 추천 모듈
"""
from .models import (
    RAGChunk,
    PreviousSummary,
    GoogleSearchResult,
    GoogleRequest,
    GoogleResponse,
)
from .service import GoogleService

__version__ = "0.1.0"

__all__ = [
    "RAGChunk",
    "PreviousSummary",
    "GoogleSearchResult",
    "GoogleRequest",
    "GoogleResponse",
    "GoogleService",
]
