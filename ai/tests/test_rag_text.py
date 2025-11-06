from __future__ import annotations

import pytest


@pytest.mark.anyio
async def test_text_upsert_success(async_client, test_context):
    payload = {
        "lecture_id": "lec-1",
        "items": [
            {"text": "요약문 1", "section_id": "1"},
            {"text": "요약문 2", "metadata": {"page": 2}},
        ],
    }
    response = await async_client.post("/rag/text-upsert", json=payload)
    assert response.status_code == 200
    assert test_context.rag.text_calls
    call = test_context.rag.text_calls[-1]
    assert call["collection_id"] == "test_lec-1"
    assert len(call["items"]) == 2


@pytest.mark.anyio
async def test_text_upsert_rejects_empty_items(async_client):
    payload = {"lecture_id": "lec-1", "items": []}
    response = await async_client.post("/rag/text-upsert", json=payload)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_text_upsert_requires_lecture(async_client):
    payload = {"lecture_id": "   ", "items": [{"text": "data"}]}
    response = await async_client.post("/rag/text-upsert", json=payload)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_text_upsert_preserves_metadata(async_client, test_context):
    payload = {
        "lecture_id": "lec-meta",
        "items": [
            {"text": "내용", "metadata": {"tag": "core"}},
        ],
    }
    await async_client.post("/rag/text-upsert", json=payload)
    call = test_context.rag.text_calls[-1]
    item = call["items"][0]
    assert item.metadata == {"tag": "core"}


@pytest.mark.anyio
async def test_text_upsert_returns_stub_result(async_client, test_context):
    payload = {"lecture_id": "lec-result", "items": [{"text": "내용"}]}
    response = await async_client.post("/rag/text-upsert", json=payload)
    assert response.status_code == 200
    assert response.json()["result"] == test_context.rag.upsert_text_result
