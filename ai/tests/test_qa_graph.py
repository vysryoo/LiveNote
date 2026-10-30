from __future__ import annotations

import asyncio

import pytest

from core.schemas import QnAType
from qa.graph import build_qa_graph
from qa.models import QAEvent

pytestmark = pytest.mark.anyio("asyncio")


class FakeClient:
    """프롬프트별로 정해 둔 조각을 지연을 두고 내준다. 'fail'이면 예외를 낸다."""

    def __init__(self, outputs: dict[str, list[str]], delay: float = 0.01):
        self.outputs = outputs
        self.delay = delay
        self.cancelled: list[str] = []

    async def stream_text(self, prompt: str):
        if prompt == "fail":
            raise RuntimeError("호출 실패")
        try:
            for delta in self.outputs[prompt]:
                await asyncio.sleep(self.delay)
                yield delta
        except asyncio.CancelledError:
            self.cancelled.append(prompt)
            raise


async def _collect(graph, items):
    return [event async for event in graph.astream({"items": items}, stream_mode="custom")]


CONCEPT, APPLICATION = QnAType.CONCEPT, QnAType.APPLICATION


async def test_items_stream_concurrently_and_complete():
    client = FakeClient({
        "p0": ["질문A\n", "답", "변A"],
        "p1": ["질문B\n", "답변B"],
    })

    events = await _collect(build_qa_graph(client.stream_text), [(CONCEPT, "p0"), (APPLICATION, "p1")])

    done = {e.data["item"]: e.data for e in events if e.name == "done"}
    assert done[0] == {"item": 0, "type": "CONCEPT", "question": "질문A", "answer": "답변A"}
    assert done[1] == {"item": 1, "type": "APPLICATION", "question": "질문B", "answer": "답변B"}
    # 두 항목이 동시에 생성되므로 item 1의 질문이 item 0 완료보다 먼저 도착함
    kinds = [(e.name, e.data["item"]) for e in events]
    assert kinds.index(("question", 1)) < kinds.index(("done", 0))
    assert [e for e in events if e.data["item"] == 0][0] == QAEvent("start", {"item": 0, "type": "CONCEPT"})


async def test_failed_item_reports_error_and_others_continue():
    client = FakeClient({"ok": ["질문\n", "답변"]})

    events = await _collect(build_qa_graph(client.stream_text), [(CONCEPT, "fail"), (APPLICATION, "ok")])

    assert QAEvent("error", {"item": 0, "message": "호출 실패"}) in events
    assert any(e.name == "done" and e.data["item"] == 1 for e in events)
    assert not any(e.name == "done" and e.data["item"] == 0 for e in events)


async def test_empty_answer_is_reported_as_error():
    client = FakeClient({"p": ["질문만\n"]})

    events = await _collect(build_qa_graph(client.stream_text), [(CONCEPT, "p")])

    assert events[-1] == QAEvent("error", {"item": 0, "message": "질문 또는 답변이 비어 있음"})


async def test_closing_stream_cancels_remaining_generation():
    client = FakeClient({"fast": ["질문\n", "답변"], "slow": ["질문\n"] + ["조각"] * 50}, delay=0.02)
    stream = build_qa_graph(client.stream_text).astream(
        {"items": [(CONCEPT, "fast"), (APPLICATION, "slow")]}, stream_mode="custom"
    )

    async for event in stream:
        if event.name == "done":
            break
    await stream.aclose()
    await asyncio.sleep(0.05)

    assert client.cancelled == ["slow"]
