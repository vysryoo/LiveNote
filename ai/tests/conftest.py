from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from server.app import create_app
from server.config import AppSettings


@dataclass
class SimpleModel:
    """model_dump를 제공하는 단순 베이스"""
    
    def model_dump(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)


@dataclass
class PaperInfo(SimpleModel):
    url: str
    title: str
    abstract: str
    year: Optional[int] = None
    cited_by_count: int = 0
    authors: List[str] = field(default_factory=list)


@dataclass
class OpenAlexResponse(SimpleModel):
    lecture_id: str
    section_id: int
    paper_info: PaperInfo
    reason: str
    score: float


@dataclass
class WikiPageInfo(SimpleModel):
    url: str
    title: str
    extract: str
    lang: str
    page_id: int


@dataclass
class WikiResponse(SimpleModel):
    lecture_id: str
    section_id: int
    page_info: WikiPageInfo
    reason: str
    score: float


@dataclass
class YouTubeVideoInfo(SimpleModel):
    url: str
    title: str
    extract: str
    lang: str


@dataclass
class YouTubeResponse(SimpleModel):
    lecture_id: str
    section_id: int
    video_info: YouTubeVideoInfo
    reason: str
    score: float


@dataclass
class StubRetrievedChunk:
    """단순 RAG 청크"""
    id: str
    text: str
    score: float
    metadata: Dict[str, Any]


class StubRAGService:
    """RAG 서비스 스텁"""
    
    def __init__(self):
        self.pdf_calls: List[Dict[str, Any]] = []
        self.text_calls: List[Dict[str, Any]] = []
        self.retrieve_calls: List[Dict[str, Any]] = []
        self.retrieve_result: List[StubRetrievedChunk] = []
        self.upsert_pdf_result: Dict[str, Any] = {"count": 3, "status": "ok"}
        self.upsert_text_result: Dict[str, Any] = {"count": 2, "status": "ok"}
    
    def upsert_pdf(self, collection_id: str, pdf_path: str, base_metadata: Optional[Dict[str, Any]] = None):
        self.pdf_calls.append(
            {
                "collection_id": collection_id,
                "pdf_path": pdf_path,
                "base_metadata": base_metadata,
            }
        )
        return self.upsert_pdf_result
    
    def upsert_text(self, collection_id: str, items: List[Any]):
        self.text_calls.append(
            {
                "collection_id": collection_id,
                "items": items,
            }
        )
        return self.upsert_text_result
    
    def retrieve(self, collection_id: str, query: str, top_k: int, filters=None):
        self.retrieve_calls.append(
            {
                "collection_id": collection_id,
                "query": query,
                "top_k": top_k,
                "filters": filters,
            }
        )
        return list(self.retrieve_result)


class StubQAService:
    """QA 서비스 스텁"""
    
    def __init__(self):
        self.events: List[Tuple[str, str, Dict[str, Any]]] = []
        self.request_payloads: List[Any] = []
    
    async def stream_questions(self, request):
        self.request_payloads.append(request)
        for event in self.events:
            if isinstance(event, Exception):
                raise event
            event_type, q_type, payload = event
            # 작은 지연으로 순서를 제어
            await asyncio.sleep(payload.get("_delay", 0))
            clean_payload = dict(payload)
            clean_payload.pop("_delay", None)
            yield event_type, q_type, clean_payload


class StubOpenAlexService:
    """OpenAlex 서비스 스텁"""
    
    def __init__(self):
        self.responses: List[OpenAlexResponse] = []
        self.delay: float = 0.0
        self.requests: List[OpenAlexResponse] = []
    
    async def recommend_papers(self, request):
        self.requests.append(request)
        if self.delay:
            await asyncio.sleep(self.delay)
        return list(self.responses)


class StubWikiService:
    """Wiki 서비스 스텁"""
    
    def __init__(self):
        self.responses: List[WikiResponse] = []
        self.delay: float = 0.0
        self.requests: List[WikiResponse] = []
    
    async def recommend_pages(self, request):
        self.requests.append(request)
        if self.delay:
            await asyncio.sleep(self.delay)
        return list(self.responses)


class StubYouTubeService:
    """YouTube 서비스 스텁"""
    
    def __init__(self):
        self.responses: List[YouTubeResponse] = []
        self.delay: float = 0.0
        self.requests: List[Any] = []
    
    async def recommend_videos(self, request):
        self.requests.append(request)
        if self.delay:
            await asyncio.sleep(self.delay)
        return list(self.responses)


@dataclass
class TestContext:
    """테스트에서 사용할 스텁 모음"""
    
    rag: StubRAGService = field(default_factory=StubRAGService)
    qa: StubQAService = field(default_factory=StubQAService)
    openalex: StubOpenAlexService = field(default_factory=StubOpenAlexService)
    wiki: StubWikiService = field(default_factory=StubWikiService)
    youtube: StubYouTubeService = field(default_factory=StubYouTubeService)
    settings: AppSettings = field(default_factory=AppSettings)


@pytest.fixture
def test_context() -> TestContext:
    ctx = TestContext()
    # 기본 설정 조정
    ctx.settings.rag.collection_prefix = "test"
    ctx.settings.rag.qa_retrieve_top_k = 2
    ctx.settings.rag.rec_retrieve_top_k = 3
    ctx.settings.qa.language = "ko"
    ctx.settings.qa.question_types = ["응용", "비교", "심화"]
    ctx.settings.qa.qa_top_k = 3
    ctx.settings.rec.openalex.top_k = 2
    ctx.settings.rec.openalex.verify = True
    ctx.settings.rec.openalex.min_score = 3.0
    ctx.settings.rec.openalex.sort_by = "hybrid"
    ctx.settings.rec.wiki.top_k = 2
    ctx.settings.rec.wiki.verify = False
    ctx.settings.rec.wiki.wiki_lang = "en"
    ctx.settings.rec.wiki.min_score = 3.0
    ctx.settings.rec.youtube.top_k = 2
    ctx.settings.rec.youtube.verify = True
    ctx.settings.rec.youtube.yt_lang = "en"
    ctx.settings.rec.youtube.min_score = 3.0
    return ctx


@pytest.fixture
def fastapi_app(test_context: TestContext) -> FastAPI:
    return create_app(
        test_context.settings,
        rag_service=test_context.rag,
        qa_service=test_context.qa,
        openalex_service=test_context.openalex,
        wiki_service=test_context.wiki,
        youtube_service=test_context.youtube,
    )


@pytest.fixture
async def async_client(fastapi_app: FastAPI):
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
