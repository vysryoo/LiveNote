"""
Utility functions for filtering and ranking
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def deduplicate_pages(pages: List[Dict]) -> List[Dict]:
    """
    중복 문서 제거 (제목 기준)
    
    Args:
        pages: 검색 결과 리스트
        
    Returns:
        중복 제거된 리스트
    """
    seen_titles = set()
    unique = []
    
    for page in pages:
        title = page.get("title", "").lower().strip()
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique.append(page)
    
    logger.info(f"🔄 중복 제거: {len(pages)}개 → {len(unique)}개")
    return unique


def rerank_pages(pages: List[Dict], keywords: List[str]) -> List[Dict]:
    """
    간단한 재랭킹 (키워드 매칭 점수)
    
    Args:
        pages: 검색 결과 리스트
        keywords: 검색 키워드 리스트
        
    Returns:
        재랭킹된 리스트
    """
    keywords_lower = [kw.lower() for kw in keywords]
    
    for page in pages:
        title_lower = page.get("title", "").lower()
        snippet_lower = page.get("snippet", "").lower()
        
        # 매칭 점수
        score = 0.0
        for kw in keywords_lower:
            if kw in title_lower:
                score += 2.0  # 제목 매칭: 가중치 2
            elif kw in snippet_lower:
                score += 0.5  # 스니펫 매칭: 가중치 0.5
        
        page["match_score"] = score
    
    # 점수 순 정렬
    ranked = sorted(pages, key=lambda x: x.get("match_score", 0), reverse=True)
    
    return ranked
