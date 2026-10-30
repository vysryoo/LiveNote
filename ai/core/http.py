"""
외부 API 호출 공통

검색 API(OpenAlex, 위키백과, YouTube, 네이버)는 요청이 몰리면 429나 503으로 거절한다.
거절되면 Retry-After를 따르거나 1·2·4초로 늘려 기다렸다가 최대 3번 다시 시도한다.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_STATUSES = {429, 503}
MAX_RETRY_WAIT_SEC = 10.0


def retry_wait_seconds(response: httpx.Response, attempt: int) -> float:
    """다시 시도하기 전 기다릴 시간을 정한다. Retry-After(초)가 있으면 따르고, 없으면 1·2·4초로 늘린다.

    Args:
        response: 거절 응답
        attempt: 지금까지 시도 횟수 (1부터)
    Returns:
        대기 시간(초). 최대 10초
    """
    header = response.headers.get("Retry-After", "")
    wait = float(header) if header.replace(".", "", 1).isdigit() else 2.0 ** (attempt - 1)
    return min(wait, MAX_RETRY_WAIT_SEC)


async def get_with_retry(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    limiter: Optional[asyncio.Semaphore] = None,
) -> httpx.Response:
    """GET 요청을 보내고, 429·503이면 기다렸다가 다시 시도한다.

    Args:
        client: 요청에 쓸 HTTP 클라이언트
        url: 요청 주소
        params: 쿼리 파라미터
        headers: 요청 헤더
        limiter: 동시 요청 수 제한. 기다리는 동안에는 자리를 비움
    Returns:
        마지막 응답. 재시도 후에도 거절이면 거절 응답을 그대로 돌려줌
    Raises:
        httpx.HTTPError: 네트워크 오류
    """
    for attempt in range(1, MAX_RETRIES + 2):
        if limiter is None:
            response = await client.get(url, params=params, headers=headers)
        else:
            async with limiter:
                response = await client.get(url, params=params, headers=headers)
        if response.status_code not in RETRY_STATUSES or attempt > MAX_RETRIES:
            return response
        wait = retry_wait_seconds(response, attempt)
        logger.warning("%s %d, %.1f초 후 재시도 (%d/%d)", response.url.host, response.status_code, wait, attempt, MAX_RETRIES)
        await asyncio.sleep(wait)
    raise RuntimeError("unreachable")
