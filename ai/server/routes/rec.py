"""
REC 통합 API (SSE)
"""
from __future__ import annotations

import asyncio
import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator

from cap1_openalex_module.openalexkit.models import (
    OpenAlexRequest,
    PreviousSectionSummary as OpenAlexPreviousSummary,
)
from cap1_wiki_module.wikikit.models import (
    PreviousSummary as WikiPreviousSummary,
    WikiRequest,
)
from cap1_youtube_module.youtubekit.models import (
    PreviousSummary as YouTubePreviousSummary,
    YouTubeRequest,
)

from ..config import AppSettings
from ..dependencies import (
    get_openalex_service,
    get_rag_service,
    get_settings,
    get_wiki_service,
    get_youtube_service,
)
from ..utils import (
    build_collection_id,
    format_sse,
    to_openalex_rag_chunks,
    to_wiki_rag_chunks,
    to_youtube_rag_chunks,
)

router = APIRouter(prefix="/rec", tags=["REC"])


class PreviousSummary(BaseModel):
    """이전 섹션 요약 정보"""
    
    section_id: int = Field(..., ge=1, description="섹션 ID")
    summary: str = Field(..., min_length=5, description="요약 내용")
    timestamp: Optional[int] = Field(default=None, description="타임스탬프(ms)")


class RECRequest(BaseModel):
    """REC 통합 요청"""
    
    lecture_id: str = Field(..., min_length=1, description="강의 ID")
    section_id: int = Field(..., ge=1, description="섹션 ID")
    section_summary: str = Field(..., min_length=10, description="섹션 요약")
    previous_summaries: List[PreviousSummary] = Field(default_factory=list, description="이전 요약")
    yt_exclude: List[str] = Field(default_factory=list, description="제외할 유튜브 제목")
    wiki_exclude: List[str] = Field(default_factory=list, description="제외할 위키 제목")
    paper_exclude: List[str] = Field(default_factory=list, description="제외할 논문 ID")

    @validator("lecture_id")
    def validate_lecture_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("lecture_id는 비어 있을 수 없습니다.")
        return value


@router.post("/recommend", status_code=status.HTTP_200_OK)
async def recommend_resources(
    request: RECRequest,
    rag_service=Depends(get_rag_service),
    openalex_service=Depends(get_openalex_service),
    wiki_service=Depends(get_wiki_service),
    youtube_service=Depends(get_youtube_service),
    settings: AppSettings = Depends(get_settings),
):
    """논문/위키/유튜브 추천 SSE 엔드포인트"""
    collection_id = build_collection_id(settings.rag.collection_prefix, request.lecture_id)
    
    def _retrieve():
        return rag_service.retrieve(
            collection_id=collection_id,
            query=request.section_summary,
            top_k=settings.rag.rec_retrieve_top_k
        )
    
    try:
        rag_chunks = await asyncio.to_thread(_retrieve)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"RAG 검색 실패: {exc}"
        ) from exc
    
    # 이전 요약 변환
    openalex_prev = [
        OpenAlexPreviousSummary(
            section_id=ps.section_id,
            summary=ps.summary,
            timestamp=ps.timestamp
        )
        for ps in request.previous_summaries
    ]
    wiki_prev = [
        WikiPreviousSummary(
            section_id=ps.section_id,
            summary=ps.summary,
            timestamp=ps.timestamp
        )
        for ps in request.previous_summaries
    ]
    youtube_prev = [
        YouTubePreviousSummary(
            section_id=ps.section_id,
            summary=ps.summary,
            timestamp=ps.timestamp
        )
        for ps in request.previous_summaries
    ]
    
    openalex_request = OpenAlexRequest(
        lecture_id=request.lecture_id,
        section_id=request.section_id,
        section_summary=request.section_summary,
        language=settings.rec.openalex.language,
        top_k=settings.rec.openalex.top_k,
        verify_openalex=settings.rec.openalex.verify,
        previous_summaries=openalex_prev,
        rag_context=to_openalex_rag_chunks(rag_chunks),
        year_from=settings.rec.openalex.year_from,
        exclude_ids=request.paper_exclude,
        sort_by=settings.rec.openalex.sort_by,
        min_score=settings.rec.openalex.min_score,
    )
    
    wiki_request = WikiRequest(
        lecture_id=request.lecture_id,
        section_id=request.section_id,
        lecture_summary=request.section_summary,
        language=settings.rec.wiki.language,
        top_k=settings.rec.wiki.top_k,
        verify_wiki=settings.rec.wiki.verify,
        previous_summaries=wiki_prev,
        rag_context=to_wiki_rag_chunks(rag_chunks),
        wiki_lang=settings.rec.wiki.wiki_lang,
        fallback_to_ko=settings.rec.wiki.fallback_to_ko,
        exclude_titles=request.wiki_exclude,
        min_score=settings.rec.wiki.min_score,
    )
    
    youtube_request = YouTubeRequest(
        lecture_id=request.lecture_id,
        section_id=request.section_id,
        lecture_summary=request.section_summary,
        language=settings.rec.youtube.language,
        top_k=settings.rec.youtube.top_k,
        verify_yt=settings.rec.youtube.verify,
        previous_summaries=youtube_prev,
        rag_context=to_youtube_rag_chunks(rag_chunks),
        yt_lang=settings.rec.youtube.yt_lang,
        exclude_titles=request.yt_exclude,
        min_score=settings.rec.youtube.min_score,
    )
    
    async def event_stream():
        start = time.perf_counter()
        completed = 0
        
        yield format_sse(
            {
                "event": "context_ready",
                "collection_id": collection_id,
                "chunk_count": len(rag_chunks),
            },
            event="rec_context"
        )
        
        tasks = {
            asyncio.create_task(openalex_service.recommend_papers(openalex_request)): "openalex",
            asyncio.create_task(wiki_service.recommend_pages(wiki_request)): "wiki",
            asyncio.create_task(youtube_service.recommend_videos(youtube_request)): "youtube",
        }

        pending = set(tasks.keys())
        while pending:
            done, pending = await asyncio.wait(
                pending,
                return_when=asyncio.FIRST_COMPLETED,
            )
            for finished in done:
                source = tasks.get(finished, "unknown")
                try:
                    result = await finished
                except Exception as exc:
                    yield format_sse(
                        {
                            "source": source,
                            "error": str(exc),
                        },
                        event="rec_error"
                    )
                    continue

                completed += 1
                payload = [item.model_dump() for item in result]
                yield format_sse(
                    {
                        "source": source,
                        "count": len(payload),
                        "items": payload,
                    },
                    event="rec_partial"
                )
        
        duration_ms = int((time.perf_counter() - start) * 1000)
        yield format_sse(
            {
                "completed_sources": completed,
                "duration_ms": duration_ms,
            },
            event="rec_complete"
        )
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")
