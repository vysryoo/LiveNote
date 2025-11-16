"""
Wikipedia module configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()


class WikiConfig:
    """Wikipedia 모듈 설정"""
    
    # ━━━ OpenAI API ━━━
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # ━━━ Wikipedia API ━━━
    TIMEOUT: int = 15  # HTTP 타임아웃 (초)
    USER_AGENT: str = os.getenv(
        "WIKIKIT_USER_AGENT",
        "WikiKit/0.1 (+https://github.com/nongman25; contact: wook252wook@gmail.com)",
    )
    
    # ━━━ 기본값 ━━━
    DEFAULT_LANGUAGE: str = "en"
    DEFAULT_TOP_K: int = 5
    DEFAULT_WIKI_LANG: str = "en"  # 영문 우선
    
    # ━━━ 검색 설정 ━━━
    # SEARCH_LIMIT: 한 개의 키워드로 Wikipedia를 검색할 때 가져올 문서 개수
    # 예: "Stack" 키워드로 검색 → 최대 3개 문서 반환
    # 값이 크면: 더 많은 후보 확보 (품질 향상) BUT API 호출 비용 증가
    # 값이 작면: 빠른 응답 (속도 우선) BUT 좋은 문서를 놓칠 수 있음
    SEARCH_LIMIT: int = 3
    
    # FANOUT: 동시에 검색할 키워드 개수 (병렬 처리)
    # 예: LLM이 ["Stack", "LIFO", "Data Structure"] 생성 → FANOUT=3이면 3개 모두 동시 검색
    # 값이 크면: 더 다양한 결과 (검색 범위 확대) BUT 중복/관련성 낮은 문서 증가
    # 값이 작면: 핵심 키워드만 사용 (정확도 우선) BUT 검색 범위 좁음
    FANOUT: int = 3
    
    # ━━━ 제한 ━━━
    MAX_TOP_K: int = 10  # 최대 반환 개수
    CARD_LIMIT: int = 15  # 검증 대상 최대 수 (NO_SCORING 모드에서도 사용)
    
    # EXTRACT_SENTENCES: Wikipedia에서 가져올 문서 요약 문장 수
    # Wikipedia API가 문서의 도입부(intro)에서 이 개수만큼 문장을 추출해서 반환
    # 예: EXTRACT_SENTENCES=3 → "문장1. 문장2. 문장3." (약 50-150자)
    # 용도: 사용자에게 문서 미리보기 제공 (LLM 없이도 내용 파악 가능)
    # 값이 크면: 더 자세한 설명 BUT 응답 크기 증가
    # 값이 작면: 간결한 요약 BUT 정보 부족할 수 있음
    EXTRACT_SENTENCES: int = 3
    
    # ━━━ LLM 설정 ━━━
    #LLM_MODEL: str = "gpt-4o-mini"
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.2
    MAX_TOKENS_QUERY: int = 100  # 키워드 생성용 (간소화)
    MAX_TOKENS_SCORE: int = 80   # 스코어링용 (간소화)
    
    # ━━━ 병렬 처리 ━━━
    DETAIL_CONCURRENCY: int = 12   # 상세 정보 fetch 동시성
    VERIFY_CONCURRENCY: int = 10   # LLM 검증 동시성
    
    @classmethod
    def validate(cls):
        """설정 검증"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
