"""
백엔드 콜백 전송

요약·자료 추천은 요청에 먼저 응답한 뒤, 결과를 백엔드 콜백 URL로 보낸다.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

import httpx

from core.config import Settings

from .security import internal_auth_headers

logger = logging.getLogger(__name__)

CALLBACK_TIMEOUT_SEC = 30.0


async def post_callback(url: str, payload: Dict[str, Any], settings: Settings) -> None:
    """결과를 백엔드 콜백 URL로 보낸다. 실패하면 로그만 남긴다.

    Args:
        url: 콜백 URL
        payload: JSON 본문
        settings: 서버 설정 (내부 인증 키)
    """
    try:
        async with httpx.AsyncClient(timeout=CALLBACK_TIMEOUT_SEC) as client:
            await client.post(url, json=payload, headers=internal_auth_headers(settings))
    except Exception:
        logger.exception("콜백 전송 실패: %s", url)
