"""
QA 생성 설정
"""

import os


class QAConfig:
    """QA 생성 관련 설정"""
    
    # OpenAI API
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_TIMEOUT: int = 30  # seconds
    
    # 모델 설정
    #QA_MODEL: str = "gpt-4o"
    QA_MODEL: str = "gpt-4o-mini"
    QA_MAX_TOKENS: int = 500
    QA_TEMPERATURE: float = 0.5
    
    # 기본값
    DEFAULT_LANGUAGE: str = "ko"
    DEFAULT_QUESTION_TYPES: list = ["개념", "응용", "비교", "심화", "실습"]
    DEFAULT_QA_COUNT: int = 3
    
    # 검증
    MIN_SUMMARY_LENGTH: int = 10
    MAX_QA_COUNT: int = 5
    
    @classmethod
    def validate(cls):
        """설정 검증"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
