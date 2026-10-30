from __future__ import annotations

import httpx
import pytest

from recommend.providers import wiki as wiki_client
from recommend.providers.wiki import WikiClient, retry_wait_seconds

pytestmark = pytest.mark.anyio("asyncio")

SEARCH_BODY = {"query": {"search": [{"title": "Buck converter", "pageid": 1, "snippet": ""}]}}


@pytest.fixture
def waits(monkeypatch):
    recorded = []

    async def fake_sleep(seconds):
        recorded.append(seconds)

    monkeypatch.setattr(wiki_client.asyncio, "sleep", fake_sleep)
    return recorded


def _client(statuses):
    calls = []

    def handler(request):
        calls.append(request)
        status = statuses[min(len(calls) - 1, len(statuses) - 1)]
        headers = {"Retry-After": "3"} if status == 429 else {}
        return httpx.Response(status, json=SEARCH_BODY if status == 200 else {}, headers=headers)

    return WikiClient("LiveNote-test", transport=httpx.MockTransport(handler)), calls


async def test_search_retries_after_429_and_respects_retry_after(waits):
    client, calls = _client([429, 429, 200])

    results = await client.search_pages("Buck converter", lang="en", limit=3)

    assert [r["title"] for r in results] == ["Buck converter"]
    assert len(calls) == 3
    assert waits == [3.0, 3.0]


async def test_search_gives_up_after_max_retries(waits):
    client, calls = _client([429])

    assert await client.search_pages("Buck converter", lang="en") == []
    assert len(calls) == wiki_client.MAX_RETRIES + 1


async def test_other_errors_are_not_retried(waits):
    client, calls = _client([404])

    assert await client.search_pages("x", lang="en") == []
    assert len(calls) == 1
    assert waits == []


def test_retry_wait_uses_backoff_without_header_and_caps_wait():
    request = httpx.Request("GET", "https://en.wikipedia.org")

    assert retry_wait_seconds(httpx.Response(429, request=request), attempt=1) == 1.0
    assert retry_wait_seconds(httpx.Response(429, request=request), attempt=3) == 4.0
    assert retry_wait_seconds(httpx.Response(429, headers={"Retry-After": "120"}, request=request), attempt=1) == 10.0
