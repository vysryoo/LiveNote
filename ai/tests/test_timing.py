from __future__ import annotations

import json
import logging
from typing import List

import pytest

from core.schemas import RAGChunk
from core.timing import RequestTimer, logger as timing_logger


class _RecordCollector(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records: List[dict] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(json.loads(record.getMessage()))


@pytest.fixture
def timing_records():
    collector = _RecordCollector()
    timing_logger.addHandler(collector)
    yield collector.records
    timing_logger.removeHandler(collector)


def test_mark_writes_stage_with_context(timing_records):
    timer = RequestTimer("qa", lecture_id=7)

    timer.mark("received", chunks=2)

    record = timing_records[-1]
    assert record["event"] == "timing"
    assert record["kind"] == "qa"
    assert record["stage"] == "received"
    assert record["lecture_id"] == 7
    assert record["chunks"] == 2
    assert record["request_id"] == timer.request_id
    assert record["elapsed_ms"] >= 0


def test_mark_once_records_first_occurrence_per_key(timing_records):
    timer = RequestTimer("qa")

    timer.mark_once("item_first_answer", key=0, item=0)
    timer.mark_once("item_first_answer", key=0, item=0)
    timer.mark_once("item_first_answer", key=1, item=1)

    assert [r["item"] for r in timing_records] == [0, 1]


@pytest.mark.anyio("asyncio")
async def test_qa_generate_records_streaming_stages(async_client, test_context, timing_records):
    test_context.rag.retrieve_result = [RAGChunk(id="c1", text="스택", score=0.9, metadata={})]
    test_context.qa.events = [
        ("start", "개념", {"item": 0}),
        ("question", "개념", {"item": 0, "text": "Q"}),
        ("answer", "개념", {"item": 0, "text": "A"}),
        ("answer", "개념", {"item": 0, "text": "B"}),
        ("qa", "개념", {"item": 0, "type": "개념", "question": "Q", "answer": "AB"}),
    ]
    payload = {
        "lecture_id": 1,
        "section_index": 0,
        "section_summary": "스택과 큐의 차이를 자세히 설명한다.",
        "question_types": ["CONCEPT"],
    }

    await async_client.post("/qa/generate", json=payload)

    qa_records = [r for r in timing_records if r["kind"] == "qa"]
    assert [r["stage"] for r in qa_records] == [
        "received", "retrieved", "item_start", "item_question", "item_first_answer", "item_done", "completed",
    ]
    assert len({r["request_id"] for r in qa_records}) == 1
