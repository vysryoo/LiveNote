from __future__ import annotations

import json
from typing import List, Tuple

import pytest

from core.schemas import QnAType, RAGChunk
from qa.models import QAEvent

pytestmark = pytest.mark.anyio("asyncio")


def _prepare_chunks() -> List[RAGChunk]:
    return [
        RAGChunk(id="c1", text="스택은 LIFO 구조다.", score=0.91, metadata={"section_id": "1"}),
        RAGChunk(id="c2", text="큐는 FIFO 구조와 비교된다.", score=0.82, metadata={"section_id": "2"}),
    ]


def _parse_sse(body: str) -> List[Tuple[str, dict]]:
    events = []
    for block in body.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.split("\n"))
        events.append((lines["event"], json.loads(lines["data"])))
    return events


def _qa_events(item: int, q_type: QnAType, question: str, answer_parts: List[str]) -> List[QAEvent]:
    events = [QAEvent("start", {"item": item, "type": q_type.value}), QAEvent("question", {"item": item, "text": question})]
    events += [QAEvent("answer", {"item": item, "text": part}) for part in answer_parts]
    events.append(QAEvent("done", {"item": item, "type": q_type.value, "question": question, "answer": "".join(answer_parts)}))
    return events


@pytest.mark.anyio("asyncio")
async def test_qa_generate_streams_events_as_sse(async_client, test_context):
    test_context.rag.retrieve_result = _prepare_chunks()
    test_context.qa.events = _qa_events(0, QnAType.APPLICATION, "응용Q", ["응용", "A"])
    payload = {
        "lecture_id": 1,
        "summary_id": 1,
        "section_index": 0,
        "section_summary": "스택과 큐의 차이를 자세히 설명한다.",
    }
    response = await async_client.post("/qa/generate", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert _parse_sse(response.text) == [
        ("start", {"item": 0, "type": QnAType.APPLICATION.value}),
        ("question", {"item": 0, "text": "응용Q"}),
        ("answer", {"item": 0, "text": "응용"}),
        ("answer", {"item": 0, "text": "A"}),
        ("done", {"item": 0, "type": QnAType.APPLICATION.value, "question": "응용Q", "answer": "응용A"}),
    ]


@pytest.mark.anyio("asyncio")
async def test_qa_generate_uses_default_question_types(async_client, test_context):
    test_context.rag.retrieve_result = _prepare_chunks()
    payload = {
        "lecture_id": 1,
        "summary_id": 1,
        "section_index": 0,
        "section_summary": "스택과 큐의 차이를 자세히 설명한다.",
    }
    await async_client.post("/qa/generate", json=payload)

    qa_request = test_context.qa.request_payloads[-1]
    assert qa_request.question_types == [QnAType.APPLICATION, QnAType.COMPARISON, QnAType.ADVANCED]


@pytest.mark.anyio("asyncio")
async def test_qa_generate_respects_question_types_override(async_client, test_context):
    test_context.rag.retrieve_result = _prepare_chunks()
    test_context.qa.events = _qa_events(0, QnAType.CONCEPT, "Q1", ["A1"]) + _qa_events(1, QnAType.ADVANCED, "Q2", ["A2"])
    payload = {
        "lecture_id": 2,
        "summary_id": 2,
        "section_index": 1,
        "section_summary": "자료구조 간의 비교와 차이를 서술한다.",
        "question_types": [QnAType.CONCEPT.value, QnAType.ADVANCED.value],
    }
    response = await async_client.post("/qa/generate", json=payload)

    qa_request = test_context.qa.request_payloads[-1]
    assert qa_request.question_types == [QnAType.CONCEPT, QnAType.ADVANCED]
    done_types = [data["type"] for event, data in _parse_sse(response.text) if event == "done"]
    assert done_types == [QnAType.CONCEPT.value, QnAType.ADVANCED.value]


@pytest.mark.anyio("asyncio")
async def test_qa_generate_reports_item_error(async_client, test_context):
    test_context.rag.retrieve_result = _prepare_chunks()
    test_context.qa.events = [
        QAEvent("start", {"item": 0, "type": "CONCEPT"}),
        QAEvent("error", {"item": 0, "message": "timeout"}),
    ]
    payload = {
        "lecture_id": 5,
        "section_index": 0,
        "section_summary": "스택과 큐의 차이를 자세히 설명한다.",
        "question_types": [QnAType.CONCEPT.value],
    }
    response = await async_client.post("/qa/generate", json=payload)

    assert _parse_sse(response.text)[-1] == ("error", {"item": 0, "message": "timeout"})


@pytest.mark.anyio("asyncio")
async def test_qa_generate_rejects_invalid_enum(async_client):
    payload = {
        "lecture_id": 3,
        "summary_id": 3,
        "section_index": 2,
        "section_summary": "데이터 처리 파이프라인을 구성하는 방법을 다룬다.",
        "question_types": ["UNKNOWN"],
    }
    response = await async_client.post("/qa/generate", json=payload)
    assert response.status_code == 422


@pytest.mark.anyio("asyncio")
async def test_qa_generate_handles_rag_failure(async_client, test_context, monkeypatch):
    def raise_error(*args, **kwargs):
        raise RuntimeError("no collection")

    monkeypatch.setattr(test_context.rag, "retrieve_context", raise_error)
    payload = {
        "lecture_id": 4,
        "summary_id": 4,
        "section_index": 3,
        "section_summary": "심화 내용을 다루며 응용 예시를 제시한다.",
    }
    response = await async_client.post("/qa/generate", json=payload)
    assert response.status_code == 400
    assert "RAG" in response.json()["detail"]


@pytest.mark.anyio("asyncio")
async def test_qa_generate_rejects_blank_summary(async_client):
    payload = {"lecture_id": 1, "section_index": 0, "section_summary": " " * 12}
    response = await async_client.post("/qa/generate", json=payload)
    assert response.status_code == 422
