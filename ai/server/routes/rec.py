"""
REC 통합 API (Callback)
"""
from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field, HttpUrl

from core.config import Settings
from core.schemas import PreviousSummary, ResourceType
from core.tasks import run_in_background
from core.timing import RequestTimer
from recommend.graph import run_recommendations
from recommend.models import RecContext

from ..callback import post_callback
from ..dependencies import Services, get_app_settings, get_services
from ..utils import CamelModel, NonBlankStr, build_collection_id

router = APIRouter(prefix="/rec", tags=["REC"])
logger = logging.getLogger(__name__)


class PreviousSummaryItem(CamelModel):
    """이전 섹션 요약 (API 입력용)"""

    section_index: int = Field(..., ge=0, description="섹션 ID")
    summary: str = Field(..., min_length=5, description="요약 내용")
    timestamp: Optional[int] = Field(default=None, description="타임스탬프(ms)")


class RECRequest(CamelModel):
    """REC 통합 요청"""

    lecture_id: int = Field(..., ge=1, description="강의 ID")
    summary_id: Optional[int] = Field(default=None, description="요약 ID")
    section_index: int = Field(..., ge=0, description="섹션 인덱스(0-base)")
    section_summary: NonBlankStr = Field(..., min_length=10, description="섹션 요약")
    callback_url: HttpUrl = Field(..., description="콜백 URL")
    previous_summaries: List[PreviousSummaryItem] = Field(default_factory=list, description="이전 요약")
    yt_exclude: List[str] = Field(default_factory=list, description="제외할 유튜브 제목")
    wiki_exclude: List[str] = Field(default_factory=list, description="제외할 위키 제목")
    paper_exclude: List[str] = Field(default_factory=list, description="제외할 논문 ID")
    google_exclude: List[str] = Field(default_factory=list, description="제외할 블로그 URL (필드 이름은 백엔드 호환용)")
    resource_types: Optional[List[ResourceType]] = Field(
        default=None,
        description="요청 리소스 유형 (미지정 시 모든 유형)"
    )


@router.post("/recommend", status_code=status.HTTP_202_ACCEPTED)
async def recommend_resources(
    request: RECRequest,
    services: Services = Depends(get_services),
    settings: Settings = Depends(get_app_settings),
):
    """자료 종류별 추천을 시작하고 바로 응답한다. 종류마다 끝나는 대로 콜백으로 결과를 보낸다."""
    timer = RequestTimer("rec", lecture_id=request.lecture_id, section_index=request.section_index)
    timer.mark("received")
    collection_id = build_collection_id(settings.rag.collection_prefix, str(request.lecture_id))

    def _retrieve():
        return services.rag.retrieve_context(
            collection_id=collection_id,
            query=request.section_summary,
            section_index=request.section_index,
            pdf_top_k=settings.rag.rec_retrieve_top_k,
            summary_top_k=settings.rag.summary_retrieve_top_k,
            recent_window=settings.rag.recent_summary_window,
        )

    try:
        rag_chunks = await asyncio.to_thread(_retrieve)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"RAG 검색 실패: {exc}",
        ) from exc
    timer.mark("retrieved", chunks=len(rag_chunks))

    selected_resource_types = _select_resource_types(request.resource_types)
    if not selected_resource_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="요청된 리소스 유형이 없습니다."
        )

    context = RecContext(
        summary=request.section_summary,
        # 추천 프롬프트는 섹션 번호를 1부터 표시
        previous_summaries=[
            PreviousSummary(section_id=ps.section_index + 1, summary=ps.summary, timestamp=ps.timestamp)
            for ps in request.previous_summaries
        ],
        rag_chunks=rag_chunks,
        excludes={
            ResourceType.PAPER: request.paper_exclude,
            ResourceType.WIKI: request.wiki_exclude,
            ResourceType.VIDEO: request.yt_exclude,
            ResourceType.BLOG: request.google_exclude,
        },
    )

    async def provider_task(res_type: ResourceType):
        try:
            resources = [r.to_resource() for r in await services.rec.recommend(res_type, context)]
            logger.info(
                "추천 결과: %s %d개 (%s)",
                res_type.value,
                len(resources),
                ", ".join(r["title"] for r in resources[:5]) or "none",
            )
            timer.mark("provider_done", resource_type=res_type.value, count=len(resources))
            await post_resources_callback(request, resources, settings)
            timer.mark("provider_callback_sent", resource_type=res_type.value)
        except Exception as exc:  # pragma: no cover - 외부 서비스 예외
            timer.mark("provider_failed", resource_type=res_type.value)
            logger.exception("추천 실패: %s %s", res_type.value, exc)
            await post_resources_callback(request, [], settings)

    # 자료 종류별 추천은 그래프가 동시에 실행하고, 각각 끝나는 대로 콜백을 보냄
    run_in_background(
        run_recommendations(selected_resource_types, provider_task),
        name=f"rec-{request.lecture_id}-{request.section_index}",
    )

    return {"status": "accepted", "collection_id": collection_id}


def _select_resource_types(resource_types: Optional[List[ResourceType]]) -> List[ResourceType]:
    """요청된 리소스 유형에서 중복을 뺀다. 지정하지 않았으면 모든 유형"""
    if resource_types is None:
        return list(ResourceType)
    return list(dict.fromkeys(resource_types))


async def post_resources_callback(request: RECRequest, resources: List[dict], settings: Settings) -> None:
    """자료 종류 하나의 추천 결과를 콜백으로 보낸다."""
    payload = {
        "lectureId": request.lecture_id,
        "summaryId": request.summary_id,
        "sectionIndex": request.section_index,
        "resources": resources,
    }
    await post_callback(str(request.callback_url), payload, settings)
