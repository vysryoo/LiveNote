"""
OpenAI API 클라이언트
"""

import os
from typing import AsyncIterator, Optional

from openai import AsyncOpenAI

from ..config.qa_config import QAConfig


class OpenAIClient:
    """OpenAI API 비동기 클라이언트"""
    
    def __init__(self, api_key: str = None, model: Optional[str] = None):
        """
        초기화
        
        Args:
            api_key: OpenAI API 키 (None이면 환경변수에서 로드)
        """
        # API 키 우선순위: 파라미터 > 환경변수 > config
        final_api_key = api_key or os.getenv("OPENAI_API_KEY") or QAConfig.OPENAI_API_KEY
        self.client = AsyncOpenAI(
            api_key=final_api_key,
            timeout=QAConfig.OPENAI_TIMEOUT
        )
        self.model = model or QAConfig.QA_MODEL
        self.max_tokens = QAConfig.QA_MAX_TOKENS
        self.temperature = QAConfig.QA_TEMPERATURE
    
    async def stream_text(self, prompt: str) -> AsyncIterator[str]:
        """
        응답을 생성되는 대로 조각 단위로 반환

        Args:
            prompt: 프롬프트 텍스트

        Yields:
            str: 모델 출력 조각

        Raises:
            APIError, APITimeoutError: OpenAI 호출 실패. 이미 반환한 조각은 취소되지 않음
        """
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "당신은 교육 전문가입니다. 학습에 도움되는 질문과 답변을 생성합니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stream=True,
        )
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
