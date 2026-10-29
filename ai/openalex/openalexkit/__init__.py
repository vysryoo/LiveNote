"""
OpenAlexKit - 학술 논문 검색 및 추천 모듈

LiveNote 프로젝트를 위한 OpenAlex API 기반 논문 추천 시스템
"""

from .service import OpenAlexService
from .models import (
    OpenAlexRequest,
    OpenAlexResponse,
    PaperInfo,
    RAGChunk,
    PreviousSectionSummary,
)

__version__ = "0.1.0"

__all__ = [
    "OpenAlexService",
    "OpenAlexRequest",
    "OpenAlexResponse",
    "PaperInfo",
    "RAGChunk",
    "PreviousSectionSummary",
]
