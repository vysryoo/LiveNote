"""
OpenAlex 모듈 설정
"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class OpenAlexConfig:
    """OpenAlex 모듈 설정"""
    
    # ━━━ OpenAI API ━━━
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # ━━━ OpenAlex API ━━━
    TIMEOUT: int = 15  # HTTP 타임아웃 (초) - 20→15 (25% 감소)
    PER_PAGE: int = 40  # 페이지당 결과 수 - 50→40 (API 응답 속도 개선) 응답 속도 개선의 핵심
    
    # ━━━ 기본값 ━━━
    DEFAULT_LANGUAGE: str = "ko"
    DEFAULT_TOP_K: int = 5
    DEFAULT_YEAR_FROM: int = 1930
    
    # ━━━ 제한 ━━━
    CARD_LIMIT: int = 13  # 검증 대상 최대 수 (13<-10, 23% 감소)
    MAX_TOP_K: int = 10   # 최대 반환 개수
    
    # ━━━ LLM 설정 ━━━
    LLM_MODEL: str = "gpt-4o-mini"
    #LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.2  # 0.3→0.2 (더 결정적, 빠른 응답)
    MAX_TOKENS_QUERY: int = 150   # 100<-80 (20% 감소)
    MAX_TOKENS_SCORE: int = 200   # 120→200 (reason 잘림 방지)
    
    # ━━━ 초록 길이 ━━━
    ABSTRACT_MAX_LENGTH: int = 400  # 500→400 (20% 감소)
    
    # ━━━ 병렬 처리 ━━━
    VERIFY_CONCURRENCY: int = 20  # 15→20 (33% 증가, YouTube와 동일)
    
    @classmethod
    def validate(cls):
        """설정 검증"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        if cls.CARD_LIMIT < 1:
            raise ValueError(f"CARD_LIMIT은 1 이상이어야 합니다: {cls.CARD_LIMIT}")
        
        if cls.VERIFY_CONCURRENCY < 1:
            raise ValueError(
                f"VERIFY_CONCURRENCY는 1 이상이어야 합니다: {cls.VERIFY_CONCURRENCY}"
            )
