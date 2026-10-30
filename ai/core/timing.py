"""
요청 단계별 소요 시간 기록

요청 하나의 시작 시각을 기준으로 단계별 경과 시간(ms)을 JSON 한 줄 로그로 남긴다.
스트리밍 효과 측정과 변경 전후 비교에 사용한다.

로그 형식:
{"event": "timing", "kind": "qa", "request_id": "...", "stage": "item_question",
 "elapsed_ms": 812.4, "ts": 1761700000.123, "lecture_id": 1, "item": 0}
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any, Hashable

# 출력 형식은 core.logs.setup_logging에서 정함. 레벨은 앱 로그 설정과 관계없이 기록되도록 고정
logger = logging.getLogger("livenote.timing")
logger.setLevel(logging.INFO)


class RequestTimer:
    """요청 하나의 단계별 경과 시간을 기록한다."""

    def __init__(self, kind: str, **context: Any) -> None:
        """기록을 시작한다. 생성 시각이 경과 시간의 기준이 된다.

        Args:
            kind: 요청 종류 (qa, rec, summary 등)
            **context: 모든 기록에 함께 남길 값 (lecture_id, section_index 등)
        """
        self.kind = kind
        self.request_id = uuid.uuid4().hex[:12]
        self._context = context
        self._started = time.perf_counter()
        self._marked: set[tuple[str, Hashable]] = set()

    def mark(self, stage: str, **fields: Any) -> None:
        """단계 도달 시각을 기록한다.

        Args:
            stage: 단계 이름
            **fields: 이 기록에만 남길 값 (항목 번호, 개수 등)
        """
        record = {
            "event": "timing",
            "kind": self.kind,
            "request_id": self.request_id,
            "stage": stage,
            "elapsed_ms": round((time.perf_counter() - self._started) * 1000, 1),
            "ts": round(time.time(), 3),
            **self._context,
            **fields,
        }
        logger.info(json.dumps(record, ensure_ascii=False, default=str))

    def mark_once(self, stage: str, key: Hashable = None, **fields: Any) -> None:
        """같은 단계와 키 조합은 처음 한 번만 기록한다.

        답변 조각처럼 반복되는 이벤트에서 첫 도착 시각만 남길 때 사용한다.

        Args:
            stage: 단계 이름
            key: 단계 안에서 구분할 값 (항목 번호 등). None이면 단계당 한 번
            **fields: 이 기록에만 남길 값
        """
        if (stage, key) in self._marked:
            return
        self._marked.add((stage, key))
        self.mark(stage, **fields)
