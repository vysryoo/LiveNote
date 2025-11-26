"""
QA 생성 API (Callback)
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional, List

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field, HttpUrl, validator

from cap1_QA_module.qakit.models import QARequest, PreviousQA

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
    callback_url: HttpUrl = Field(..., description="콜백 URL")
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


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_qa(
    request: QAGenerateRequest,
    rag_service=Depends(get_rag_service),
    qa_service=Depends(get_qa_service),
    settings: AppSettings = Depends(get_settings),
):
    """QA 생성 콜백 엔드포인트"""
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

    async def run_and_callback():
        try:
            async for event_type, q_type, payload in qa_service.stream_questions(qa_request):
                if event_type == "qa":
                    enum_type = _to_qna_enum(payload.get("type") or q_type)
                    if enum_type is None:
                        logger.warning("알 수 없는 QA 유형 무시: %s", q_type)
                        continue
                    item = {
                        "type": enum_type.value,
                        "question": payload.get("question"),
                        "answer": payload.get("answer"),
                    }
                    # 먼저 도착한 QA부터 즉시 콜백 전송
                    await post_qna_callback(request, [item])
        except Exception as exc:  # pragma: no cover - 외부 모듈 예외
            logger.exception("QA 생성 실패: %s", exc)

    asyncio.create_task(run_and_callback())
    return {"status": "accepted", "collection_id": collection_id}


async def post_qna_callback(request: QAGenerateRequest, qna_items: List[dict]):
    """콜백 URL로 QA 결과 전송"""
    payload = {
        "lectureId": request.lecture_id,
        "summaryId": request.summary_id,
        "sectionIndex": request.section_index,
        "qnaList": qna_items,
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(str(request.callback_url), json=payload)
    except Exception as exc:  # pragma: no cover - 네트워크 예외
        logger.exception("QA 콜백 전송 실패: %s", exc)


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
