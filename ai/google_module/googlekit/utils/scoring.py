"""
Google 검색 결과 Heuristic 점수 계산
"""
import logging
from typing import List
from ..config import flags

logger = logging.getLogger(__name__)


def heuristic_score(
    title: str,
    snippet: str,
    keywords: List[str],
    display_link: str
) -> float:
    """
    Heuristic 점수 계산
    
    가중치:
    - 제목 매칭: 40%
    - 스니펫 매칭: 30%
    - 도메인 신뢰도: 30%
    
    Args:
        title: 검색 결과 제목
        snippet: 검색 결과 스니펫
        keywords: 검색 키워드 리스트
        display_link: 도메인 (예: naver.com)
        
    Returns:
        점수 (0.0-10.0)
    """
    title_lower = title.lower()
    snippet_lower = snippet.lower()
    
    # 1. 제목 매칭 점수 (0-10)
    title_score = 0.0
    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in title_lower:
            title_score += 10.0 / len(keywords)
    title_score = min(title_score, 10.0)
    
    # 2. 스니펫 매칭 점수 (0-10)
    snippet_score = 0.0
    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in snippet_lower:
            snippet_score += 10.0 / len(keywords)
    snippet_score = min(snippet_score, 10.0)
    
    # 3. 도메인 신뢰도 점수 (0-10)
    domain_score = 5.0  # 기본값
    display_link_lower = display_link.lower()
    
    for trusted_domain in flags.TRUSTED_DOMAINS:
        if trusted_domain.lower() in display_link_lower:
            domain_score = 10.0
            break
    
    # 가중 평균
    final_score = (
        title_score * flags.WEIGHT_TITLE_MATCH +
        snippet_score * flags.WEIGHT_SNIPPET_MATCH +
        domain_score * flags.WEIGHT_DOMAIN_TRUST
    )
    
    return round(final_score, 2)


def calculate_reason(
    title: str,
    snippet: str,
    keywords: List[str],
    score: float,
    language: str = "ko"
) -> str:
    """
    Heuristic 점수에 대한 이유 생성
    
    Args:
        title: 검색 결과 제목
        snippet: 검색 결과 스니펫
        keywords: 검색 키워드 리스트
        score: 계산된 점수
        language: 응답 언어
        
    Returns:
        추천 이유 (1-2문장)
    """
    matched_keywords = [
        kw for kw in keywords
        if kw.lower() in title.lower() or kw.lower() in snippet.lower()
    ]
    
    if language == "ko":
        if score >= 7.0:
            return f"키워드 '{', '.join(matched_keywords[:2])}'와 높은 관련성을 보이는 자료입니다."
        elif score >= 5.0:
            return f"키워드 '{', '.join(matched_keywords[:2])}'와 관련된 유용한 정보를 제공합니다."
        else:
            return "검색 결과와 부분적으로 관련이 있습니다."
    else:
        if score >= 7.0:
            return f"Highly relevant to keywords '{', '.join(matched_keywords[:2])}'."
        elif score >= 5.0:
            return f"Provides useful information related to '{', '.join(matched_keywords[:2])}'."
        else:
            return "Partially relevant to the search query."
