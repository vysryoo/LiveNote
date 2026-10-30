"""
백그라운드 작업 보관

요청에는 먼저 응답하고 뒤에서 이어 가는 작업(요약 생성, 자료 추천 콜백)을 띄운다.
asyncio는 이벤트 루프가 작업을 약하게만 참조하므로, 참조를 잡아 두지 않은 작업은
실행 도중 가비지 컬렉션으로 사라질 수 있다. 여기서 끝날 때까지 참조를 보관한다.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Coroutine, Set

logger = logging.getLogger(__name__)

_running: Set[asyncio.Task] = set()


def run_in_background(coro: Coroutine, name: str | None = None) -> asyncio.Task:
    """코루틴을 백그라운드 작업으로 띄우고 끝날 때까지 참조를 보관한다.

    Args:
        coro: 실행할 코루틴. 예외는 코루틴 안에서 처리해야 함 (처리하지 않은 예외는 로그만 남김)
        name: 로그에 쓸 작업 이름
    Returns:
        띄운 작업
    """
    task = asyncio.create_task(coro, name=name)
    _running.add(task)
    task.add_done_callback(_finish)
    return task


def _finish(task: asyncio.Task) -> None:
    _running.discard(task)
    if not task.cancelled() and task.exception() is not None:
        logger.error("백그라운드 작업 실패: %s", task.get_name(), exc_info=task.exception())


def running_count() -> int:
    """실행 중인 백그라운드 작업 수를 돌려준다.

    Returns:
        작업 수
    """
    return len(_running)


async def shutdown(timeout_sec: float) -> None:
    """서버 종료 시 남은 작업을 기다리고, 시간 안에 끝나지 않은 작업은 취소한다.

    Args:
        timeout_sec: 기다릴 최대 시간(초)
    """
    if not _running:
        return
    pending = list(_running)
    logger.info("백그라운드 작업 %d개 종료 대기 (최대 %.0f초)", len(pending), timeout_sec)
    _, still_running = await asyncio.wait(pending, timeout=timeout_sec)
    for task in still_running:
        task.cancel()
    if still_running:
        await asyncio.gather(*still_running, return_exceptions=True)
        logger.warning("백그라운드 작업 %d개를 종료 시간 초과로 취소함", len(still_running))
