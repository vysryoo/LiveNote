"""
논문 필터링 및 재랭킹 유틸리티
"""
import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def deduplicate_papers(papers: List[Dict]) -> List[Dict]:
    """
    중복 논문 제거 (DOI or 정규화된 제목)
    
    우선순위:
    1. DOI 존재 → DOI로 중복 체크
    2. DOI 없음 → 정규화된 제목으로 중복 체크
    
    Args:
        papers: 논문 리스트
        
    Returns:
        중복 제거된 논문 리스트
    """
    seen = set()
    unique = []
    
    for paper in papers:
        # DOI 우선, 없으면 정규화된 제목
        url = paper.get("url", "")
        
        # DOI가 있으면 DOI로 중복 체크
        if url and url.startswith("http"):
            key = url
        else:
            # DOI 없으면 제목으로 중복 체크
            key = _normalize_title(paper.get("title", ""))
        
        if key and key not in seen:
            seen.add(key)
            unique.append(paper)
    
    logger.info(f"🔍 중복 제거: {len(papers)}개 → {len(unique)}개")
    return unique


def rerank_papers(papers: List[Dict], query: Dict) -> List[Dict]:
    """
    간단한 재랭킹 (키워드 매칭 점수)
    
    점수 계산:
    - match_score = 제목 매칭 * 3 + 초록 매칭 * 1
    
    정렬:
    - (match_score, relevance_score) 내림차순
    
    Args:
        papers: 논문 리스트
        query: 검색 쿼리 (tokens 포함)
        
    Returns:
        재랭킹된 논문 리스트
    """
    tokens = [kw.lower() for kw in query.get("tokens", [])]
    
    for paper in papers:
        title_lower = paper.get("title", "").lower()
        abstract_lower = paper.get("abstract", "").lower()
        
        # 키워드 매칭 점수
        match_score = 0
        for kw in tokens:
            if kw in title_lower:
                match_score += 3
            if kw in abstract_lower:
                match_score += 1
        
        paper["match_score"] = match_score
    
    # 매칭 점수 + relevance_score 기준 정렬
    papers.sort(
        key=lambda x: (x.get("match_score", 0), x.get("relevance_score", 0)), 
        reverse=True
    )
    
    logger.info(f"🔄 재랭킹 완료: 상위 논문 match_score={papers[0].get('match_score', 0) if papers else 0}")
    
    return papers


def _normalize_title(title: str) -> str:
    """
    제목 정규화 (소문자 + 특수문자 제거)
    
    Args:
        title: 논문 제목
        
    Returns:
        정규화된 제목
    """
    return re.sub(r'[^\w\s]', '', title.lower()).strip()
