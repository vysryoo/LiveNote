"""
자료 추천 입력과 결과
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from pydantic import BaseModel

from core.schemas import PreviousSummary, RAGChunk, ResourceType


@dataclass(frozen=True)
class RecContext:
    """추천 요청 하나의 입력. 모든 공급자가 같은 값을 받는다."""

    summary: str
    previous_summaries: List[PreviousSummary] = field(default_factory=list)
    rag_chunks: List[RAGChunk] = field(default_factory=list)
    # 자료 종류별로 이미 보여 준 자료 (논문 ID, 위키·영상 제목, 블로그 URL)
    excludes: Dict[ResourceType, List[str]] = field(default_factory=dict)

    def excluded(self, resource_type: ResourceType) -> List[str]:
        """자료 종류의 제외 목록을 돌려준다.

        Args:
            resource_type: 자료 종류
        Returns:
            제외 목록. 없으면 빈 목록
        """
        return self.excludes.get(resource_type, [])


@dataclass(frozen=True)
class Score:
    """후보 하나의 관련도 점수와 이유."""

    score: float
    reason: str


class LLMScore(BaseModel):
    """LLM 검증 응답 형식."""

    score: float
    reason: str


@dataclass(frozen=True)
class Recommendation:
    """추천 결과. 필드는 백엔드 콜백의 resources 항목과 같다."""

    type: ResourceType
    title: str
    url: str
    description: str
    score: float
    reason: str
    detail: Dict[str, Any]

    def to_resource(self) -> Dict[str, Any]:
        """콜백 payload의 resources 항목으로 바꾼다.

        Returns:
            {"type", "title", "url", "description", "score", "reason", "detail"}
        """
        return {
            "type": self.type.value,
            "title": self.title,
            "url": self.url,
            "description": self.description,
            "score": self.score,
            "reason": self.reason,
            "detail": self.detail,
        }


def one_line(text: str) -> str:
    """줄바꿈을 공백으로 바꾼다. 카드 한 줄 표시용.

    Args:
        text: 원문
    Returns:
        줄바꿈 없는 텍스트
    """
    return text.replace("\n", " ").replace("\r", " ")
