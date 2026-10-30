"""
모듈 공통 모델

QA·추천 모듈과 서버가 함께 쓰는 유형 Enum, RAG 검색 결과, 이전 섹션 요약 형식.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class QnAType(str, Enum):
    """QnA 질문 유형."""

    CONCEPT = "CONCEPT"
    APPLICATION = "APPLICATION"
    ADVANCED = "ADVANCED"
    COMPARISON = "COMPARISON"


class ResourceType(str, Enum):
    """추천 자료 유형."""

    PAPER = "PAPER"  # OpenAlex
    WIKI = "WIKI"  # Wikipedia
    VIDEO = "VIDEO"  # YouTube
    BLOG = "BLOG"  # 네이버 블로그


class RAGChunk(BaseModel):
    """RAG 검색 결과 조각."""

    # 모듈 프롬프트에 조각을 통째로 넣는 곳이 있어 저장소 내부 ID는 직렬화에서 뺌
    id: Optional[str] = Field(default=None, exclude=True, description="저장소 조각 ID")
    text: str = Field(..., description="조각 텍스트")
    score: float = Field(default=0.0, description="유사도 점수")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="메타데이터")


class PreviousSummary(BaseModel):
    """이전 섹션 요약. 모듈 프롬프트에서 섹션 번호는 1부터 센다."""

    section_id: int = Field(..., ge=1, description="섹션 번호 (1부터)")
    summary: str = Field(..., min_length=1, description="섹션 요약")
    timestamp: Optional[int] = Field(default=None, description="타임스탬프 (ms)")
