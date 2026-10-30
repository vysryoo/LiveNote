from __future__ import annotations

import asyncio
from typing import List

import pytest

from core.schemas import RAGChunk, ResourceType
from recommend.models import Recommendation

pytestmark = pytest.mark.anyio("asyncio")


def prepare_chunks() -> List[RAGChunk]:
    return [
        RAGChunk(id="c1", text="알고리즘 분석 내용", score=0.9, metadata={"section_id": "1"}),
        RAGChunk(id="c2", text="자료 구조 관련 설명", score=0.85, metadata={"section_id": "2"}),
    ]


def _recommendation(resource_type: ResourceType) -> Recommendation:
    name = resource_type.value.lower()
    return Recommendation(
        type=resource_type,
        title=f"{name} 1",
        url=f"http://example.com/{name}",
        description=f"{name} 설명",
        score=7.0,
        reason="관련 개념",
        detail={"url": f"http://example.com/{name}"},
    )


def set_default_results(test_context, resource_types=tuple(ResourceType)) -> None:
    test_context.rec.results = {t: [_recommendation(t)] for t in resource_types}


@pytest.mark.anyio("asyncio")
async def test_rec_recommend_defaults_use_all_providers(async_client, test_context, callback_recorder):
    test_context.rag.retrieve_result = prepare_chunks()
    set_default_results(test_context)

    payload = {
        "lecture_id": 1,
        "summary_id": 10,
        "section_index": 0,
        "section_summary": "자료구조와 알고리즘을 설명하는 강의",
        "callback_url": "http://example.com/rec",
        "previous_summaries": [{"section_index": 0, "summary": "이전 섹션 요약"}],
        "yt_exclude": ["old_video"],
        "wiki_exclude": ["old_wiki"],
        "paper_exclude": ["old_paper"],
        "google_exclude": ["http://old.example.com"],
    }
    response = await async_client.post("/rec/recommend", json=payload)
    assert response.status_code == 202
    await asyncio.sleep(0.05)

    contexts = dict(test_context.rec.calls)
    assert set(contexts) == set(ResourceType)
    context = contexts[ResourceType.PAPER]
    assert context.summary == "자료구조와 알고리즘을 설명하는 강의"
    assert context.rag_chunks == prepare_chunks()
    assert [(p.section_id, p.summary) for p in context.previous_summaries] == [(1, "이전 섹션 요약")]
    assert context.excludes == {
        ResourceType.PAPER: ["old_paper"],
        ResourceType.WIKI: ["old_wiki"],
        ResourceType.VIDEO: ["old_video"],
        ResourceType.BLOG: ["http://old.example.com"],
    }

    callbacks = {item["json"]["resources"][0]["type"]: item["json"] for item in callback_recorder}
    assert set(callbacks) == {t.value for t in ResourceType}
    assert callbacks["WIKI"] == {
        "lectureId": 1,
        "summaryId": 10,
        "sectionIndex": 0,
        "resources": [_recommendation(ResourceType.WIKI).to_resource()],
    }


@pytest.mark.anyio("asyncio")
async def test_rec_recommend_filters_by_resource_types(async_client, test_context, callback_recorder):
    test_context.rag.retrieve_result = prepare_chunks()
    set_default_results(test_context)

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

    assert {t for t, _ in test_context.rec.calls} == {ResourceType.WIKI, ResourceType.VIDEO}

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
    set_default_results(test_context, [ResourceType.WIKI])
    test_context.rec.failures[ResourceType.PAPER] = RuntimeError("OpenAlex down")

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

    monkeypatch.setattr(test_context.rag, "retrieve_context", raise_error)
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
