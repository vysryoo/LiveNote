"""
FastAPI 의존성 헬퍼
"""
from __future__ import annotations

from fastapi import Request

from .config import AppSettings

async def get_settings(request: Request) -> AppSettings:
    """앱 설정 조회"""
    return request.app.state.app_settings


async def get_rag_service(request: Request):
    """RAG 서비스 인스턴스"""
    return request.app.state.rag_service


async def get_qa_service(request: Request):
    """QA 서비스 인스턴스"""
    return request.app.state.qa_service


async def get_openalex_service(request: Request):
    """OpenAlex 서비스 인스턴스"""
    return request.app.state.openalex_service


async def get_wiki_service(request: Request):
    """Wikipedia 서비스 인스턴스"""
    return request.app.state.wiki_service


async def get_youtube_service(request: Request):
    """YouTube 서비스 인스턴스"""
    return request.app.state.youtube_service


async def get_google_service(request: Request):
    """Google 서비스 인스턴스"""
    return request.app.state.google_service
