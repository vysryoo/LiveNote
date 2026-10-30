"""
QA 생성 API (SSE 스트리밍)
"""
from __future__ import annotations

import json
import logging
from typing import AsyncIterator, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import Field

from core.config import Settings
from core.schemas import QnAType
from core.timing import RequestTimer
from qa.models import PreviousQA, QAEvent, QARequest
from rag.service import build_collection_id

from ..dependencies import Services, get_app_settings, get_services
from ..models import CamelModel, NonBlankStr
from ..retrieval import retrieve_section_context

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
    rag_chunks = await retrieve_section_context(
        services, settings, collection_id, request.section_index, request.section_summary, settings.rag.qa_retrieve_top_k
    )
    timer.mark("retrieved", chunks=len(rag_chunks))

    qa_request = QARequest(
        section_summary=request.section_summary,
        question_types=_select_question_types(request.question_types, settings),
        subject=request.subject,
        language=settings.qa.language,
        rag_chunks=rag_chunks,
        previous_qa=[PreviousQA(type=item.type, question=item.question, answer=item.answer) for item in request.previous_qa],
    )

    return StreamingResponse(_stream_sse(services, qa_request, timer), media_type="text/event-stream")


def _select_question_types(requested: Optional[List[QnAType]], settings: Settings) -> List[QnAType]:
    """요청한 질문 유형(없으면 설정값)을 최대 개수까지 고른다. 남는 유형이 없으면 400으로 거절한다."""
    question_types = list(requested if requested is not None else settings.qa.question_types)[: settings.qa.max_question_types]
    if not question_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="생성할 질문 유형이 설정되지 않았습니다."
        )
    return question_types


async def _stream_sse(services: Services, qa_request: QARequest, timer: RequestTimer) -> AsyncIterator[str]:
    async for event in services.qa.stream_questions(qa_request):
        _mark_event(timer, event)
        yield _sse(event.name, event.data)
    timer.mark("completed")


def _mark_event(timer: RequestTimer, event: QAEvent) -> None:
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


def _sse(event: str, data: dict) -> str:
    """SSE 이벤트 한 개를 문자열로 만든다."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
