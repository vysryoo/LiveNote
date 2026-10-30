"""
섹션 요약 서비스
"""
from __future__ import annotations

from functools import lru_cache

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from core.config import SummarySettings
from core.llm import ModelPurpose, build_chat_model


@lru_cache(maxsize=4)
def build_summary_chain(max_tokens: int) -> Runnable:
    """요약 체인(프롬프트 | 모델 | 문자열)을 만든다. 같은 설정이면 만든 체인을 재사용한다.

    시스템 프롬프트와 전사는 템플릿 변수로 넣어, 본문의 중괄호가 템플릿 문법으로 해석되지 않게 한다.

    Args:
        max_tokens: 최대 출력 토큰
    Returns:
        {"system_prompt", "transcript"}를 받아 요약 문자열을 돌려주는 체인
    """
    prompt = ChatPromptTemplate.from_messages([("system", "{system_prompt}"), ("user", "{transcript}")])
    return prompt | build_chat_model(ModelPurpose.SUMMARY, max_tokens) | StrOutputParser()


class SummaryService:
    """섹션 전사를 1~2문장으로 요약한다."""

    def __init__(self, settings: SummarySettings) -> None:
        """서비스를 만든다.

        Args:
            settings: 요약 설정 (프롬프트, 최대 토큰, 최소 전사 길이)
        """
        self.settings = settings

    def is_too_short(self, transcript: str) -> bool:
        """공백을 뺀 전사 길이가 최소 길이 이하인지 판단한다.

        Args:
            transcript: 전사
        Returns:
            요약하지 않을 만큼 짧으면 True
        """
        return len("".join(transcript.split())) <= self.settings.min_transcript_length

    async def summarize(self, transcript: str) -> str:
        """전사를 요약한다.

        Args:
            transcript: 전사
        Returns:
            요약 (앞뒤 공백 제거)
        Raises:
            openai.APIError: OpenAI 호출 실패
        """
        summary = await build_summary_chain(self.settings.max_tokens).ainvoke(
            {"system_prompt": self.settings.system_prompt, "transcript": transcript}
        )
        return summary.strip()
