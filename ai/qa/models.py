"""
QnA 생성 입력과 진행 이벤트
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from core.schemas import QnAType, RAGChunk


class PreviousQA(BaseModel):
    """이미 만든 QnA. 같은 질문을 다시 만들지 않도록 프롬프트에 넣는다."""

    type: str = Field(..., description="질문 유형. QnAType 값(CONCEPT 등) 또는 한글 이름(개념 등)")
    question: str = Field(..., description="질문")
    answer: str = Field(..., description="답변")


class QARequest(BaseModel):
    """QnA 생성 요청."""

    section_summary: str = Field(..., min_length=10, description="현재 섹션 요약")
    question_types: List[QnAType] = Field(..., min_length=1, description="생성할 질문 유형. 유형마다 1개씩 생성")
    subject: Optional[str] = Field(default=None, description="과목")
    language: str = Field(default="ko", description="질문·답변 언어")
    rag_chunks: List[RAGChunk] = Field(default_factory=list, description="강의 자료 조각·이전 섹션 요약")
    previous_qa: List[PreviousQA] = Field(default_factory=list, description="이미 만든 QnA")


@dataclass(frozen=True)
class QAEvent:
    """생성 진행 이벤트. 이름과 데이터는 SSE 응답 이벤트와 같다.

    - start: {"item", "type"}
    - question: {"item", "text"} 질문 완성
    - answer: {"item", "text"} 답변 조각
    - done: {"item", "type", "question", "answer"}
    - error: {"item", "message"} 해당 항목 생성 실패. 이 항목의 done은 오지 않음

    item은 요청한 질문 유형 순서(0부터), type은 QnAType 값이다.
    """

    name: str
    data: Dict[str, Any]
