"""
YouTube 유틸리티 함수 (필터링, 중복 제거, Heuristic 점수)
"""
from __future__ import annotations

import re
import math
from typing import Dict, Iterable, List, Tuple

from rapidfuzz import fuzz
from ..config import flags


def normalize_title(t: str) -> str:
    """제목 정규화 (소문자 + 특수문자 제거)"""
    t = t.lower()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^a-z0-9가-힣 _\-]", "", t)
    return t.strip()


def deduplicate_items(items: Iterable[Tuple[str, Dict]]) -> List[Dict]:
    """중복 제거 (키 기반)"""
    seen = set()
    out: List[Dict] = []
    for key, payload in items:
        if key in seen:
            continue
        seen.add(key)
        out.append(payload)
    return out


def _views_score(view_count: int) -> float:
    """조회수 점수 (로그 스케일 → [0, 1])"""
    if view_count <= 0:
        return 0.0
    return min(1.0, math.log10(view_count + 1) / 6.0)


def _recency_score(publish_time: str) -> float:
    """최신성 점수 (연도 기반 → [0, 1])"""
    # Format: 2024-01-01T00:00:00Z
    try:
        year = int(publish_time[:4])
        return max(0.0, min(1.0, (year - 2015) / 10.0))
    except Exception:
        return 0.5


def heuristic_score(
    *, title: str, query: str, view_count: int, publish_time: str
) -> float:
    """
    Heuristic 점수 계산 (0~10)
    
    - 제목 유사도 (flags.WEIGHT_TITLE_MATCH)
    - 조회수 (flags.WEIGHT_VIEWS)
    - 최신성 (flags.WEIGHT_RECENCY)
    """
    # 제목 유사도 [0, 1]
    sim = fuzz.token_set_ratio(title, query) / 100.0
    
    # 조회수, 최신성 점수
    v = _views_score(view_count)
    r = _recency_score(publish_time)
    
    # 가중 평균 → 0~10 스케일
    raw = (
        flags.WEIGHT_TITLE_MATCH * sim 
        + flags.WEIGHT_VIEWS * v 
        + flags.WEIGHT_RECENCY * r
    )
    
    return max(0.0, min(10.0, raw * 10.0))
