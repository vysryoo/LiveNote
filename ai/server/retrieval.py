"""
QnA·추천 요청의 강의 문맥 검색
"""
from __future__ import annotations

import asyncio
from typing import List

from fastapi import HTTPException, status

from core.config import Settings
from core.schemas import RAGChunk

from .dependencies import Services


async def retrieve_section_context(
    services: Services,
    settings: Settings,
    collection_id: str,
    section_index: int,
    query: str,
    pdf_top_k: int,
) -> List[RAGChunk]:
    """현재 섹션 요약으로 강의 자료 조각과 이전 섹션 요약을 검색한다. Chroma 검색은 동기 호출이라 스레드에서 실행한다.

    Args:
        services: 서비스 묶음
        settings: 서버 설정 (이전 요약 개수, 제외할 직전 섹션 수)
        collection_id: 강의 컬렉션 ID
        section_index: 현재 섹션 번호 (0부터)
        query: 질의 (현재 섹션 요약)
        pdf_top_k: 강의 자료 조각 개수
    Returns:
        강의 자료 조각 뒤에 이전 섹션 요약을 이은 목록
    Raises:
        HTTPException: 검색 실패(400). SSE 응답이나 백그라운드 작업을 시작하기 전에 일반 HTTP 오류로 응답하게 함
    """
    try:
        return await asyncio.to_thread(
            services.rag.retrieve_context,
            collection_id=collection_id,
            query=query,
            section_index=section_index,
            pdf_top_k=pdf_top_k,
            summary_top_k=settings.rag.summary_retrieve_top_k,
            recent_window=settings.rag.recent_summary_window,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"RAG 검색 실패: {exc}") from exc
