"""
논문 파싱 유틸리티
"""
import logging
from typing import Dict, Optional

from ..config.openalex_config import OpenAlexConfig

logger = logging.getLogger(__name__)


def parse_abstract_inverted_index(inverted_index: Optional[Dict]) -> str:
    """
    Inverted index 형태 초록을 일반 텍스트로 변환
    
    Args:
        inverted_index: {"word": [pos1, pos2, ...], ...}
        
    Returns:
        일반 텍스트 초록 (최대 ABSTRACT_MAX_LENGTH 자)
    """
    if not inverted_index:
        return ""
    
    try:
        # 단어와 위치를 리스트로 변환
        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        
        # 위치 순으로 정렬
        word_positions.sort()
        
        # 텍스트 재구성
        abstract = " ".join([word for _, word in word_positions])
        
        # 설정된 최대 길이로 자르기
        if len(abstract) > OpenAlexConfig.ABSTRACT_MAX_LENGTH:
            abstract = abstract[:OpenAlexConfig.ABSTRACT_MAX_LENGTH]
        
        return abstract
        
    except Exception as e:
        logger.error(f"❌ 초록 파싱 실패: {e}")
        return ""
