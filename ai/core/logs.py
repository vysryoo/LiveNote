"""
로깅 설정

서버 프로세스 시작 시 한 번 호출한다. uvicorn은 자기 로거만 설정해, 설정이 없으면 앱 모듈의 INFO 로그가 출력되지 않는다.
"""
from __future__ import annotations

import logging
import sys

from core.timing import logger as timing_logger

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def setup_logging(level: int = logging.INFO) -> None:
    """앱 로그와 시간 기록 로그의 출력을 설정한다. 여러 번 호출해도 한 번만 적용된다.

    시간 기록·LLM 사용량 로그(livenote.timing)는 JSON 한 줄을 그대로 분석에 쓰도록 메시지만 출력한다.

    Args:
        level: 앱 로그 최소 레벨
    """
    logging.basicConfig(level=level, format=LOG_FORMAT)
    if not timing_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        timing_logger.addHandler(handler)
        timing_logger.propagate = False
