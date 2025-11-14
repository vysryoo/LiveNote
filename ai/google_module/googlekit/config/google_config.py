"""
Google 모듈 설정
"""
import os
from typing import Optional


class GoogleConfig:
    """Google 모듈 설정"""
    
    # API 키
    GOOGLE_SEARCH_API_KEY: str = os.getenv("GOOGLE_SEARCH_API_KEY", "")
    GOOGLE_SEARCH_ENGINE_ID: str = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # 검색 설정
    DEFAULT_TOP_K: int = 5
    DEFAULT_LANGUAGE: str = "ko"
    DEFAULT_SEARCH_LANG: str = "en"
    
    # 제한
    MAX_TOP_K: int = 10
    CARD_LIMIT: int = 15  # 검증 대상 최대 수
    SEARCH_LIMIT: int = 10  # API 한 번 호출 시 최대 결과
    FANOUT: int = 3  # 동시 검색 키워드 개수
    
    # LLM 설정
    #LLM_MODEL: str = "gpt-4o-mini"
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.2
    MAX_TOKENS_QUERY: int = 100
    MAX_TOKENS_SCORE: int = 80
    
    # 병렬 처리
    VERIFY_CONCURRENCY: int = 15
    
    @classmethod
    def validate(cls):
        """환경 변수 검증"""
        if not cls.GOOGLE_SEARCH_API_KEY:
            raise ValueError("GOOGLE_SEARCH_API_KEY가 설정되지 않았습니다.")
        if not cls.GOOGLE_SEARCH_ENGINE_ID:
            raise ValueError("GOOGLE_SEARCH_ENGINE_ID가 설정되지 않았습니다.")
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
