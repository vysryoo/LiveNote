"""
YouTube 모듈 설정
"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class YouTubeConfig:
    """YouTube 모듈 설정"""
    
    # ━━━ OpenAI API ━━━
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # ━━━ YouTube Data API v3 ━━━
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY") or os.getenv("KEY", "")
    TIMEOUT: int = 10  # HTTP 타임아웃 (초)
    
    # ━━━ 기본값 ━━━
    DEFAULT_LANGUAGE: str = "ko"
    DEFAULT_TOP_K: int = 5
    DEFAULT_YT_LANG: str = "en"
    
    # ━━━ 제한 ━━━
    MAX_TOP_K: int = 10   # 최대 반환 개수
    # MAX_SEARCH_RESULTS는 flags.py에서 정의 (중복 제거)
    
    # ━━━ LLM 설정 ━━━
    LLM_MODEL: str = "gpt-4o-mini"
    #LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.1
    MAX_TOKENS_QUERY: int = 300   # 쿼리 생성용
    MAX_TOKENS_SUMMARY: int = 400  # 요약 생성용
    MAX_TOKENS_SCORE: int = 300   # 스코어링용
    
    # ━━━ 콘텐츠 길이 제한 ━━━
    MAX_CONTENT_LENGTH: int = 500  # 요약 프롬프트에 넣을 최대 글자 수 (토큰 절약)
    
    # ━━━ 병렬 처리 ━━━
    VERIFY_CONCURRENCY: int = 20  # 동시 검증 수 (Semaphore 제한)
    
    # ━━━ Offline 모드 ━━━
    OFFLINE_MODE: bool = os.getenv("YT_OFFLINE_MODE", "0") == "1"
    
    @classmethod
    def validate(cls):
        """설정 검증"""
        from . import flags
        
        if not cls.OFFLINE_MODE:
            if not cls.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
            
            if not cls.YOUTUBE_API_KEY:
                raise ValueError("YOUTUBE_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        if flags.MAX_SEARCH_RESULTS < 1:
            raise ValueError(f"MAX_SEARCH_RESULTS는 1 이상이어야 합니다: {flags.MAX_SEARCH_RESULTS}")
        
        if cls.VERIFY_CONCURRENCY < 1:
            raise ValueError(
                f"VERIFY_CONCURRENCY는 1 이상이어야 합니다: {cls.VERIFY_CONCURRENCY}"
            )
