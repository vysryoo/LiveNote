"""
FastAPI 애플리케이션 생성
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI

from core import tasks as background_tasks
from core.config import Settings, get_settings

from .dependencies import Services
from .routes import qa_router, rag_router, rec_router, summary_router
from .security import verify_internal_api_key

# 요약 생성(수 초)과 추천 콜백이 끝날 만큼의 시간
BACKGROUND_SHUTDOWN_TIMEOUT_SEC = 30.0


def build_services(settings: Settings) -> Services:
    """설정으로 실제 서비스들을 만든다.

    Args:
        settings: 서버 설정
    Returns:
        서비스 묶음
    """
    from qa.service import QAService
    from rag.service import RAGService
    from recommend.service import RecommendService
    from summary.service import SummaryService

    return Services(
        rag=RAGService(settings),
        qa=QAService(),
        rec=RecommendService(settings),
        summary=SummaryService(settings.summary),
    )


def create_app(settings: Optional[Settings] = None, services: Optional[Services] = None) -> FastAPI:
    """FastAPI 앱을 만든다.

    Args:
        settings: 서버 설정. None이면 환경변수와 ai/.env로 만든 설정
        services: 서비스 묶음. None이면 설정으로 만들고, 서버 종료 시 연결을 닫음
    Returns:
        FastAPI 앱
    """
    settings = settings or get_settings()
    owns_services = services is None
    services = services or build_services(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # 키가 빠진 채 요청을 받기 시작하지 않도록 서버 시작 단계에서 멈춤
        settings.check_required()
        try:
            yield
        finally:
            # 요청에 먼저 응답한 요약·추천 콜백이 끝나도록 잠시 기다림
            await background_tasks.shutdown(timeout_sec=BACKGROUND_SHUTDOWN_TIMEOUT_SEC)
            if owns_services:
                await services.rec.close()

    app = FastAPI(
        title="LiveNote AI Gateway",
        version="1.0.0",
        description="LiveNote AI 서비스를 위한 통합 API Gateway",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.services = services

    # /health를 제외한 모든 API는 백엔드만 호출하도록 공유 키를 확인
    internal_only = [Depends(verify_internal_api_key)]
    app.include_router(rag_router, dependencies=internal_only)
    app.include_router(qa_router, dependencies=internal_only)
    app.include_router(rec_router, dependencies=internal_only)
    app.include_router(summary_router, dependencies=internal_only)

    @app.get("/health")
    async def health_check():
        """간단한 헬스 체크"""
        return {"status": "ok"}

    return app
