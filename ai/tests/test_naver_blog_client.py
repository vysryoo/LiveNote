from __future__ import annotations

import httpx
import pytest

from recommend.providers.blog import BlogProvider, NaverBlogClient

pytestmark = pytest.mark.anyio("asyncio")


def _client(handler) -> NaverBlogClient:
    return NaverBlogClient("id", "secret", transport=httpx.MockTransport(handler))


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


def test_missing_credentials_are_rejected():
    with pytest.raises(ValueError):
        NaverBlogClient(client_id="", client_secret="secret")


async def test_search_shortening_drops_last_word_until_results():
    class StubClient:
        def __init__(self):
            self.queries = []

        async def search(self, query, lang, num):
            self.queries.append(query)
            return [{"title": "결과"}] if query == "벅 컨버터" else []

    api = StubClient()
    provider = BlogProvider(top_k=1, verify=True, min_score=3.0, language="ko", search_lang="ko", api=api)

    results = await provider.search_shortening("벅 컨버터 전압초평형 듀티비")

    assert results == [{"title": "결과"}]
    assert api.queries == ["벅 컨버터 전압초평형 듀티비", "벅 컨버터 전압초평형", "벅 컨버터"]
