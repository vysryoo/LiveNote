from __future__ import annotations

import json
from typing import List, Tuple

import pytest

from tests.conftest import (
    OpenAlexResponse,
    PaperInfo,
    StubRetrievedChunk,
    WikiPageInfo,
    WikiResponse,
    YouTubeResponse,
    YouTubeVideoInfo,
)


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


def prepare_chunks():
    return [
        StubRetrievedChunk(id="c1", text="알고리즘 분석 내용", score=0.9, metadata={"section_id": "1"}),
        StubRetrievedChunk(id="c2", text="자료 구조 관련 설명", score=0.85, metadata={"section_id": "2"}),
        StubRetrievedChunk(id="c3", text="성능 최적화 사례", score=0.8, metadata={"section_id": "3"}),
    ]


def build_default_responses():
    openalex_items = [
        OpenAlexResponse(
            lecture_id="lec",
            section_id=1,
            paper_info=PaperInfo(
                url="http://example.com/paper1",
                title="Paper 1",
                abstract="Abstract 1",
                year=2024,
                cited_by_count=100,
                authors=["Alice"],
            ),
            reason="LLM 검증",
            score=7.5,
        )
    ]
    wiki_items = [
        WikiResponse(
            lecture_id="lec",
            section_id=1,
            page_info=WikiPageInfo(
                url="http://example.com/wiki1",
                title="Wiki 1",
                extract="Extract 1",
                lang="en",
                page_id=1,
            ),
            reason="관련 키워드",
            score=6.8,
        )
    ]
    yt_items = [
        YouTubeResponse(
            lecture_id="lec",
            section_id=1,
            video_info=YouTubeVideoInfo(
                url="http://youtu.be/1",
                title="Video 1",
                extract="Extract 1",
                lang="en",
            ),
            reason="LLM verification",
            score=7.2,
        )
    ]
    return openalex_items, wiki_items, yt_items


@pytest.mark.anyio
async def test_rec_stream_orders_partial_events(async_client, test_context):
    test_context.rag.retrieve_result = prepare_chunks()
    oa_items, wiki_items, yt_items = build_default_responses()
    test_context.openalex.responses = oa_items
    test_context.wiki.responses = wiki_items
    test_context.youtube.responses = yt_items
    test_context.openalex.delay = 0.03
    test_context.wiki.delay = 0.0
    test_context.youtube.delay = 0.01
    
    payload = {
        "lecture_id": "lec",
        "section_id": 1,
        "section_summary": "자료구조와 알고리즘을 설명하는 강의",
        "previous_summaries": [
            {"section_id": 1, "summary": "스택 소개", "timestamp": 111},
            {"section_id": 2, "summary": "큐 소개", "timestamp": 222},
        ],
        "yt_exclude": [],
        "wiki_exclude": [],
        "paper_exclude": [],
    }
    async with async_client.stream("POST", "/rec/recommend", json=payload) as response:
        assert response.status_code == 200
        events = await collect_sse(response)
    
    assert events[0][0] == "rec_context"
    partial_events = [evt for evt in events if evt[0] == "rec_partial"]
    sources = [evt[1]["source"] for evt in partial_events]
    assert sources == ["wiki", "youtube", "openalex"]
    assert test_context.rag.retrieve_calls[-1]["top_k"] == test_context.settings.rag.rec_retrieve_top_k


@pytest.mark.anyio
async def test_rec_stream_returns_complete(async_client, test_context):
    test_context.rag.retrieve_result = prepare_chunks()
    oa_items, wiki_items, yt_items = build_default_responses()
    test_context.openalex.responses = oa_items
    test_context.wiki.responses = wiki_items
    test_context.youtube.responses = yt_items
    
    payload = {
        "lecture_id": "lec",
        "section_id": 3,
        "section_summary": "최적화 전략을 제시하는 강의",
        "previous_summaries": [],
        "yt_exclude": [],
        "wiki_exclude": [],
        "paper_exclude": [],
    }
    async with async_client.stream("POST", "/rec/recommend", json=payload) as response:
        events = await collect_sse(response)
    
    complete = [evt for evt in events if evt[0] == "rec_complete"]
    assert complete
    assert complete[0][1]["completed_sources"] == 3


@pytest.mark.anyio
async def test_rec_stream_handles_errors(async_client, test_context, monkeypatch):
    test_context.rag.retrieve_result = prepare_chunks()
    
    async def failing_openalex(request):
        raise RuntimeError("OpenAlex down")
    
    monkeypatch.setattr(test_context.openalex, "recommend_papers", failing_openalex)
    oa_items, wiki_items, yt_items = build_default_responses()
    test_context.wiki.responses = wiki_items
    test_context.youtube.responses = yt_items
    
    payload = {
        "lecture_id": "lec",
        "section_id": 4,
        "section_summary": "알고리즘 복잡도 분석",
        "previous_summaries": [],
        "yt_exclude": [],
        "wiki_exclude": [],
        "paper_exclude": [],
    }
    async with async_client.stream("POST", "/rec/recommend", json=payload) as response:
        events = await collect_sse(response)
    errors = [evt for evt in events if evt[0] == "rec_error"]
    assert errors
    assert errors[0][1]["source"] == "openalex"


@pytest.mark.anyio
async def test_rec_stream_applies_config(async_client, test_context):
    test_context.rag.retrieve_result = prepare_chunks()
    oa_items, wiki_items, yt_items = build_default_responses()
    test_context.openalex.responses = oa_items
    test_context.wiki.responses = wiki_items
    test_context.youtube.responses = yt_items
    
    payload = {
        "lecture_id": "lec",
        "section_id": 5,
        "section_summary": "데이터 시각화와 분석을 다룬다.",
        "previous_summaries": [
            {"section_id": 3, "summary": "이전 요약"},
        ],
        "yt_exclude": ["Old video"],
        "wiki_exclude": ["Old wiki"],
        "paper_exclude": ["old-id"],
    }
    await async_client.post("/rec/recommend", json=payload)
    oa_request = test_context.openalex.requests[-1]
    wiki_request = test_context.wiki.requests[-1]
    yt_request = test_context.youtube.requests[-1]
    
    assert oa_request.top_k == test_context.settings.rec.openalex.top_k
    assert oa_request.sort_by == "hybrid"
    assert wiki_request.verify_wiki == test_context.settings.rec.wiki.verify
    assert wiki_request.wiki_lang == "en"
    assert yt_request.verify_yt == test_context.settings.rec.youtube.verify
    assert yt_request.yt_lang == "en"
    assert oa_request.exclude_ids == ["old-id"]
    assert wiki_request.exclude_titles == ["Old wiki"]
    assert yt_request.exclude_titles == ["Old video"]


@pytest.mark.anyio
async def test_rec_stream_requires_rag(async_client, test_context, monkeypatch):
    def raise_error(*args, **kwargs):
        raise RuntimeError("rag failure")
    
    monkeypatch.setattr(test_context.rag, "retrieve", raise_error)
    payload = {
        "lecture_id": "lec",
        "section_id": 6,
        "section_summary": "네트워크 최적화 기법을 다룬다.",
        "previous_summaries": [],
        "yt_exclude": [],
        "wiki_exclude": [],
        "paper_exclude": [],
    }
    response = await async_client.post("/rec/recommend", json=payload)
    assert response.status_code == 400
    assert "RAG" in response.json()["detail"]
