"""
QnA 생성 LLM 클라이언트
"""

from typing import AsyncIterator

from core.llm import ModelPurpose, stream

from ..config.qa_config import QAConfig

# 화면이 수식 렌더링을 하지 않아 LaTeX를 쓰면 기호가 그대로 보임
SYSTEM_PROMPT = "당신은 교육 전문가입니다. 학습에 도움되는 질문과 답변을 생성합니다. 수식과 기호는 LaTeX 문법 없이 일반 텍스트로 씁니다."


class OpenAIClient:
    """QnA 생성 프롬프트를 공통 LLM 계층으로 스트리밍 호출한다."""

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
        async for delta in stream(
            ModelPurpose.QA,
            [("system", SYSTEM_PROMPT), ("user", prompt)],
            max_tokens=QAConfig.QA_MAX_TOKENS,
        ):
            yield delta
