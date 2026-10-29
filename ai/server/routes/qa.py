"""
QA 생성 API (SSE 스트리밍)
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncIterator, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import Field, validator

from QA_module.qakit.models import QARequest, PreviousQA

from ..config import AppSettings
from ..dependencies import get_qa_service, get_rag_service, get_settings
from ..models import QnAType
from ..utils import CamelModel, build_collection_id, to_qa_rag_context

router = APIRouter(prefix="/qa", tags=["QA"])
logger = logging.getLogger(__name__)

QNA_TYPE_TO_INTERNAL = {
    QnAType.CONCEPT: "개념",
    QnAType.APPLICATION: "응용",
    QnAType.ADVANCED: "심화",
    QnAType.COMPARISON: "비교",
}
INTERNAL_TO_QNA_TYPE = {v: k for k, v in QNA_TYPE_TO_INTERNAL.items()}


class PreviousQAItem(CamelModel):
    """이전 QA 항목 (API 입력용)"""
    type: str = Field(..., description="질문 유형 (개념/응용/비교/심화/실습)")
    question: str = Field(..., description="질문 내용")
    answer: str = Field(..., description="답변 내용")


class QAGenerateRequest(CamelModel):
    """QA 생성 입력"""

    lecture_id: int = Field(..., ge=1, description="강의 ID")
    summary_id: Optional[int] = Field(default=None, description="요약 ID")
    section_index: int = Field(..., ge=0, description="섹션 인덱스(0-base)")
    section_summary: str = Field(..., min_length=10, description="섹션 요약")
    subject: Optional[str] = Field(default=None, description="선택 과목 정보")
    question_types: Optional[List[QnAType]] = Field(
        default=None,
        description="생성할 질문 유형 (미지정 시 설정값 사용)"
    )
    previous_qa: Optional[List[PreviousQAItem]] = Field(
        default_factory=list,
        description="중복 방지를 위한 이전 QA 목록"
    )

    @validator("section_summary")
    def validate_section_summary(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("section_summary는 비어 있을 수 없습니다.")
        return value


@router.post("/generate")
async def generate_qa(
    request: QAGenerateRequest,
    rag_service=Depends(get_rag_service),
    qa_service=Depends(get_qa_service),
    settings: AppSettings = Depends(get_settings),
):
    """질문 유형별 QA를 생성하며 생성 과정을 SSE로 응답한다.

    요청 검증과 RAG 검색은 응답 시작 전에 수행하므로, 실패하면 일반 HTTP 오류로 응답한다.
    응답 이벤트 (data는 JSON, item은 질문 유형 순서):
    - start: {"item", "type"}
    - question: {"item", "text"} 질문 완성
    - answer: {"item", "text"} 답변 조각
    - done: {"item", "type", "question", "answer"}
    - error: {"item", "message"} 해당 항목 생성 실패
    """
    lecture_id_str = str(request.lecture_id)
    collection_id = build_collection_id(settings.rag.collection_prefix, lecture_id_str)
    section_id_for_provider = request.section_index + 1  # QA 모듈은 1-base

    def _retrieve():
        return rag_service.retrieve(
            collection_id=collection_id,
            query=request.section_summary,
            top_k=settings.rag.qa_retrieve_top_k
        )

    try:
        rag_chunks = await asyncio.to_thread(_retrieve)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"RAG 검색 실패: {exc}"
        ) from exc

    requested_types = list(request.question_types) if request.question_types is not None else list(settings.qa.question_types)
    qa_question_types_enum: List[QnAType] = requested_types[: settings.qa.qa_top_k]
    if not qa_question_types_enum:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="생성할 질문 유형이 설정되지 않았습니다."
        )

    qa_question_types = [_to_internal_qna_type(q_type) for q_type in qa_question_types_enum]
    if not qa_question_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="생성할 질문 유형이 설정되지 않았습니다."
        )

    qa_request = QARequest(
        lecture_id=lecture_id_str,
        section_id=section_id_for_provider,
        section_summary=request.section_summary,
        subject=request.subject,
        language=settings.qa.language,
        question_types=qa_question_types,
        qa_count=len(qa_question_types),
        rag_context=to_qa_rag_context(rag_chunks),
        previous_qa=[
            PreviousQA(type=_normalize_previous_type(item.type), question=item.question, answer=item.answer)
            for item in request.previous_qa
        ]
    )

    async def events() -> AsyncIterator[str]:
        async for event_type, q_type, payload in qa_service.stream_questions(qa_request):
            enum_type = _to_qna_enum(payload.get("type") or q_type)
            type_value = enum_type.value if enum_type else q_type
            item = payload.get("item")
            if event_type == "start":
                yield _sse("start", {"item": item, "type": type_value})
            elif event_type in ("question", "answer"):
                yield _sse(event_type, {"item": item, "text": payload.get("text", "")})
            elif event_type == "qa":
                yield _sse("done", {
                    "item": item,
                    "type": type_value,
                    "question": payload.get("question"),
                    "answer": payload.get("answer"),
                })
            elif event_type == "error":
                logger.warning("QA 생성 실패: type=%s error=%s", q_type, payload.get("error"))
                yield _sse("error", {"item": item, "message": payload.get("error")})

    return StreamingResponse(events(), media_type="text/event-stream")


def _sse(event: str, data: dict) -> str:
    """SSE 이벤트 한 개를 문자열로 만든다."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _to_internal_qna_type(q_type: QnAType | str) -> str:
    """Enum 값을 QA 모듈에서 사용하는 유형 문자열로 변환"""
    try:
        enum_type = q_type if isinstance(q_type, QnAType) else QnAType(q_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"지원하지 않는 질문 유형: {q_type}"
        ) from exc
    return QNA_TYPE_TO_INTERNAL[enum_type]


def _normalize_previous_type(value: str) -> str:
    """이전 QA 유형을 QA 모듈용 문자열로 정규화"""
    try:
        return _to_internal_qna_type(value)
    except HTTPException:
        return value


def _to_qna_enum(value: Optional[str]) -> Optional[QnAType]:
    """QA 모듈 응답을 Enum 값으로 역매핑"""
    if value is None:
        return None
    if value in INTERNAL_TO_QNA_TYPE:
        return INTERNAL_TO_QNA_TYPE[value]
    try:
        return QnAType(value)
    except ValueError:
        return None
