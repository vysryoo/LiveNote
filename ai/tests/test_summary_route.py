from __future__ import annotations

import asyncio

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel

pytestmark = pytest.mark.anyio("asyncio")

TRANSCRIPT = ["스택은 마지막에 넣은 원소를 먼저 꺼내는 구조입니다.", "큐는 먼저 넣은 원소를 먼저 꺼냅니다."]


@pytest.fixture
def summary_model(monkeypatch):
    from summary import service

    service.build_summary_chain.cache_clear()
    monkeypatch.setattr(service, "build_chat_model", lambda purpose, max_tokens: FakeListChatModel(responses=["  스택과 큐 비교  "]))
    yield
    service.build_summary_chain.cache_clear()


async def test_summary_is_sent_to_callback_with_section_times(async_client, callback_recorder, summary_model, internal_api_key):
    response = await async_client.post("/summary/generate", json={
        "lectureId": 1,
        "sectionIndex": 2,
        "summaryId": 5,
        "transcript": TRANSCRIPT,
        "callbackUrl": "http://backend/callback?source=ai",
    })
    await asyncio.sleep(0.05)

    assert response.status_code == 202
    assert response.json() == {"status": "accepted"}
    assert callback_recorder == [{
        "url": "http://backend/callback?source=ai&type=summary",
        "json": {
            "id": 5,
            "summaryId": 5,
            "lectureId": 1,
            "sectionIndex": 2,
            "startSec": 60,
            "endSec": 90,
            "text": "스택과 큐 비교",
            "phase": "FINAL",
            "status": "COMPLETED",
        },
        "headers": {"X-Internal-Api-Key": internal_api_key},
    }]


async def test_short_transcript_is_skipped_with_notice(async_client, callback_recorder, summary_model):
    response = await async_client.post("/summary/generate", json={
        "lectureId": 1,
        "sectionIndex": 0,
        "transcript": "네 안녕",
        "phase": "partial",
        "startSec": 3,
        "callbackUrl": "http://backend/callback",
    })
    await asyncio.sleep(0.05)

    assert response.json() == {"status": "skipped", "reason": "too_short"}
    payload = callback_recorder[0]["json"]
    assert callback_recorder[0]["url"] == "http://backend/callback?type=summary"
    assert (payload["text"], payload["status"], payload["phase"]) == ("요약을 생성하기에 강의가 너무 짧습니다.", "TOO_SHORT", "PARTIAL")
    assert (payload["startSec"], payload["endSec"]) == (3, 33)


async def test_missing_callback_url_is_rejected(async_client, callback_recorder, summary_model):
    response = await async_client.post("/summary/generate", json={"lectureId": 1, "sectionIndex": 0, "transcript": TRANSCRIPT})

    assert response.status_code == 400
    assert callback_recorder == []
