"""
FastAPI 애플리케이션 생성
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI

from core import tasks as background_tasks
from core.config import Settings, get_settings

from .routes import qa_router, rag_router, rec_router, summary_router
from .security import verify_internal_api_key

# 요약 생성(수 초)과 추천 콜백이 끝날 만큼의 시간
BACKGROUND_SHUTDOWN_TIMEOUT_SEC = 30.0


def _ensure_service(service: Any, factory_path: str):
    """지연 로딩으로 서비스 인스턴스 확보"""
    if service is not None:
        return service
    
    module_name, attr = factory_path.rsplit(".", 1)
    module = __import__(module_name, fromlist=[attr])
    factory = getattr(module, attr)
    return factory()


def _create_rag_service(settings: Settings):
    from rag.ragkit.config import RAGConfig
    from rag.ragkit.service import RAGService

    return RAGService(RAGConfig(
        persist_dir=str(settings.rag_persist_dir),
        embedding_model=settings.rag_embedding_model,
        openai_api_key=settings.rag_openai_api_key or settings.openai_api_key,
    ))


def create_app(
    settings: Settings | None = None,
    *,
    rag_service=None,
    qa_service=None,
    openalex_service=None,
    wiki_service=None,
    youtube_service=None,
    google_service=None,
) -> FastAPI:
    """FastAPI 앱 생성"""
    base_settings = settings or get_settings()
    
    # 서비스 인스턴스를 한 번만 준비해 재사용
    _rag = rag_service if rag_service is not None else _create_rag_service(base_settings)
    _qa = _ensure_service(qa_service, "qa.qakit.service.QAService")
    _openalex = _ensure_service(openalex_service, "openalex.openalexkit.service.OpenAlexService")
    _wiki = _ensure_service(wiki_service, "wiki.wikikit.service.WikiService")
    _youtube = _ensure_service(youtube_service, "youtube.youtubekit.service.YouTubeService")
    _google = _ensure_service(google_service, "blog.blogkit.service.GoogleService")
    _openalex_owned = openalex_service is None
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # 키가 빠진 채 요청을 받기 시작하지 않도록 서버 시작 단계에서 멈춤
        base_settings.check_required()
        app.state.app_settings = base_settings
        app.state.rag_service = _rag
        app.state.qa_service = _qa
        app.state.openalex_service = _openalex
        app.state.wiki_service = _wiki
        app.state.youtube_service = _youtube
        app.state.google_service = _google
        
        try:
            yield
        finally:
            # 요청에 먼저 응답한 요약·추천 콜백이 끝나도록 잠시 기다림
            await background_tasks.shutdown(timeout_sec=BACKGROUND_SHUTDOWN_TIMEOUT_SEC)
            if _openalex_owned and hasattr(_openalex, "close"):
                await _openalex.close()
    
    app = FastAPI(
        title="LiveNote AI Gateway",
        version="1.0.0",
        description="LiveNote AI 서비스를 위한 통합 API Gateway",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # /health를 제외한 모든 API는 백엔드만 호출하도록 공유 키를 확인
    internal_only = [Depends(verify_internal_api_key)]
    app.include_router(rag_router, dependencies=internal_only)
    app.include_router(qa_router, dependencies=internal_only)
    app.include_router(rec_router, dependencies=internal_only)
    app.include_router(summary_router, dependencies=internal_only)

    # 테스트나 수동 호출 시 lifespan이 실행되지 않아도 안전하도록 기본 상태를 설정
    app.state.app_settings = base_settings
    app.state.rag_service = _rag
    app.state.qa_service = _qa
    app.state.openalex_service = _openalex
    app.state.wiki_service = _wiki
    app.state.youtube_service = _youtube
    app.state.google_service = _google
    
    @app.get("/health")
    async def health_check():
        """간단한 헬스 체크"""
        return {"status": "ok"}
    
    return app
