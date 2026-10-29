from __future__ import annotations

import json
import logging

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult

from core import llm
from core.llm import ModelPurpose, model_settings, to_messages, usage_from_result
from core.timing import logger as timing_logger

pytestmark = pytest.mark.anyio("asyncio")


class _Collector(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(json.loads(record.getMessage()))


@pytest.fixture
def clear_llm_env(monkeypatch):
    for key in ("LLM_MODEL", "LLM_QA_MODEL", "LLM_QA_REASONING_EFFORT", "LLM_VERIFY_MODEL"):
        monkeypatch.delenv(key, raising=False)


def test_model_settings_defaults_to_luna_without_reasoning(clear_llm_env):
    settings = model_settings(ModelPurpose.QA)

    assert settings.model == "gpt-6-luna"
    assert settings.reasoning_effort == "none"


def test_model_settings_env_override_and_drop_effort_for_non_reasoning_model(clear_llm_env, monkeypatch):
    monkeypatch.setenv("LLM_QA_REASONING_EFFORT", "low")
    monkeypatch.setenv("LLM_VERIFY_MODEL", "gpt-4o")

    assert model_settings(ModelPurpose.QA).reasoning_effort == "low"
    assert model_settings(ModelPurpose.VERIFY) == llm.ModelSettings(model="gpt-4o", reasoning_effort=None)


def test_build_chat_model_sends_effort_and_token_limit(clear_llm_env):
    model = llm.build_chat_model(ModelPurpose.SUMMARY, max_tokens=256)

    payload = model._get_request_payload(to_messages([("user", "hi")]))

    assert payload["model"] == "gpt-6-luna"
    assert payload["reasoning_effort"] == "none"
    assert payload["max_completion_tokens"] == 256
    assert "temperature" not in payload


def test_to_messages_rejects_unknown_role():
    with pytest.raises(ValueError):
        to_messages([("assistant", "x")])


def test_usage_from_result_reads_reasoning_tokens():
    message = AIMessage(
        "ok",
        usage_metadata={
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
            "output_token_details": {"reasoning": 2},
        },
    )
    result = LLMResult(generations=[[ChatGeneration(message=message)]])

    assert usage_from_result(result) == {"input_tokens": 10, "output_tokens": 5, "reasoning_tokens": 2}
    assert usage_from_result(LLMResult(generations=[[ChatGeneration(message=AIMessage("x"))]])) == {}


async def test_complete_and_stream_use_purpose_model_and_log_usage(monkeypatch):
    collector = _Collector()
    timing_logger.addHandler(collector)

    def fake_model(purpose, max_tokens=None):
        return GenericFakeChatModel(
            messages=iter([AIMessage("응답 본문")]),
            callbacks=[llm.UsageLogger(purpose, "fake")],
        )

    monkeypatch.setattr(llm, "build_chat_model", fake_model)
    try:
        assert await llm.complete(ModelPurpose.QUERY, [("user", "질문")], json_mode=True) == "응답 본문"
        chunks = [c async for c in llm.stream(ModelPurpose.QA, [("system", "s"), ("user", "u")])]
    finally:
        timing_logger.removeHandler(collector)

    assert "".join(chunks) == "응답 본문"
    logged = [r for r in collector.records if r["event"] == "llm"]
    assert [r["purpose"] for r in logged] == ["query", "qa"]
    assert all(r["elapsed_ms"] is not None for r in logged)
