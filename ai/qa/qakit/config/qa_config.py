"""
QA 생성 설정
"""

import os


class QAConfig:
    """QA 생성 관련 설정"""
    
    # OpenAI API
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # 최대 출력 토큰. 모델과 추론 강도는 core.llm의 QA 용도 설정을 따름
    QA_MAX_TOKENS: int = 500
    
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
