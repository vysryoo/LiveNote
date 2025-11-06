"""
QA 생성 API (SSE)
"""
from __future__ import annotations

import asyncio
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator

from cap1_QA_module.qakit.models import QARequest

from ..config import AppSettings
from ..dependencies import get_qa_service, get_rag_service, get_settings
from ..utils import build_collection_id, format_sse, to_qa_rag_context

router = APIRouter(prefix="/qa", tags=["QA"])


class QAGenerateRequest(BaseModel):
    """QA 생성 입력"""
    
    lecture_id: str = Field(..., min_length=1, description="강의 ID")
    section_id: int = Field(..., ge=1, description="섹션 ID")
    section_summary: str = Field(..., min_length=10, description="섹션 요약")
    subject: Optional[str] = Field(default=None, description="선택 과목 정보")

    @validator("lecture_id")
    def validate_lecture_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("lecture_id는 비어 있을 수 없습니다.")
        return value


@router.post("/generate", status_code=status.HTTP_200_OK)
async def generate_qa(
    request: QAGenerateRequest,
    rag_service=Depends(get_rag_service),
    qa_service=Depends(get_qa_service),
    settings: AppSettings = Depends(get_settings),
):
    """QA 생성 SSE 엔드포인트"""
    collection_id = build_collection_id(settings.rag.collection_prefix, request.lecture_id)
    
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
        lecture_id=request.lecture_id,
        section_id=request.section_id,
        section_summary=request.section_summary,
        subject=request.subject,
        language=settings.qa.language,
        question_types=qa_question_types,
        qa_count=len(qa_question_types),
        rag_context=to_qa_rag_context(rag_chunks)
    )
    
    async def event_stream():
        start = time.perf_counter()
        yielded = 0
        
        # RAG 컨텍스트 개요
        yield format_sse(
            {
                "event": "context_ready",
                "collection_id": collection_id,
                "chunk_count": len(qa_request.rag_context.chunks),
            },
            event="qa_context"
        )
        
        async for event_type, q_type, payload in qa_service.stream_questions(qa_request):
            if event_type == "qa":
                yielded += 1
                yield format_sse(
                    {
                        "type": q_type,
                        "qa": payload,
                        "index": yielded,
                    },
                    event="qa_partial"
                )
            else:
                yield format_sse(
                    {
                        "type": q_type,
                        "error": payload.get("error", "알 수 없는 오류가 발생했습니다."),
                    },
                    event="qa_error"
                )
        
        duration_ms = int((time.perf_counter() - start) * 1000)
        yield format_sse(
            {
                "total": yielded,
                "duration_ms": duration_ms,
            },
            event="qa_complete"
        )
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")
