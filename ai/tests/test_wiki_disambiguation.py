from __future__ import annotations

import pytest

from recommend.providers.wiki import WikiProvider

pytestmark = pytest.mark.anyio("asyncio")


class _FakeWikiApi:
    def __init__(self, pages):
        self.pages = pages

    async def get_page_extract(self, page_id, lang):
        return dict(self.pages[page_id])


async def test_disambiguation_pages_are_excluded():
    provider = WikiProvider(
        top_k=1, verify=False, min_score=5.0, language="ko", wiki_lang="en", fallback_to_ko=False,
        api=_FakeWikiApi({
            1: {"title": "Stack", "extract": "Stack may refer to:", "pageid": 1, "disambiguation": True},
            2: {"title": "Stack (abstract data type)", "extract": "A stack is ...", "pageid": 2, "disambiguation": False},
        }),
    )

    pages = await provider.fetch_details([{"pageid": 1}, {"pageid": 2}], "en")

    assert [page["title"] for page in pages] == ["Stack (abstract data type)"]
