from __future__ import annotations

import asyncio

import pytest

from qa.qakit.graph import build_qa_graph

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


async def test_items_stream_concurrently_and_complete():
    client = FakeClient({
        "p0": ["질문A\n", "답", "변A"],
        "p1": ["질문B\n", "답변B"],
    })

    events = await _collect(build_qa_graph(client), [("개념", "p0"), ("응용", "p1")])

    done = {payload["item"]: payload for kind, _, payload in events if kind == "qa"}
    assert done[0] == {"item": 0, "type": "개념", "question": "질문A", "answer": "답변A"}
    assert done[1] == {"item": 1, "type": "응용", "question": "질문B", "answer": "답변B"}
    # 두 항목이 동시에 생성되므로 item 1의 질문이 item 0 완료보다 먼저 도착함
    kinds = [(kind, payload["item"]) for kind, _, payload in events]
    assert kinds.index(("question", 1)) < kinds.index(("qa", 0))
    assert [kind for kind, _, payload in events if payload["item"] == 0][0] == "start"


async def test_failed_item_reports_error_and_others_continue():
    client = FakeClient({"ok": ["질문\n", "답변"]})

    events = await _collect(build_qa_graph(client), [("개념", "fail"), ("응용", "ok")])

    assert ("error", "개념", {"item": 0, "error": "호출 실패"}) in events
    assert any(kind == "qa" and payload["item"] == 1 for kind, _, payload in events)
    assert not any(kind == "qa" and payload["item"] == 0 for kind, _, payload in events)


async def test_empty_answer_is_reported_as_error():
    client = FakeClient({"p": ["질문만\n"]})

    events = await _collect(build_qa_graph(client), [("개념", "p")])

    assert events[-1] == ("error", "개념", {"item": 0, "error": "질문 또는 답변이 비어 있음"})


async def test_closing_stream_cancels_remaining_generation():
    client = FakeClient({"fast": ["질문\n", "답변"], "slow": ["질문\n"] + ["조각"] * 50}, delay=0.02)
    stream = build_qa_graph(client).astream({"items": [("개념", "fast"), ("응용", "slow")]}, stream_mode="custom")

    async for kind, _, payload in stream:
        if kind == "qa":
            break
    await stream.aclose()
    await asyncio.sleep(0.05)

    assert client.cancelled == ["slow"]
