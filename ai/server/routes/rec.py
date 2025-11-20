"""
REC 통합 API (Callback)
"""
from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field, HttpUrl, validator

from cap1_openalex_module.openalexkit.models import (
    OpenAlexRequest,
    OpenAlexResponse,
    PreviousSectionSummary as OpenAlexPreviousSummary,
)
from cap1_wiki_module.wikikit.models import (
    PreviousSummary as WikiPreviousSummary,
    WikiRequest,
    WikiResponse,
)
from cap1_youtube_module.youtubekit.models import (
    PreviousSummary as YouTubePreviousSummary,
    YouTubeRequest,
    YouTubeResponse,
)
from cap1_google_module.googlekit.models import (
    PreviousSummary as GooglePreviousSummary,
    GoogleRequest,
    GoogleResponse,
)

from ..config import AppSettings
from ..dependencies import (
    get_openalex_service,
    get_rag_service,
    get_settings,
    get_wiki_service,
    get_youtube_service,
    get_google_service,
)
from ..utils import (
    CamelModel,
    build_collection_id,
    to_openalex_rag_chunks,
    to_wiki_rag_chunks,
    to_youtube_rag_chunks,
    to_google_rag_chunks,
)

router = APIRouter(prefix="/rec", tags=["REC"])
logger = logging.getLogger(__name__)


class PreviousSummary(CamelModel):
    """이전 섹션 요약 정보"""

    section_index: int = Field(..., ge=0, description="섹션 ID")
    summary: str = Field(..., min_length=5, description="요약 내용")
    timestamp: Optional[int] = Field(default=None, description="타임스탬프(ms)")


class RECRequest(CamelModel):
    """REC 통합 요청"""

    lecture_id: int = Field(..., ge=1, description="강의 ID")
    summary_id: Optional[int] = Field(default=None, description="요약 ID")
    section_index: int = Field(..., ge=0, description="섹션 인덱스(0-base)")
    section_summary: str = Field(..., min_length=10, description="섹션 요약")
    callback_url: HttpUrl = Field(..., description="콜백 URL")
    previous_summaries: List[PreviousSummary] = Field(default_factory=list, description="이전 요약")
    yt_exclude: List[str] = Field(default_factory=list, description="제외할 유튜브 제목")
    wiki_exclude: List[str] = Field(default_factory=list, description="제외할 위키 제목")
    paper_exclude: List[str] = Field(default_factory=list, description="제외할 논문 ID")
    google_exclude: List[str] = Field(default_factory=list, description="제외할 구글 URL")

    @validator("section_summary")
    def validate_section_summary(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("section_summary는 비어 있을 수 없습니다.")
        return value


@router.post("/recommend", status_code=status.HTTP_202_ACCEPTED)
async def recommend_resources(
    request: RECRequest,
    rag_service=Depends(get_rag_service),
    openalex_service=Depends(get_openalex_service),
    wiki_service=Depends(get_wiki_service),
    youtube_service=Depends(get_youtube_service),
    google_service=Depends(get_google_service),
    settings: AppSettings = Depends(get_settings),
):
    """논문/위키/유튜브/구글 추천 콜백 엔드포인트"""
    lecture_id_str = str(request.lecture_id)
    collection_id = build_collection_id(settings.rag.collection_prefix, lecture_id_str)
    section_id_for_provider = request.section_index + 1  # 외부 모듈은 1-base

    def _retrieve():
        return rag_service.retrieve(
            collection_id=collection_id,
            query=request.section_summary,
            top_k=settings.rag.rec_retrieve_top_k,
        )

    try:
        rag_chunks = await asyncio.to_thread(_retrieve)
    except Exception as exc:  # pragma: no cover - 파라미터 검증
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"RAG 검색 실패: {exc}",
        ) from exc

    openalex_prev = [
        OpenAlexPreviousSummary(
            section_id=ps.section_index + 1,
            summary=ps.summary,
            timestamp=ps.timestamp,
        )
        for ps in request.previous_summaries
    ]
    wiki_prev = [
        WikiPreviousSummary(
            section_id=ps.section_index + 1,
            summary=ps.summary,
            timestamp=ps.timestamp,
        )
        for ps in request.previous_summaries
    ]
    youtube_prev = [
        YouTubePreviousSummary(
            section_id=ps.section_index + 1,
            summary=ps.summary,
            timestamp=ps.timestamp,
        )
        for ps in request.previous_summaries
    ]
    google_prev = [
        GooglePreviousSummary(
            section_id=ps.section_index + 1,
            summary=ps.summary,
            timestamp=ps.timestamp,
        )
        for ps in request.previous_summaries
    ]

    openalex_request = OpenAlexRequest(
        lecture_id=lecture_id_str,
        section_id=section_id_for_provider,
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
        lecture_id=lecture_id_str,
        section_id=section_id_for_provider,
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
        lecture_id=lecture_id_str,
        section_id=section_id_for_provider,
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

    google_request = GoogleRequest(
        lecture_id=lecture_id_str,
        section_id=section_id_for_provider,
        lecture_summary=request.section_summary,
        language=settings.rec.google.language,
        top_k=settings.rec.google.top_k,
        verify_google=settings.rec.google.verify,
        previous_summaries=google_prev,
        rag_context=to_google_rag_chunks(rag_chunks),
        search_lang=settings.rec.google.search_lang,
        exclude_urls=request.google_exclude,
        min_score=settings.rec.google.min_score,
    )

    async def provider_task(source: str, coro):
        try:
            result = await coro
            await post_resources_callback(request, map_resources(source, result))
        except Exception as exc:  # pragma: no cover - 외부 서비스 예외
            logger.exception("REC provider %s 실패: %s", source, exc)
            await post_resources_callback(request, [])

    asyncio.create_task(
        provider_task("openalex", openalex_service.recommend_papers(openalex_request))
    )
    asyncio.create_task(
        provider_task("wiki", wiki_service.recommend_pages(wiki_request))
    )
    asyncio.create_task(
        provider_task("youtube", youtube_service.recommend_videos(youtube_request))
    )
    asyncio.create_task(
        provider_task("google", google_service.recommend_results(google_request))
    )

    return {"status": "accepted", "collection_id": collection_id}


def map_resources(source: str, result: List) -> List[dict]:
    """provider 응답을 콜백용 리소스 포맷으로 변환"""
    mapped = []
    if source == "openalex":
        for item in result:  # type: OpenAlexResponse
            mapped.append(
                {
                    "type": "paper",
                    "title": item.paper_info.title,
                    "url": item.paper_info.url,
                    "description": item.paper_info.abstract,
                    "score": item.score,
                    "reason": item.reason,
                    "detail": item.paper_info.model_dump(),
                }
            )
    elif source == "wiki":
        for item in result:  # type: WikiResponse
            mapped.append(
                {
                    "type": "wiki",
                    "title": item.page_info.title,
                    "url": item.page_info.url,
                    "description": item.page_info.extract,
                    "score": item.score,
                    "reason": item.reason,
                    "detail": item.page_info.model_dump(),
                }
            )
    elif source == "youtube":
        for item in result:  # type: YouTubeResponse
            mapped.append(
                {
                    "type": "video",
                    "title": item.video_info.title,
                    "url": item.video_info.url,
                    "description": item.video_info.extract,
                    "score": item.score,
                    "reason": item.reason,
                    "detail": item.video_info.model_dump(),
                }
            )
    elif source == "google":
        for item in result:  # type: GoogleResponse
            mapped.append(
                {
                    "type": "google",
                    "title": item.search_result.title,
                    "url": item.search_result.url,
                    "description": item.search_result.snippet,
                    "score": item.score,
                    "reason": item.reason,
                    "detail": item.search_result.model_dump(),
                }
            )
    return mapped


async def post_resources_callback(request: RECRequest, resources: List[dict]):
    """콜백 URL로 추천 자료 전송"""
    payload = {
        "lectureId": request.lecture_id,
        "summaryId": request.summary_id,
        "sectionIndex": request.section_index,
        "resources": resources,
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(str(request.callback_url), json=payload)
    except Exception as exc:  # pragma: no cover - 네트워크 예외
        logger.exception("콜백 전송 실패: %s", exc)
