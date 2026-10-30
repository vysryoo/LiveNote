import pytest
from httpx import ASGITransport, AsyncClient

from server.security import INTERNAL_API_KEY_HEADER, internal_auth_headers


async def _post_text_upsert(fastapi_app, headers):
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://testserver", headers=headers) as client:
        return await client.post("/rag/text-upsert", json={"lecture_id": "1", "items": [{"text": "a"}]})


@pytest.mark.anyio
async def test_rejects_request_without_key(fastapi_app):
    response = await _post_text_upsert(fastapi_app, {})
    assert response.status_code == 401


@pytest.mark.anyio
async def test_rejects_request_with_wrong_key(fastapi_app):
    response = await _post_text_upsert(fastapi_app, {INTERNAL_API_KEY_HEADER: "wrong"})
    assert response.status_code == 401


@pytest.mark.anyio
async def test_rejects_all_requests_when_server_key_missing(fastapi_app, test_context):
    test_context.settings.internal_api_key = ""
    response = await _post_text_upsert(fastapi_app, {INTERNAL_API_KEY_HEADER: ""})
    assert response.status_code == 401


@pytest.mark.anyio
async def test_health_is_open(fastapi_app):
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health")
    assert response.status_code == 200


def test_callback_headers_carry_key(test_context, internal_api_key):
    assert internal_auth_headers(test_context.settings) == {INTERNAL_API_KEY_HEADER: internal_api_key}
