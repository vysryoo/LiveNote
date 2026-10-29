from __future__ import annotations

import pytest

from wiki.wikikit.service import WikiService

pytestmark = pytest.mark.anyio("asyncio")


class _FakeWikiApi:
    def __init__(self, pages):
        self.pages = pages

    async def get_page_extract(self, page_id, lang):
        return dict(self.pages[page_id])


@pytest.mark.anyio("asyncio")
async def test_disambiguation_pages_are_excluded():
    service = WikiService()
    service.api_client = _FakeWikiApi({
        1: {"title": "Stack", "extract": "Stack may refer to:", "pageid": 1, "disambiguation": True},
        2: {"title": "Stack (abstract data type)", "extract": "A stack is ...", "pageid": 2, "disambiguation": False},
    })

    pages = await service._fetch_details_parallel([{"pageid": 1}, {"pageid": 2}], "en")

    assert [page["title"] for page in pages] == ["Stack (abstract data type)"]
