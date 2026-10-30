from __future__ import annotations

import pytest

from core.config import WikiSettings
from recommend.providers.wiki import WikiPage, WikiProvider, WikiSearchHit

pytestmark = pytest.mark.anyio("asyncio")


class _FakeWikiApi:
    def __init__(self, pages):
        self.pages = pages

    async def get_page_extract(self, page_id, lang):
        return self.pages[page_id]


async def test_disambiguation_pages_are_excluded():
    provider = WikiProvider(
        WikiSettings(top_k=1, verify=False, min_score=5.0, language="ko", search_lang="en", fallback_to_other_lang=False),
        api=_FakeWikiApi({
            1: WikiPage(page_id=1, title="Stack", extract="Stack may refer to:", url="", disambiguation=True),
            2: WikiPage(page_id=2, title="Stack (abstract data type)", extract="A stack is ...", url="", disambiguation=False),
        }),
    )

    pages = await provider.fetch_details(
        [WikiSearchHit(page_id=1, title="Stack", snippet=""), WikiSearchHit(page_id=2, title="Stack (abstract data type)", snippet="")],
        "en",
    )

    assert [page.title for page in pages] == ["Stack (abstract data type)"]
