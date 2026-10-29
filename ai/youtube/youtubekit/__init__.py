"""
YouTubeKit - 강의 섹션 맞춤 유튜브 추천 모듈

LiveNote 프로젝트를 위한 YouTube Data API 기반 동영상 추천 시스템
"""

from .service import YouTubeService
from .models import (
    YouTubeRequest,
    YouTubeResponse,
    YouTubeVideoInfo,
    PreviousSummary,
    RAGChunk,
)

__version__ = "0.1.0"

__all__ = [
    "YouTubeService",
    "YouTubeRequest",
    "YouTubeResponse",
    "YouTubeVideoInfo",
    "PreviousSummary",
    "RAGChunk",
]

