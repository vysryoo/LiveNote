from __future__ import annotations

import json
from typing import List, Tuple

import pytest

from tests.conftest import StubRetrievedChunk


async def collect_sse(response) -> List[Tuple[str, dict]]:
    events: List[Tuple[str, dict]] = []
    current = None
    async for line in response.aiter_lines():
        if not line:
            continue
        if line.startswith("event:"):
            current = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data = json.loads(line.split(":", 1)[1].strip())
            events.append((current, data))
    return events


def _prepare_chunks() -> List[StubRetrievedChunk]:
    return [
        StubRetrievedChunk(id="c1", text="스택은 LIFO 구조다.", score=0.91, metadata={"section_id": "1"}),
        StubRetrievedChunk(id="c2", text="큐는 FIFO 구조와 비교된다.", score=0.82, metadata={"section_id": "2"}),
    ]


@pytest.mark.anyio
async def test_qa_stream_orders_events(async_client, test_context):
    test_context.rag.retrieve_result = _prepare_chunks()
    test_context.qa.events = [
        ("qa", "응용", {"type": "응용", "question": "응용Q", "answer": "응용A", "_delay": 0.05}),
        ("qa", "비교", {"type": "비교", "question": "비교Q", "answer": "비교A", "_delay": 0.0}),
        ("qa", "심화", {"type": "심화", "question": "심화Q", "answer": "심화A", "_delay": 0.02}),
    ]
    payload = {"lecture_id": "lec", "section_id": 1, "section_summary": "스택과 큐의 차이를 자세히 설명한다."}
    async with async_client.stream("POST", "/qa/generate", json=payload) as response:
        assert response.status_code == 200
        events = await collect_sse(response)
    
    # 첫 이벤트는 컨텍스트 정보
    assert events[0][0] == "qa_context"
    partial = [evt for evt in events if evt[0] == "qa_partial"]
    order = [evt[1]["qa"]["type"] for evt in partial]
    assert order == ["비교", "심화", "응용"]
    assert test_context.rag.retrieve_calls[-1]["top_k"] == test_context.settings.rag.qa_retrieve_top_k


@pytest.mark.anyio
async def test_qa_stream_emits_error(async_client, test_context):
    test_context.rag.retrieve_result = _prepare_chunks()
    test_context.qa.events = [
        ("qa", "응용", {"type": "응용", "question": "Q1", "answer": "A1"}),
        ("error", "비교", {"error": "LLM 실패"}),
    ]
    payload = {"lecture_id": "lec", "section_id": 2, "section_summary": "자료구조 간의 비교와 차이를 서술한다."}
    async with async_client.stream("POST", "/qa/generate", json=payload) as response:
        assert response.status_code == 200
        events = await collect_sse(response)
    
    error_events = [evt for evt in events if evt[0] == "qa_error"]
    assert error_events
    assert error_events[0][1]["type"] == "비교"


@pytest.mark.anyio
async def test_qa_stream_reports_completion(async_client, test_context):
    test_context.rag.retrieve_result = _prepare_chunks()
    test_context.qa.events = [
        ("qa", "응용", {"type": "응용", "question": "Q1", "answer": "A1"}),
        ("qa", "비교", {"type": "비교", "question": "Q2", "answer": "A2"}),
        ("qa", "심화", {"type": "심화", "question": "Q3", "answer": "A3"}),
    ]
    payload = {"lecture_id": "lec", "section_id": 3, "section_summary": "심화 내용을 다루며 응용 예시를 제시한다."}
    async with async_client.stream("POST", "/qa/generate", json=payload) as response:
        events = await collect_sse(response)
    
    complete = [evt for evt in events if evt[0] == "qa_complete"]
    assert complete
    assert complete[0][1]["total"] == 3


@pytest.mark.anyio
async def test_qa_stream_builds_request_with_context(async_client, test_context):
    test_context.rag.retrieve_result = _prepare_chunks()
    test_context.qa.events = [
        ("qa", "응용", {"type": "응용", "question": "Q1", "answer": "A1"}),
    ]
    payload = {
        "lecture_id": "lec",
        "section_id": 4,
        "section_summary": "요약 내용을 충분히 제공하여 테스트를 진행한다.",
    }
    await async_client.post("/qa/generate", json=payload)
    stored = test_context.qa.request_payloads[-1]
    assert stored.qa_count == len(test_context.settings.qa.question_types)
    assert len(stored.rag_context.chunks) == len(test_context.rag.retrieve_result)


@pytest.mark.anyio
async def test_qa_stream_fails_when_rag_raises(async_client, test_context, monkeypatch):
    def raise_error(*args, **kwargs):
        raise RuntimeError("no collection")
    
    monkeypatch.setattr(test_context.rag, "retrieve", raise_error)
    payload = {
        "lecture_id": "lec",
        "section_id": 5,
        "section_summary": "데이터 처리 파이프라인을 구성하는 방법을 다룬다.",
    }
    response = await async_client.post("/qa/generate", json=payload)
    assert response.status_code == 400
    assert "RAG" in response.json()["detail"]
