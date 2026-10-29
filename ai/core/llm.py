"""
LLM 호출 공통 계층

모든 OpenAI 채팅 호출을 LangChain ChatOpenAI로 일원화한다.
용도(요약, QnA, 검색어 생성, 후보 검증)별 모델과 추론 강도를 한곳에서 정하고, 호출마다 소요 시간과 토큰 사용량을 로그로 남긴다.

환경변수로 덮어쓰기:
    LLM_MODEL: 모든 용도의 모델
    LLM_{용도}_MODEL, LLM_{용도}_REASONING_EFFORT: 용도별 모델, 추론 강도 (용도: SUMMARY, QA, QUERY, VERIFY)
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Sequence, Tuple
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import LLMResult
from langchain_openai import ChatOpenAI

from core.timing import logger as timing_logger

DEFAULT_MODEL = "gpt-6-luna"
DEFAULT_TIMEOUT_SEC = 30.0
DEFAULT_MAX_RETRIES = 2

# reasoning_effort를 받는 모델. gpt-4o 등 일반 모델에 보내면 요청이 거부됨
REASONING_MODEL_PREFIXES = ("gpt-5", "gpt-6", "o1", "o3", "o4")


class ModelPurpose(str, Enum):
    """LLM 호출 용도."""

    SUMMARY = "summary"
    QA = "qa"
    QUERY = "query"
    VERIFY = "verify"


@dataclass(frozen=True)
class ModelSettings:
    """용도별 모델 설정."""

    model: str
    reasoning_effort: Optional[str]


# 스트리밍(QA)은 첫 글자 시간을 줄이기 위해 추론을 끔. 값은 스트리밍 측정(L)에서 다시 정함
DEFAULT_REASONING_EFFORT = {
    ModelPurpose.SUMMARY: "none",
    ModelPurpose.QA: "none",
    ModelPurpose.QUERY: "none",
    ModelPurpose.VERIFY: "none",
}

Message = Tuple[str, str]


def model_settings(purpose: ModelPurpose) -> ModelSettings:
    """용도의 모델 설정을 환경변수와 기본값으로 정한다.

    Args:
        purpose: 호출 용도
    Returns:
        모델 설정. 추론 모델이 아니면 reasoning_effort는 None
    """
    prefix = f"LLM_{purpose.name}"
    model = os.getenv(f"{prefix}_MODEL") or os.getenv("LLM_MODEL") or DEFAULT_MODEL
    effort = os.getenv(f"{prefix}_REASONING_EFFORT") or DEFAULT_REASONING_EFFORT[purpose]
    if not model.startswith(REASONING_MODEL_PREFIXES):
        effort = None
    return ModelSettings(model=model, reasoning_effort=effort)


class UsageLogger(AsyncCallbackHandler):
    """LLM 호출마다 용도, 모델, 소요 시간, 토큰 사용량을 JSON 한 줄로 남긴다."""

    def __init__(self, purpose: ModelPurpose, model: str) -> None:
        self._purpose = purpose
        self._model = model
        self._started: Dict[UUID, float] = {}

    async def on_chat_model_start(self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], *, run_id: UUID, **kwargs: Any) -> None:
        self._started[run_id] = time.perf_counter()

    async def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> None:
        self._log(run_id, usage_from_result(response), error=None)

    async def on_llm_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        self._log(run_id, {}, error=type(error).__name__)

    def _log(self, run_id: UUID, usage: Dict[str, int], error: Optional[str]) -> None:
        started = self._started.pop(run_id, None)
        record = {
            "event": "llm",
            "purpose": self._purpose.value,
            "model": self._model,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 1) if started else None,
            **usage,
        }
        if error:
            record["error"] = error
        timing_logger.info(json.dumps(record, ensure_ascii=False))


def usage_from_result(response: LLMResult) -> Dict[str, int]:
    """LLM 결과에서 입력·출력·추론 토큰 수를 꺼낸다.

    Args:
        response: LangChain LLM 결과
    Returns:
        {"input_tokens", "output_tokens", "reasoning_tokens"}. 사용량 정보가 없으면 빈 dict
    """
    for generations in response.generations:
        for generation in generations:
            message = getattr(generation, "message", None)
            usage = getattr(message, "usage_metadata", None)
            if usage:
                details = usage.get("output_token_details") or {}
                return {
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "reasoning_tokens": details.get("reasoning", 0),
                }
    return {}


def build_chat_model(purpose: ModelPurpose, max_tokens: Optional[int] = None) -> ChatOpenAI:
    """용도에 맞는 ChatOpenAI를 만든다.

    Args:
        purpose: 호출 용도
        max_tokens: 최대 출력 토큰. 추론 모델은 추론 토큰도 포함됨
    Returns:
        사용량 기록 콜백이 붙은 ChatOpenAI
    """
    settings = model_settings(purpose)
    kwargs: Dict[str, Any] = {
        "model": settings.model,
        "timeout": DEFAULT_TIMEOUT_SEC,
        "max_retries": DEFAULT_MAX_RETRIES,
        "stream_usage": True,
        "callbacks": [UsageLogger(purpose, settings.model)],
    }
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    if settings.reasoning_effort:
        kwargs["reasoning_effort"] = settings.reasoning_effort
    return ChatOpenAI(**kwargs)


def to_messages(messages: Sequence[Message]) -> List[BaseMessage]:
    """(역할, 내용) 목록을 LangChain 메시지로 바꾼다.

    Args:
        messages: ('system' 또는 'user', 내용) 목록
    Returns:
        LangChain 메시지 목록
    Raises:
        ValueError: 지원하지 않는 역할인 경우
    """
    converted: List[BaseMessage] = []
    for role, content in messages:
        if role == "system":
            converted.append(SystemMessage(content))
        elif role == "user":
            converted.append(HumanMessage(content))
        else:
            raise ValueError(f"지원하지 않는 역할: {role}")
    return converted


async def complete(
    purpose: ModelPurpose,
    messages: Sequence[Message],
    max_tokens: Optional[int] = None,
    json_mode: bool = False,
) -> str:
    """응답 전체를 한 번에 받는다.

    Args:
        purpose: 호출 용도
        messages: ('system' 또는 'user', 내용) 목록
        max_tokens: 최대 출력 토큰
        json_mode: True면 JSON 객체만 응답하도록 요청
    Returns:
        응답 본문 (앞뒤 공백 제거)
    Raises:
        openai.APIError: OpenAI 호출 실패 (재시도 후)
    """
    model = build_chat_model(purpose, max_tokens)
    runnable = model.bind(response_format={"type": "json_object"}) if json_mode else model
    result: AIMessage = await runnable.ainvoke(to_messages(messages))
    return str(result.content or "").strip()


async def stream(
    purpose: ModelPurpose,
    messages: Sequence[Message],
    max_tokens: Optional[int] = None,
) -> AsyncIterator[str]:
    """응답을 생성되는 대로 조각 단위로 받는다.

    Args:
        purpose: 호출 용도
        messages: ('system' 또는 'user', 내용) 목록
        max_tokens: 최대 출력 토큰
    Returns:
        응답 조각을 차례로 돌려주는 비동기 반복자
    Raises:
        openai.APIError: OpenAI 호출 실패. 이미 돌려준 조각은 취소되지 않음
    """
    model = build_chat_model(purpose, max_tokens)
    async for chunk in model.astream(to_messages(messages)):
        if chunk.content:
            yield str(chunk.content)
