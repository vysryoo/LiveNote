from __future__ import annotations

import asyncio
from typing import List, Tuple

import pytest

pytestmark = pytest.mark.anyio("asyncio")

from server.models import ResourceType
from tests.conftest import (
    GoogleResponse,
    GoogleSearchResult,
    OpenAlexResponse,
    PaperInfo,
    StubRetrievedChunk,
    WikiPageInfo,
    WikiResponse,
    YouTubeResponse,
    YouTubeVideoInfo,
)


def prepare_chunks() -> List[StubRetrievedChunk]:
    return [
        StubRetrievedChunk(id="c1", text="알고리즘 분석 내용", score=0.9, metadata={"section_id": "1"}),
        StubRetrievedChunk(id="c2", text="자료 구조 관련 설명", score=0.85, metadata={"section_id": "2"}),
    ]


def build_default_responses() -> Tuple[list, list, list, list]:
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
    google_items = [
        GoogleResponse(
            lecture_id="lec",
            section_id=1,
            search_result=GoogleSearchResult(
                url="http://example.com/blog",
                title="Blog 1",
                snippet="Snippet 1",
                display_link="example.com",
                lang="en",
            ),
            reason="검색 결과",
            score=6.0,
        )
    ]
    return openalex_items, wiki_items, yt_items, google_items


@pytest.mark.anyio("asyncio")
async def test_rec_recommend_defaults_use_all_providers(async_client, test_context, callback_recorder):
    test_context.rag.retrieve_result = prepare_chunks()
    oa_items, wiki_items, yt_items, google_items = build_default_responses()
    test_context.openalex.responses = oa_items
    test_context.wiki.responses = wiki_items
    test_context.youtube.responses = yt_items
    test_context.google.responses = google_items

    payload = {
        "lecture_id": 1,
        "summary_id": 10,
        "section_index": 0,
        "section_summary": "자료구조와 알고리즘을 설명하는 강의",
        "callback_url": "http://example.com/rec",
        "previous_summaries": [],
        "yt_exclude": ["old_video"],
        "wiki_exclude": ["old_wiki"],
        "paper_exclude": ["old_paper"],
        "google_exclude": ["http://old.example.com"],
    }
    response = await async_client.post("/rec/recommend", json=payload)
    assert response.status_code == 202
    await asyncio.sleep(0.05)

    assert test_context.openalex.requests and test_context.wiki.requests
    assert test_context.youtube.requests and test_context.google.requests
    assert test_context.openalex.requests[-1].exclude_ids == ["old_paper"]
    assert test_context.wiki.requests[-1].exclude_titles == ["old_wiki"]
    assert test_context.youtube.requests[-1].exclude_titles == ["old_video"]
    assert test_context.google.requests[-1].exclude_urls == ["http://old.example.com"]

    types = {item["json"]["resources"][0]["type"] for item in callback_recorder}
    assert types == {
        ResourceType.PAPER.value,
        ResourceType.WIKI.value,
        ResourceType.VIDEO.value,
        ResourceType.BLOG.value,
    }


@pytest.mark.anyio("asyncio")
async def test_rec_recommend_filters_by_resource_types(async_client, test_context, callback_recorder):
    test_context.rag.retrieve_result = prepare_chunks()
    _, wiki_items, yt_items, _ = build_default_responses()
    test_context.wiki.responses = wiki_items
    test_context.youtube.responses = yt_items

    payload = {
        "lecture_id": 2,
        "summary_id": 11,
        "section_index": 1,
        "section_summary": "최적화 전략을 제시하는 강의",
        "callback_url": "http://example.com/rec",
        "previous_summaries": [],
        "yt_exclude": ["skip video"],
        "wiki_exclude": ["skip wiki"],
        "paper_exclude": ["should_ignore"],
        "google_exclude": ["should_ignore"],
        "resource_types": [ResourceType.WIKI.value, ResourceType.VIDEO.value],
    }
    response = await async_client.post("/rec/recommend", json=payload)
    assert response.status_code == 202
    await asyncio.sleep(0.05)

    assert not test_context.openalex.requests
    assert not test_context.google.requests
    assert test_context.wiki.requests and test_context.youtube.requests
    assert test_context.wiki.requests[-1].exclude_titles == ["skip wiki"]
    assert test_context.youtube.requests[-1].exclude_titles == ["skip video"]

    types = {item["json"]["resources"][0]["type"] for item in callback_recorder}
    assert types == {ResourceType.WIKI.value, ResourceType.VIDEO.value}


@pytest.mark.anyio("asyncio")
async def test_rec_recommend_rejects_invalid_resource_type(async_client):
    payload = {
        "lecture_id": 3,
        "summary_id": 12,
        "section_index": 2,
        "section_summary": "네트워크 최적화 기법을 다룬다.",
        "callback_url": "http://example.com/rec",
        "previous_summaries": [],
        "resource_types": ["INVALID"],
    }
    response = await async_client.post("/rec/recommend", json=payload)
    assert response.status_code == 422


@pytest.mark.anyio("asyncio")
async def test_rec_recommend_handles_provider_failure(async_client, test_context, callback_recorder, monkeypatch):
    test_context.rag.retrieve_result = prepare_chunks()
    _, wiki_items, _, _ = build_default_responses()
    test_context.wiki.responses = wiki_items

    async def failing_openalex(request):
        raise RuntimeError("OpenAlex down")

    monkeypatch.setattr(test_context.openalex, "recommend_papers", failing_openalex)

    payload = {
        "lecture_id": 4,
        "summary_id": 13,
        "section_index": 3,
        "section_summary": "알고리즘 복잡도 분석",
        "callback_url": "http://example.com/rec",
        "previous_summaries": [],
        "resource_types": [ResourceType.PAPER.value, ResourceType.WIKI.value],
    }
    response = await async_client.post("/rec/recommend", json=payload)
    assert response.status_code == 202
    await asyncio.sleep(0.05)

    # 실패한 provider도 빈 리소스로 콜백하고, 다른 provider는 정상 응답
    types_by_payload = [res["json"]["resources"] for res in callback_recorder]
    assert any(payload == [] for payload in types_by_payload)
    assert any(
        resources and resources[0]["type"] == ResourceType.WIKI.value
        for resources in types_by_payload
    )


@pytest.mark.anyio("asyncio")
async def test_rec_recommend_requires_rag(async_client, test_context, monkeypatch):
    def raise_error(*args, **kwargs):
        raise RuntimeError("rag failure")

    monkeypatch.setattr(test_context.rag, "retrieve", raise_error)
    payload = {
        "lecture_id": 5,
        "summary_id": 14,
        "section_index": 4,
        "section_summary": "네트워크 최적화 기법을 다룬다.",
        "callback_url": "http://example.com/rec",
        "previous_summaries": [],
    }
    response = await async_client.post("/rec/recommend", json=payload)
    assert response.status_code == 400
    assert "RAG" in response.json()["detail"]
