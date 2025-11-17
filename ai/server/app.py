"""
FastAPI 애플리케이션 생성
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from .config import AppSettings
from .routes import qa_router, rag_router, rec_router


def _ensure_service(service: Any, factory_path: str):
    """지연 로딩으로 서비스 인스턴스 확보"""
    if service is not None:
        return service
    
    module_name, attr = factory_path.rsplit(".", 1)
    module = __import__(module_name, fromlist=[attr])
    factory = getattr(module, attr)
    return factory()


def create_app(
    settings: AppSettings | None = None,
    *,
    rag_service=None,
    qa_service=None,
    openalex_service=None,
    wiki_service=None,
    youtube_service=None,
    google_service=None,
) -> FastAPI:
    """FastAPI 앱 생성"""
    base_settings = settings or AppSettings()
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # 서비스 및 설정 초기화 (지연 로딩)
        _rag = _ensure_service(rag_service, "cap1_RAG_module.ragkit.service.RAGService")
        _qa = _ensure_service(qa_service, "cap1_QA_module.qakit.service.QAService")
        _openalex = _ensure_service(openalex_service, "cap1_openalex_module.openalexkit.service.OpenAlexService")
        _wiki = _ensure_service(wiki_service, "cap1_wiki_module.wikikit.service.WikiService")
        _youtube = _ensure_service(youtube_service, "cap1_youtube_module.youtubekit.service.YouTubeService")
        _google = _ensure_service(google_service, "cap1_google_module.googlekit.service.GoogleService")
        
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
            if openalex_service is None and hasattr(_openalex, "close"):
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
    
    app.include_router(rag_router)
    app.include_router(qa_router)
    app.include_router(rec_router)
    
    @app.get("/health")
    async def health_check():
        """간단한 헬스 체크"""
        return {"status": "ok"}
    
    return app
