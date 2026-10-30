"""
QnA 생성 서비스
"""
from __future__ import annotations

from typing import AsyncIterator

from core.llm import ModelPurpose, stream

from .graph import StreamText, build_qa_graph
from .models import QAEvent, QARequest
from .prompts import SYSTEM_PROMPT, build_prompt

# 최대 출력 토큰. 모델과 추론 강도는 core.llm의 QA 용도 설정을 따름
QA_MAX_TOKENS = 500


async def stream_llm(prompt: str) -> AsyncIterator[str]:
    """QnA 프롬프트를 QA 용도 모델로 스트리밍 호출한다.

    Args:
        prompt: 사용자 메시지로 보낼 프롬프트
    Returns:
        모델 출력 조각을 차례로 돌려주는 비동기 반복자
    Raises:
        openai.APIError: OpenAI 호출 실패. 이미 돌려준 조각은 취소되지 않음
    """
    async for delta in stream(ModelPurpose.QA, [("system", SYSTEM_PROMPT), ("user", prompt)], max_tokens=QA_MAX_TOKENS):
        yield delta


class QAService:
    """질문 유형별 QnA를 동시에 생성하며 진행 이벤트를 내보낸다."""

    def __init__(self, stream_text: StreamText = stream_llm) -> None:
        """서비스를 만든다.

        Args:
            stream_text: 프롬프트를 받아 모델 출력 조각을 내주는 함수. 테스트에서 바꿔 끼움
        """
        self.graph = build_qa_graph(stream_text)

    async def stream_questions(self, request: QARequest) -> AsyncIterator[QAEvent]:
        """질문 유형별로 동시에 생성하며 진행 이벤트를 도착 순서대로 내보낸다.

        Args:
            request: QnA 생성 요청
        Returns:
            QAEvent를 차례로 돌려주는 비동기 반복자. 이벤트 종류는 QAEvent 설명 참고
        """
        items = [(q_type, build_prompt(request, q_type)) for q_type in request.question_types]
        # 받는 쪽이 중간에 끊으면 그래프 실행이 취소되어 남은 생성도 멈춤
        async for event in self.graph.astream({"items": items}, stream_mode="custom"):
            yield event
