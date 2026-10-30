from __future__ import annotations

import httpx
import pytest

from recommend.providers.video import YouTubeClient

pytestmark = pytest.mark.anyio("asyncio")


@pytest.mark.anyio("asyncio")
async def test_api_key_is_sent_in_header_not_url():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/search"):
            return httpx.Response(400, json={"error": {"message": "bad"}})
        return httpx.Response(200, json={"items": []})

    client = YouTubeClient("secret-key", transport=httpx.MockTransport(handler))

    with pytest.raises(httpx.HTTPStatusError) as error:
        await client.search_videos("stack", lang="ko", max_results=3)
    await client.get_videos(["abc"])

    assert "secret-key" not in str(error.value)
    for request in requests:
        assert "key" not in request.url.params
        assert request.headers["X-Goog-Api-Key"] == "secret-key"
