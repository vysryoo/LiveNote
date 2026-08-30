"""
Google 검색 결과 필터링 유틸리티
"""
import logging
from typing import List, Dict, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def deduplicate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    URL 기준 중복 제거
    
    Args:
        results: 검색 결과 리스트
        
    Returns:
        중복 제거된 결과 리스트
    """
    seen_urls = set()
    unique_results = []
    
    for result in results:
        url = result.get("link", "")
        if not url:
            continue
        
        # URL 정규화 (프로토콜, www 제거 후 비교)
        parsed = urlparse(url)
        normalized = f"{parsed.netloc.replace('www.', '')}{parsed.path}"
        
        if normalized not in seen_urls:
            seen_urls.add(normalized)
            unique_results.append(result)
    
    logger.info(f"🔄 중복 제거: {len(results)}개 → {len(unique_results)}개")
    
    return unique_results


def rerank_results(
    results: List[Dict[str, Any]],
    keywords: List[str]
) -> List[Dict[str, Any]]:
    """
    키워드 매칭도 기준 재정렬
    
    Args:
        results: 검색 결과 리스트
        keywords: 검색 키워드 리스트
        
    Returns:
        재정렬된 결과 리스트
    """
    def keyword_match_score(result: Dict[str, Any]) -> float:
        """키워드 매칭 점수 계산"""
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        
        score = 0.0
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in title:
                score += 2.0  # 제목 매칭 가중치 높음
            if keyword_lower in snippet:
                score += 1.0
        
        return score
    
    # 점수 계산 및 정렬
    scored_results = [
        (result, keyword_match_score(result))
        for result in results
    ]
    scored_results.sort(key=lambda x: x[1], reverse=True)
    
    # 결과만 반환
    reranked = [result for result, _ in scored_results]
    
    logger.info(f"📊 재정렬 완료: {len(reranked)}개")
    
    return reranked


def filter_excluded_urls(
    results: List[Dict[str, Any]],
    exclude_urls: List[str]
) -> List[Dict[str, Any]]:
    """
    제외 URL 필터링
    
    Args:
        results: 검색 결과 리스트
        exclude_urls: 제외할 URL 리스트
        
    Returns:
        필터링된 결과 리스트
    """
    if not exclude_urls:
        return results
    
    # URL 정규화
    exclude_normalized = set()
    for url in exclude_urls:
        parsed = urlparse(url)
        normalized = f"{parsed.netloc.replace('www.', '')}{parsed.path}"
        exclude_normalized.add(normalized)
    
    filtered = []
    for result in results:
        url = result.get("link", "")
        parsed = urlparse(url)
        normalized = f"{parsed.netloc.replace('www.', '')}{parsed.path}"
        
        if normalized not in exclude_normalized:
            filtered.append(result)
    
    logger.info(f"🚫 제외 URL 필터링: {len(results)}개 → {len(filtered)}개")
    
    return filtered
