"""
QA 생성 API (SSE 스트리밍)
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncIterator, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import Field

from core.config import Settings
from core.schemas import QnAType
from core.timing import RequestTimer
from qa.models import PreviousQA, QARequest

from ..dependencies import Services, get_app_settings, get_services
from ..utils import CamelModel, NonBlankStr, build_collection_id

router = APIRouter(prefix="/qa", tags=["QA"])
logger = logging.getLogger(__name__)

class PreviousQAItem(CamelModel):
    """이전 QA 항목 (API 입력용)"""
    type: str = Field(..., description="질문 유형 (CONCEPT 등 QnAType 값 또는 개념/응용/비교/심화)")
    question: str = Field(..., description="질문 내용")
    answer: str = Field(..., description="답변 내용")


class QAGenerateRequest(CamelModel):
    """QA 생성 입력"""

    lecture_id: int = Field(..., ge=1, description="강의 ID")
    summary_id: Optional[int] = Field(default=None, description="요약 ID")
    section_index: int = Field(..., ge=0, description="섹션 인덱스(0-base)")
    section_summary: NonBlankStr = Field(..., min_length=10, description="섹션 요약")
    subject: Optional[str] = Field(default=None, description="선택 과목 정보")
    question_types: Optional[List[QnAType]] = Field(
        default=None,
        description="생성할 질문 유형 (미지정 시 설정값 사용)"
    )
    previous_qa: Optional[List[PreviousQAItem]] = Field(
        default_factory=list,
        description="중복 방지를 위한 이전 QA 목록"
    )


@router.post("/generate")
async def generate_qa(
    request: QAGenerateRequest,
    services: Services = Depends(get_services),
    settings: Settings = Depends(get_app_settings),
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
    timer = RequestTimer("qa", lecture_id=request.lecture_id, section_index=request.section_index)
    timer.mark("received")
    collection_id = build_collection_id(settings.rag.collection_prefix, str(request.lecture_id))

    def _retrieve():
        return services.rag.retrieve_context(
            collection_id=collection_id,
            query=request.section_summary,
            section_index=request.section_index,
            pdf_top_k=settings.rag.qa_retrieve_top_k,
            summary_top_k=settings.rag.summary_retrieve_top_k,
            recent_window=settings.rag.recent_summary_window,
        )

    try:
        rag_chunks = await asyncio.to_thread(_retrieve)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"RAG 검색 실패: {exc}"
        ) from exc
    timer.mark("retrieved", chunks=len(rag_chunks))

    requested_types = request.question_types if request.question_types is not None else settings.qa.question_types
    question_types: List[QnAType] = list(requested_types)[: settings.qa.max_question_types]
    if not question_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="생성할 질문 유형이 설정되지 않았습니다."
        )

    qa_request = QARequest(
        section_summary=request.section_summary,
        question_types=question_types,
        subject=request.subject,
        language=settings.qa.language,
        rag_chunks=rag_chunks,
        previous_qa=[PreviousQA(type=item.type, question=item.question, answer=item.answer) for item in request.previous_qa],
    )

    async def events() -> AsyncIterator[str]:
        async for event in services.qa.stream_questions(qa_request):
            item = event.data["item"]
            if event.name == "start":
                timer.mark("item_start", item=item, type=event.data["type"])
            elif event.name == "question":
                timer.mark("item_question", item=item)
            elif event.name == "answer":
                timer.mark_once("item_first_answer", key=item, item=item)
            elif event.name == "done":
                timer.mark("item_done", item=item, answer_chars=len(event.data["answer"]))
            elif event.name == "error":
                timer.mark("item_error", item=item)
                logger.warning("QA 생성 실패: item=%s error=%s", item, event.data["message"])
            yield _sse(event.name, event.data)
        timer.mark("completed")

    return StreamingResponse(events(), media_type="text/event-stream")


def _sse(event: str, data: dict) -> str:
    """SSE 이벤트 한 개를 문자열로 만든다."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
