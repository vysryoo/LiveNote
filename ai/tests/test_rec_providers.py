"""
자료 추천 공급자 동작 고정 테스트

검색 API와 LLM을 가짜로 바꾼 시나리오에서 콜백으로 나가는 추천 결과와 LLM에 보낸 프롬프트를 스냅샷으로 비교한다.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Dict, List

import pytest

from core.llm import ModelPurpose
from core.schemas import PreviousSummary, RAGChunk, ResourceType
from server.routes.rec import map_resources
from tests.snapshots import assert_snapshot

pytestmark = pytest.mark.anyio("asyncio")

SUMMARY = "스택은 마지막에 넣은 원소를 먼저 꺼내는 LIFO 자료구조이고, 큐와 비교해 설명함"
PREVIOUS = [
    PreviousSummary(section_id=1, summary="자료구조 수업 소개와 배열 복습"),
    PreviousSummary(section_id=2, summary="연결 리스트의 노드와 포인터 구조"),
    PreviousSummary(section_id=3, summary="연결 리스트 삽입과 삭제의 시간 복잡도"),
]
RAG = [
    RAGChunk(text="스택(Stack): push, pop 연산. 함수 호출 스택 예시", score=0.71, metadata={"source_type": "pdf"}),
    RAGChunk(text="큐(Queue): enqueue, dequeue. 프린터 대기열 예시", score=0.64, metadata={"source_type": "pdf"}),
    RAGChunk(text="섹션 1 요약: 자료구조 수업 소개", score=0.52, metadata={"source_type": "summary"}),
]

Handler = Callable[[str], str]


class FakeLLM:
    """프롬프트를 기록하고, 시나리오 함수가 정한 응답을 돌려준다. 응답이 예외면 그 예외를 낸다."""

    def __init__(self, handler: Handler) -> None:
        self.handler = handler
        self.calls: List[Dict[str, Any]] = []

    async def complete(self, purpose: ModelPurpose, messages, max_tokens=None, json_mode=False) -> str:
        self.calls.append({"purpose": purpose.value, "messages": [list(m) for m in messages], "max_tokens": max_tokens})
        return self.handler(messages[-1][1])

    def sorted_calls(self) -> List[Dict[str, Any]]:
        return sorted(self.calls, key=lambda call: json.dumps(call, ensure_ascii=False, sort_keys=True))


def install_llm(monkeypatch, module: str, handler: Handler) -> FakeLLM:
    fake = FakeLLM(handler)
    monkeypatch.setattr(f"{module}.complete", fake.complete)
    return fake


def fail(message: str):
    raise RuntimeError(message)


@pytest.fixture(autouse=True)
def provider_keys(monkeypatch):
    """공급자 설정이 import 시점에 읽은 키를 테스트 값으로 채운다."""
    from blog.blogkit.config.google_config import GoogleConfig
    from openalex.openalexkit.config.openalex_config import OpenAlexConfig
    from wiki.wikikit.config.wiki_config import WikiConfig
    from youtube.youtubekit.config.youtube_config import YouTubeConfig

    for config in (OpenAlexConfig, WikiConfig, YouTubeConfig, GoogleConfig):
        monkeypatch.setattr(config, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(YouTubeConfig, "YOUTUBE_API_KEY", "yt-test")
    monkeypatch.setattr(YouTubeConfig, "OFFLINE_MODE", False)
    monkeypatch.setattr(GoogleConfig, "NAVER_CLIENT_ID", "naver-id")
    monkeypatch.setattr(GoogleConfig, "NAVER_CLIENT_SECRET", "naver-secret")


# 논문

PAPERS = [
    {"id": "W1", "title": "Stack machines and LIFO evaluation", "abstract": "We study stack based evaluation.",
     "year": 2001, "cited_by_count": 500, "url": "https://doi.org/10.1/a", "authors": ["Kim"], "relevance_score": 30.0},
    {"id": "W2", "title": "Stack machines (reprint)", "abstract": "Reprint.",
     "year": 2003, "cited_by_count": 10, "url": "https://doi.org/10.1/a", "authors": [], "relevance_score": 10.0},
    {"id": "W3", "title": "Queueing theory basics", "abstract": "Queue models in networks.",
     "year": 1990, "cited_by_count": 900, "url": "https://doi.org/10.1/c", "authors": ["Lee"], "relevance_score": 20.0},
    {"id": "W4", "title": "Array based stack implementation", "abstract": "An array stack.",
     "year": 2010, "cited_by_count": 40, "url": "https://doi.org/10.1/d", "authors": ["Park"], "relevance_score": 15.0},
    {"id": "W5", "title": "Linked list queues", "abstract": "Queue built on a linked list with a stack comparison.",
     "year": 2015, "cited_by_count": 70, "url": "https://doi.org/10.1/e", "authors": ["Choi"], "relevance_score": 12.0},
]


class FakeOpenAlexApi:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    async def search_papers(self, query, exclude_ids=None, sort_by="relevance"):
        self.calls.append({"query": query, "exclude_ids": exclude_ids, "sort_by": sort_by})
        return [dict(paper) for paper in PAPERS]


def paper_llm(prompt: str) -> str:
    if "search tokens for OpenAlex" in prompt:
        return '```json\n{"tokens": ["stack", "queue"]}\n```'
    if "Stack machines and LIFO" in prompt:
        return '{"score": 9, "reason": "LIFO 평가를 직접 다룸"}'
    if "Queueing theory" in prompt:
        return '{"score": 4, "reason": "주제가 다름"}'
    if "Array based stack" in prompt:
        fail("검증 호출 실패")
    if "Linked list queues" in prompt:
        return '{"score": 7, "reason": "큐 구현을 다룸"}'
    raise AssertionError(prompt[:200])


async def test_paper_provider(monkeypatch):
    from openalex.openalexkit.models import OpenAlexRequest
    from openalex.openalexkit.service import OpenAlexService

    llm = install_llm(monkeypatch, "openalex.openalexkit.llm.openai_client", paper_llm)
    service = OpenAlexService()
    api = FakeOpenAlexApi()
    service.api_client = api
    request = OpenAlexRequest(
        lecture_id="1", section_id=4, section_summary=SUMMARY, language="ko", top_k=3, verify_openalex=True,
        previous_summaries=PREVIOUS, rag_context=RAG, year_from=1960, exclude_ids=["W9"], sort_by="hybrid", min_score=5.0,
    )

    results = await service.recommend_papers(request)

    assert_snapshot("rec_paper", {
        "results": map_resources(ResourceType.PAPER, results),
        "api_calls": api.calls,
        "llm_calls": llm.sorted_calls(),
    })


# 위키

WIKI_SEARCH = {
    ("Stack", "en"): [{"pageid": 1, "title": "Stack", "snippet": "Stack may refer to"},
                      {"pageid": 2, "title": "Stack (abstract data type)", "snippet": "LIFO collection"}],
    ("LIFO", "en"): [{"pageid": 3, "title": "Queue (abstract data type)", "snippet": "FIFO"},
                     {"pageid": 2, "title": "Stack (abstract data type)", "snippet": "LIFO collection"}],
    ("Stack", "ko"): [{"pageid": 10, "title": "스택", "snippet": "스택 자료구조"}],
    ("LIFO", "ko"): [{"pageid": 11, "title": "후입선출", "snippet": "LIFO"}],
}
WIKI_PAGES = {
    1: {"title": "Stack", "extract": "Stack may refer to:", "disambiguation": True},
    2: {"title": "Stack (abstract data type)", "extract": "A stack is a LIFO\ncollection of elements."},
    3: {"title": "Queue (abstract data type)", "extract": "A queue is FIFO."},
    10: {"title": "스택", "extract": "스택은 LIFO 구조의 자료구조이다."},
    11: {"title": "후입선출", "extract": "후입선출은 나중에 들어온 것을 먼저 처리한다."},
}


class FakeWikiApi:
    def __init__(self) -> None:
        self.calls: List[Any] = []

    async def search_pages(self, keyword, lang="en", limit=6):
        self.calls.append(["search", keyword, lang, limit])
        return [dict(page) for page in WIKI_SEARCH.get((keyword, lang), [])]

    async def get_page_extract(self, page_id, lang="en"):
        self.calls.append(["extract", page_id, lang])
        page = WIKI_PAGES[page_id]
        return {
            "title": page["title"],
            "extract": page["extract"],
            "url": f"https://{lang}.wikipedia.org/?curid={page_id}",
            "pageid": page_id,
            "disambiguation": page.get("disambiguation", False),
        }


def wiki_llm(prompt: str) -> str:
    if "Wikipedia search keywords" in prompt:
        return '{"keywords": ["Stack", "LIFO"]}'
    if "Document Title: Stack (abstract data type)" in prompt:
        return '{"score": 8, "reason": "스택을 직접 설명"}'
    if "Document Title: 스택" in prompt:
        fail("검증 호출 실패")
    if "Document Title: 후입선출" in prompt:
        return '```json\n{"score": 6.5, "reason": "배경 개념"}\n```'
    raise AssertionError(prompt[:200])


def wiki_request(**overrides):
    from wiki.wikikit.models import WikiRequest

    fields = dict(
        lecture_id="1", section_id=4, lecture_summary=SUMMARY, language="ko", top_k=2, verify_wiki=False,
        previous_summaries=PREVIOUS, rag_context=RAG, wiki_lang="en", fallback_to_ko=True,
        exclude_titles=["Queue (abstract data type)"], min_score=5.0,
    )
    fields.update(overrides)
    return WikiRequest(**fields)


@pytest.mark.parametrize("verify", [False, True], ids=["heuristic", "llm"])
async def test_wiki_provider(monkeypatch, verify):
    from wiki.wikikit.service import WikiService

    llm = install_llm(monkeypatch, "wiki.wikikit.llm.openai_client", wiki_llm)
    service = WikiService()
    api = FakeWikiApi()
    service.api_client = api

    results = await service.recommend_pages(wiki_request(verify_wiki=verify, top_k=3 if verify else 2))

    assert_snapshot(f"rec_wiki_{'llm' if verify else 'heuristic'}", {
        "results": map_resources(ResourceType.WIKI, results),
        "api_calls": sorted(api.calls, key=json.dumps),
        "llm_calls": llm.sorted_calls(),
    })


# 영상

def video_search_items():
    from youtube.youtubekit.api.youtube_client import YouTubeSearchItem

    def item(video_id, title):
        return YouTubeSearchItem(video_id=video_id, title=title, description=f"{title} description",
                                 channel_title="CS Channel", publish_time="2022-03-01T00:00:00Z")

    return [
        item("v1", "Stacks and Queues Explained"),
        item("v2", "Stack vs Queue | CS101"),
        item("v3", "Cooking pasta at home"),
        item("v4", "STACKS and Queues explained!"),
        item("v5", "Queue tutorial"),
        item("v6", "Stack overflow explained"),
    ]


def video_details():
    from youtube.youtubekit.api.youtube_client import YouTubeVideoDetail

    def detail(video_id, title, views, lang):
        return YouTubeVideoDetail(video_id=video_id, title=title, description=f"{title}\nfull description",
                                  default_lang=lang, view_count=views, duration_iso8601="PT10M",
                                  channel_title="CS Channel", publish_time="2021-05-01T00:00:00Z")

    return [
        detail("v1", "Stacks and Queues Explained", 120000, "en"),
        detail("v3", "Cooking pasta at home", 5000, None),
        detail("v6", "Stack overflow explained", 30000, "en"),
    ]


class FakeYouTubeApi:
    def __init__(self) -> None:
        self.calls: List[Any] = []

    async def search_videos(self, q, lang, max_results=8):
        self.calls.append(["search", q, lang, max_results])
        return video_search_items()

    async def get_videos(self, ids):
        self.calls.append(["videos", list(ids)])
        return [detail for detail in video_details() if detail.video_id in ids]


def video_llm(prompt: str) -> str:
    if "YouTube search queries" in prompt:
        return '{"queries": ["stack queue data structure", "second query"], "rationale": "core terms"}'
    if "predict video content" in prompt:
        title = prompt.split('Title: "', 1)[1].split('"', 1)[0]
        return json.dumps({"extract": f"{title} 요약 문장 1. 요약 문장 2."}, ensure_ascii=False)
    if "Evaluate video relevance" in prompt:
        if "Video Title: Stacks and Queues Explained" in prompt:
            return '{"score": 8.456, "reason": "스택과 큐를 직접 비교"}'
        if "Video Title: Cooking pasta" in prompt:
            return '{"score": 1, "reason": "무관"}'
        if "Video Title: Stack overflow" in prompt:
            fail("검증 호출 실패")
    raise AssertionError(prompt[:200])


async def test_video_provider(monkeypatch):
    from youtube.youtubekit.models import YouTubeRequest
    from youtube.youtubekit.service import YouTubeService

    llm = install_llm(monkeypatch, "youtube.youtubekit.llm.openai_client", video_llm)
    api = FakeYouTubeApi()
    service = YouTubeService(yt_client=api)
    service.llm.enabled = True
    request = YouTubeRequest(
        lecture_id="1", section_id=4, lecture_summary=SUMMARY, language="ko", top_k=2, verify_yt=True,
        previous_summaries=PREVIOUS, rag_context=RAG, yt_lang="en", exclude_titles=["Stack vs Queue | CS101"],
        min_score=7.0,
    )

    results = await service.recommend_videos(request)

    assert_snapshot("rec_video", {
        "results": map_resources(ResourceType.VIDEO, results),
        "api_calls": api.calls,
        "llm_calls": llm.sorted_calls(),
    })


# 블로그

BLOG_RESULTS = [
    {"title": "스택과 큐 차이 정리", "link": "https://blog.naver.com/a/1", "snippet": "스택 큐 차이를 예제로", "displayLink": "a"},
    {"title": "스택과 큐 차이 정리 (복사)", "link": "https://www.blog.naver.com/a/1", "snippet": "중복 글", "displayLink": "a"},
    {"title": "자료구조 일기", "link": "https://blog.naver.com/b/2", "snippet": "오늘 공부함", "displayLink": "b"},
    {"title": "이미 본 글", "link": "https://blog.naver.com/c/3", "snippet": "스택", "displayLink": "c"},
    {"title": "큐 구현하기", "link": "https://blog.naver.com/d/4", "snippet": "큐 구현", "displayLink": "d"},
]


class FakeNaverApi:
    def __init__(self) -> None:
        self.calls: List[Any] = []

    async def search(self, query, lang="ko", num=10):
        self.calls.append([query, lang, num])
        return [dict(result) for result in BLOG_RESULTS] if query == "스택 큐 차이" else []


def blog_llm(prompt: str) -> str:
    if "search query generator" in prompt:
        return "스택 큐 차이 예제\n큐 구현 방법"
    if "Title: 스택과 큐 차이 정리" in prompt:
        return '{"score": 8, "reason": "차이를 예제로 설명"}'
    if "Title: 자료구조 일기" in prompt:
        return '{"score": 2, "reason": "내용 부족"}'
    if "Title: 큐 구현하기" in prompt:
        fail("검증 호출 실패")
    raise AssertionError(prompt[:200])


async def test_blog_provider(monkeypatch):
    from blog.blogkit.models import GoogleRequest
    from blog.blogkit.service import GoogleService

    llm = install_llm(monkeypatch, "blog.blogkit.llm.openai_client", blog_llm)
    service = GoogleService()
    api = FakeNaverApi()
    service.api_client = api
    request = GoogleRequest(
        lecture_id="1", section_id=4, lecture_summary=SUMMARY, language="ko", top_k=2, verify_google=True,
        previous_summaries=PREVIOUS, rag_context=RAG, search_lang="ko", exclude_urls=["https://blog.naver.com/c/3"],
        min_score=3.0,
    )

    results = await service.recommend_results(request)

    assert_snapshot("rec_blog", {
        "results": map_resources(ResourceType.BLOG, results),
        "api_calls": api.calls,
        "llm_calls": llm.sorted_calls(),
    })
