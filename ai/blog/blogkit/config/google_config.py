"""
Google 모듈 설정
"""
import os
from typing import Optional


class GoogleConfig:
    """Google 모듈 설정"""
    
    # API 키. 블로그 검색은 네이버 블로그 검색 API 사용
    NAVER_CLIENT_ID: str = os.getenv("NAVER_CLIENT_ID", "")
    NAVER_CLIENT_SECRET: str = os.getenv("NAVER_CLIENT_SECRET", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # 검색 설정
    DEFAULT_TOP_K: int = 5
    DEFAULT_LANGUAGE: str = "ko"
    DEFAULT_SEARCH_LANG: str = "en"
    
    # 제한
    MAX_TOP_K: int = 10
    CARD_LIMIT: int = 15  # 검증 대상 최대 수
    SEARCH_LIMIT: int = 10  # API 한 번 호출 시 최대 결과
    FANOUT: int = 1  # 동시 검색 키워드 개수
    
    # LLM 설정 (모델과 추론 강도는 core.llm의 QUERY·VERIFY 용도 설정을 따름)
    MAX_TOKENS_QUERY: int = 150
    MAX_TOKENS_SCORE: int = 120
    
    # 병렬 처리
    VERIFY_CONCURRENCY: int = 15
    
    @classmethod
    def validate(cls):
        """환경 변수 검증"""
        if not cls.NAVER_CLIENT_ID:
            raise ValueError("NAVER_CLIENT_ID가 설정되지 않았습니다.")
        if not cls.NAVER_CLIENT_SECRET:
            raise ValueError("NAVER_CLIENT_SECRET가 설정되지 않았습니다.")
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
