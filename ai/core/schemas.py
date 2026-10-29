"""
모듈 공통 입력 모델

QA·추천 모듈이 함께 쓰는 RAG 검색 결과와 이전 섹션 요약 형식.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class RAGChunk(BaseModel):
    """RAG 검색 결과 조각."""

    text: str = Field(..., description="조각 텍스트")
    score: float = Field(default=0.0, description="유사도 점수")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="메타데이터")


class PreviousSummary(BaseModel):
    """이전 섹션 요약. 모듈 프롬프트에서 섹션 번호는 1부터 센다."""

    section_id: int = Field(..., ge=1, description="섹션 번호 (1부터)")
    summary: str = Field(..., min_length=1, description="섹션 요약")
    timestamp: Optional[int] = Field(default=None, description="타임스탬프 (ms)")
