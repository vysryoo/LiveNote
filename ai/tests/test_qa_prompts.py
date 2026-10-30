"""
QnA 프롬프트 고정 테스트

QnA 생성 요청이 LLM에 보내는 메시지 전체를 스냅샷으로 비교한다.
"""
from __future__ import annotations

from typing import Any, Dict, List

import pytest
from httpx import ASGITransport, AsyncClient

from core.schemas import RAGChunk
from qa.service import QAService
from server.app import create_app
from tests.snapshots import assert_snapshot

pytestmark = pytest.mark.anyio("asyncio")

SUMMARY = "스택은 마지막에 넣은 원소를 먼저 꺼내는 LIFO 자료구조이고, 큐와 비교해 설명함"


@pytest.fixture
def llm_calls(monkeypatch) -> List[Dict[str, Any]]:
    calls: List[Dict[str, Any]] = []

    async def fake_stream(purpose, messages, max_tokens=None):
        calls.append({"purpose": purpose.value, "messages": [list(m) for m in messages], "max_tokens": max_tokens})
        yield "질문\n"
        yield "답변"

    monkeypatch.setattr("qa.service.stream", fake_stream)
    return calls


async def _generate(test_context, internal_api_key, body: Dict[str, Any]) -> None:
    app = create_app(
        test_context.settings,
        rag_service=test_context.rag,
        qa_service=QAService(),
        rec_service=test_context.rec,
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver", headers={"X-Internal-Api-Key": internal_api_key}
    ) as client:
        response = await client.post("/qa/generate", json=body)
    assert response.status_code == 200


@pytest.mark.parametrize("with_context", [True, False], ids=["context", "bare"])
async def test_qa_prompts(test_context, internal_api_key, llm_calls, with_context):
    body: Dict[str, Any] = {
        "lectureId": 1,
        "sectionIndex": 3,
        "sectionSummary": SUMMARY,
        "questionTypes": ["CONCEPT", "APPLICATION", "COMPARISON", "ADVANCED"],
    }
    test_context.settings.qa.qa_top_k = 4
    if with_context:
        test_context.rag.retrieve_result = [
            RAGChunk(id="c1", text="스택(Stack): push, pop 연산", score=0.71, metadata={}),
            RAGChunk(id="c2", text="큐(Queue): enqueue, dequeue", score=0.64, metadata={}),
            RAGChunk(id="c3", text="섹션 1 요약: 자료구조 수업 소개", score=0.52, metadata={}),
        ]
        body["subject"] = "자료구조"
        body["previousQa"] = [
            {"type": "CONCEPT", "question": "배열이란 무엇인가요?", "answer": "연속된 메모리에 저장하는 구조"},
            {"type": "개념", "question": "연결 리스트의 노드는?", "answer": "값과 포인터"},
        ]

    await _generate(test_context, internal_api_key, body)

    calls = sorted(llm_calls, key=lambda call: call["messages"][-1][1])
    assert_snapshot(f"qa_prompts_{'context' if with_context else 'bare'}", calls)
