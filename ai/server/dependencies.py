"""
FastAPI 의존성
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Request

from core.config import Settings


@dataclass
class Services:
    """요청 처리에 쓰는 서비스 묶음. 테스트에서는 스텁으로 바꿔 끼운다."""

    rag: Any
    qa: Any
    rec: Any
    summary: Any


async def get_app_settings(request: Request) -> Settings:
    """앱 설정을 돌려준다."""
    return request.app.state.settings


async def get_services(request: Request) -> Services:
    """서비스 묶음을 돌려준다."""
    return request.app.state.services
