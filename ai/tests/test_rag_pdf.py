from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.mark.anyio
async def test_pdf_upsert_success(async_client, test_context):
    pdf_path = Path("cap1_RAG_module/test_data/simple_test.pdf")
    payload = pdf_path.read_bytes()
    response = await async_client.post(
        "/rag/pdf-upsert",
        files={"file": ("simple_test.pdf", payload, "application/pdf")},
        data={"lecture_id": "lecture123", "base_metadata": json.dumps({"subject": "cs"})},
    )
    assert response.status_code == 200
    assert test_context.rag.pdf_calls
    call = test_context.rag.pdf_calls[-1]
    assert call["collection_id"] == "test_lecture123"
    assert call["base_metadata"] == {"subject": "cs"}
    assert Path(call["pdf_path"]).exists()


@pytest.mark.anyio
async def test_pdf_upsert_rejects_non_pdf(async_client):
    response = await async_client.post(
        "/rag/pdf-upsert",
        files={"file": ("notes.txt", b"text", "text/plain")},
        data={"lecture_id": "lecture123"},
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


@pytest.mark.anyio
async def test_pdf_upsert_blocks_empty_file(async_client):
    response = await async_client.post(
        "/rag/pdf-upsert",
        files={"file": ("empty.pdf", b"", "application/pdf")},
        data={"lecture_id": "lecture123"},
    )
    assert response.status_code == 400
    assert "빈 파일" in response.json()["detail"]


@pytest.mark.anyio
async def test_pdf_upsert_invalid_metadata(async_client):
    pdf_path = Path("cap1_RAG_module/test_data/simple_test.pdf")
    response = await async_client.post(
        "/rag/pdf-upsert",
        files={"file": ("simple_test.pdf", pdf_path.read_bytes(), "application/pdf")},
        data={"lecture_id": "lecture123", "base_metadata": "{not-json}"},
    )
    assert response.status_code == 400
    assert "JSON" in response.json()["detail"]


@pytest.mark.anyio
async def test_pdf_upsert_blank_lecture_id(async_client):
    pdf_path = Path("cap1_RAG_module/test_data/simple_test.pdf")
    response = await async_client.post(
        "/rag/pdf-upsert",
        files={"file": ("simple_test.pdf", pdf_path.read_bytes(), "application/pdf")},
        data={"lecture_id": "   "},
    )
    assert response.status_code == 400
    assert "lecture_id" in response.json()["detail"]
