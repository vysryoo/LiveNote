from __future__ import annotations

import httpx
import pytest

from youtube_module.youtubekit.api.youtube_client import YouTubeAPIClient

pytestmark = pytest.mark.anyio("asyncio")


@pytest.mark.anyio("asyncio")
async def test_api_key_is_sent_in_header_not_url(monkeypatch):
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/search"):
            return httpx.Response(400, json={"error": {"message": "bad"}})
        return httpx.Response(200, json={"items": []})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs))
    client = YouTubeAPIClient(api_key="secret-key")

    with pytest.raises(httpx.HTTPStatusError) as error:
        await client.search_videos("stack", lang="ko", max_results=3)
    await client.get_videos(["abc"])

    assert "secret-key" not in str(error.value)
    for request in requests:
        assert "key" not in request.url.params
        assert request.headers["X-Goog-Api-Key"] == "secret-key"
