"""
백엔드와 AI 서버 사이의 내부 요청 인증
"""
from __future__ import annotations

import os
import secrets
from typing import Dict, Optional

from fastapi import Header, HTTPException, status

INTERNAL_API_KEY_HEADER = "X-Internal-Api-Key"


def _configured_key() -> str:
    return os.getenv("INTERNAL_API_KEY", "")


async def verify_internal_api_key(
    x_internal_api_key: Optional[str] = Header(default=None),
) -> None:
    """백엔드가 보낸 요청인지 공유 키 헤더로 확인한다.

    Args:
        x_internal_api_key: 요청의 X-Internal-Api-Key 헤더 값
    Raises:
        HTTPException: 키가 없거나 다른 경우(401). 서버에 키가 설정되지 않았어도 모두 거부함
    """
    expected = _configured_key()
    # 키 설정이 빠진 채 실행돼도 열린 상태가 되지 않도록 모든 요청을 거부
    if not expected or not x_internal_api_key or not secrets.compare_digest(
        x_internal_api_key, expected
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid internal api key")


def internal_auth_headers() -> Dict[str, str]:
    """백엔드로 콜백을 보낼 때 붙일 인증 헤더를 만든다.

    Returns:
        공유 키 헤더
    """
    return {INTERNAL_API_KEY_HEADER: _configured_key()}
