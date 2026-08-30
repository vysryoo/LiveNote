"""
공유 데이터 모델과 Enum 정의
"""
from __future__ import annotations

from enum import Enum


class QnAType(str, Enum):
    """QA 질문 유형"""
    CONCEPT = "CONCEPT"
    APPLICATION = "APPLICATION"
    ADVANCED = "ADVANCED"
    COMPARISON = "COMPARISON"


class ResourceType(str, Enum):
    """추천 리소스 유형"""
    PAPER = "PAPER"      # OpenAlex
    WIKI = "WIKI"        # Wikipedia
    VIDEO = "VIDEO"      # YouTube
    BLOG = "BLOG"        # Google 검색
