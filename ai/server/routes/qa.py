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
from ..utils import CamelModel, build_collection_id, to_qa_rag_context

router = APIRouter(prefix="/qa", tags=["QA"])
logger = logging.getLogger(__name__)


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

    qa_question_types = settings.qa.question_types[: settings.qa.qa_top_k]
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
            PreviousQA(type=item.type, question=item.question, answer=item.answer)
            for item in request.previous_qa
        ]
    )

    async def run_and_callback():
        qna_items: List[dict] = []
        try:
            async for event_type, q_type, payload in qa_service.stream_questions(qa_request):
                if event_type == "qa":
                    qna_items.append(
                        {
                            "type": q_type,
                            "question": payload.get("question"),
                            "answer": payload.get("answer"),
                        }
                    )
        except Exception as exc:  # pragma: no cover - 외부 모듈 예외
            logger.exception("QA 생성 실패: %s", exc)
        finally:
            await post_qna_callback(request, qna_items)

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
