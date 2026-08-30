from __future__ import annotations

import asyncio
from typing import List

import pytest

pytestmark = pytest.mark.anyio("asyncio")

from server.models import QnAType
from tests.conftest import StubRetrievedChunk


def _prepare_chunks() -> List[StubRetrievedChunk]:
    return [
        StubRetrievedChunk(id="c1", text="스택은 LIFO 구조다.", score=0.91, metadata={"section_id": "1"}),
        StubRetrievedChunk(id="c2", text="큐는 FIFO 구조와 비교된다.", score=0.82, metadata={"section_id": "2"}),
    ]


@pytest.mark.anyio("asyncio")
async def test_qa_generate_uses_default_question_types(async_client, test_context, callback_recorder):
    test_context.rag.retrieve_result = _prepare_chunks()
    test_context.qa.events = [
        ("qa", "응용", {"type": "응용", "question": "응용Q", "answer": "응용A"}),
        ("qa", "비교", {"type": "비교", "question": "비교Q", "answer": "비교A"}),
    ]
    payload = {
        "lecture_id": 1,
        "summary_id": 1,
        "section_index": 0,
        "section_summary": "스택과 큐의 차이를 자세히 설명한다.",
        "callback_url": "http://example.com/qa",
    }
    response = await async_client.post("/qa/generate", json=payload)
    assert response.status_code == 202
    await asyncio.sleep(0.05)

    qa_request = test_context.qa.request_payloads[-1]
    assert qa_request.question_types == ["응용", "비교", "심화"]
    assert qa_request.qa_count == len(test_context.settings.qa.question_types)

    assert callback_recorder
    qna_types = []
    for payload in callback_recorder:
        qna_types.extend([item["type"] for item in payload["json"]["qnaList"]])
    assert qna_types == [QnAType.APPLICATION.value, QnAType.COMPARISON.value]


@pytest.mark.anyio("asyncio")
async def test_qa_generate_respects_question_types_override(async_client, test_context, callback_recorder):
    test_context.rag.retrieve_result = _prepare_chunks()
    test_context.qa.events = [
        ("qa", "개념", {"type": "개념", "question": "Q1", "answer": "A1"}),
        ("qa", "심화", {"type": "심화", "question": "Q2", "answer": "A2"}),
    ]
    payload = {
        "lecture_id": 2,
        "summary_id": 2,
        "section_index": 1,
        "section_summary": "자료구조 간의 비교와 차이를 서술한다.",
        "question_types": [QnAType.CONCEPT.value, QnAType.ADVANCED.value],
        "callback_url": "http://example.com/qa",
    }
    response = await async_client.post("/qa/generate", json=payload)
    assert response.status_code == 202
    await asyncio.sleep(0.05)

    qa_request = test_context.qa.request_payloads[-1]
    assert qa_request.question_types == ["개념", "심화"]
    assert qa_request.qa_count == 2

    qna_types = []
    for payload in callback_recorder:
        qna_types.extend([item["type"] for item in payload["json"]["qnaList"]])
    assert qna_types == [QnAType.CONCEPT.value, QnAType.ADVANCED.value]


@pytest.mark.anyio("asyncio")
async def test_qa_generate_rejects_invalid_enum(async_client):
    payload = {
        "lecture_id": 3,
        "summary_id": 3,
        "section_index": 2,
        "section_summary": "데이터 처리 파이프라인을 구성하는 방법을 다룬다.",
        "question_types": ["UNKNOWN"],
        "callback_url": "http://example.com/qa",
    }
    response = await async_client.post("/qa/generate", json=payload)
    assert response.status_code == 422


@pytest.mark.anyio("asyncio")
async def test_qa_generate_handles_rag_failure(async_client, test_context, monkeypatch):
    def raise_error(*args, **kwargs):
        raise RuntimeError("no collection")

    monkeypatch.setattr(test_context.rag, "retrieve", raise_error)
    payload = {
        "lecture_id": 4,
        "summary_id": 4,
        "section_index": 3,
        "section_summary": "심화 내용을 다루며 응용 예시를 제시한다.",
        "callback_url": "http://example.com/qa",
    }
    response = await async_client.post("/qa/generate", json=payload)
    assert response.status_code == 400
    assert "RAG" in response.json()["detail"]
