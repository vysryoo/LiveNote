from __future__ import annotations

import httpx
import pytest

from blog.blogkit.api.naver_client import NaverBlogSearchClient

pytestmark = pytest.mark.anyio("asyncio")


def _client(handler) -> NaverBlogSearchClient:
    return NaverBlogSearchClient("id", "secret", transport=httpx.MockTransport(handler))


@pytest.mark.anyio("asyncio")
async def test_search_sends_credentials_and_normalizes_items():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(200, json={"items": [{
            "title": "<b>스택</b>과 큐 정리 &amp; 예제",
            "link": "https://blog.naver.com/a/1",
            "description": "<b>스택</b>은 LIFO 구조입니다.",
            "bloggername": "개발노트",
            "bloggerlink": "blog.naver.com/a",
        }]})

    results = await _client(handler).search("스택 큐", num=5)

    request = captured["request"]
    assert request.url.host == "naverapihub.apigw.ntruss.com"
    assert request.headers["X-NCP-APIGW-API-KEY-ID"] == "id"
    assert request.headers["X-NCP-APIGW-API-KEY"] == "secret"
    assert request.url.params["query"] == "스택 큐"
    assert request.url.params["display"] == "5"
    assert results == [{
        "title": "스택과 큐 정리 & 예제",
        "link": "https://blog.naver.com/a/1",
        "snippet": "스택은 LIFO 구조입니다.",
        "displayLink": "개발노트",
    }]


@pytest.mark.anyio("asyncio")
async def test_search_returns_empty_list_on_error_status():
    results = await _client(lambda request: httpx.Response(401, json={"errorCode": "024"})).search("스택")

    assert results == []


@pytest.mark.anyio("asyncio")
async def test_search_returns_empty_list_on_network_error():
    def handler(request):
        raise httpx.ConnectError("unreachable")

    assert await _client(handler).search("스택") == []


def test_missing_credentials_are_rejected(monkeypatch):
    monkeypatch.setattr("blog.blogkit.config.google_config.GoogleConfig.NAVER_CLIENT_ID", "")
    with pytest.raises(ValueError):
        NaverBlogSearchClient(client_id=None, client_secret="secret")
