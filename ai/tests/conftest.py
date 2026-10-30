from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from core.config import Settings, get_settings
from core.schemas import QnAType, RAGChunk, ResourceType
from qa.models import QAEvent
from recommend.models import RecContext, Recommendation
from server.app import create_app
from server.dependencies import Services
from summary.service import SummaryService


class StubRAGService:
    """RAG 서비스 스텁"""
    
    def __init__(self):
        self.pdf_calls: List[Dict[str, Any]] = []
        self.text_calls: List[Dict[str, Any]] = []
        self.retrieve_calls: List[Dict[str, Any]] = []
        self.retrieve_result: List[RAGChunk] = []
        self.upsert_pdf_result: Dict[str, Any] = {"count": 3, "status": "ok"}
        self.upsert_summaries_result: Dict[str, Any] = {"count": 2, "status": "ok"}
    
    def upsert_pdf(self, collection_id: str, pdf_path: str, base_metadata: Optional[Dict[str, Any]] = None):
        self.pdf_calls.append(
            {
                "collection_id": collection_id,
                "pdf_path": pdf_path,
                "base_metadata": base_metadata,
            }
        )
        return self.upsert_pdf_result
    
    def upsert_summaries(self, collection_id: str, items: List[Any]):
        self.text_calls.append(
            {
                "collection_id": collection_id,
                "items": items,
            }
        )
        return self.upsert_summaries_result
    
    def retrieve_context(self, collection_id: str, query: str, section_index: int, pdf_top_k: int, summary_top_k: int, recent_window: int):
        self.retrieve_calls.append(
            {
                "collection_id": collection_id,
                "query": query,
                "section_index": section_index,
                "top_k": pdf_top_k,
                "summary_top_k": summary_top_k,
                "recent_window": recent_window,
            }
        )
        return list(self.retrieve_result)


class StubQAService:
    """QA 서비스 스텁"""
    
    def __init__(self):
        self.events: List[QAEvent] = []
        self.request_payloads: List[Any] = []

    async def stream_questions(self, request):
        self.request_payloads.append(request)
        for event in self.events:
            yield event


class StubRecommendService:
    """자료 추천 서비스 스텁. 자료 종류별로 정해 둔 결과를 돌려주고, failures에 있는 종류는 예외를 낸다."""

    def __init__(self):
        self.results: Dict[ResourceType, List[Recommendation]] = {}
        self.failures: Dict[ResourceType, Exception] = {}
        self.calls: List[Tuple[ResourceType, RecContext]] = []

    async def recommend(self, resource_type: ResourceType, context: RecContext) -> List[Recommendation]:
        self.calls.append((resource_type, context))
        if resource_type in self.failures:
            raise self.failures[resource_type]
        return list(self.results.get(resource_type, []))

    async def close(self) -> None:
        pass


@dataclass
class TestContext:
    """테스트에서 사용할 스텁 모음"""
    
    rag: StubRAGService = field(default_factory=StubRAGService)
    qa: StubQAService = field(default_factory=StubQAService)
    rec: StubRecommendService = field(default_factory=StubRecommendService)
    settings: Settings = field(default_factory=Settings)

    def services(self, **overrides: Any) -> Services:
        """스텁 서비스 묶음을 만든다. 요약은 실제 서비스(LLM 호출은 테스트에서 바꿔 끼움)."""
        fields = dict(rag=self.rag, qa=self.qa, rec=self.rec, summary=SummaryService(self.settings.summary))
        fields.update(overrides)
        return Services(**fields)


@pytest.fixture
def test_context(tmp_path) -> TestContext:
    ctx = TestContext()
    # 업로드·벡터 저장을 실제 ai/server_storage 대신 임시 폴더에 둠
    ctx.settings.rag_upload_dir = tmp_path / "uploads"
    ctx.settings.rag_persist_dir = tmp_path / "chroma"
    # 기본 설정 조정
    ctx.settings.rag.collection_prefix = "test"
    ctx.settings.rag.qa_retrieve_top_k = 2
    ctx.settings.rag.rec_retrieve_top_k = 3
    ctx.settings.qa.language = "ko"
    ctx.settings.qa.question_types = [QnAType.APPLICATION, QnAType.COMPARISON, QnAType.ADVANCED]
    ctx.settings.qa.qa_top_k = 3
    return ctx


@pytest.fixture
def fastapi_app(test_context: TestContext) -> FastAPI:
    return create_app(test_context.settings, services=test_context.services())


TEST_INTERNAL_API_KEY = "test-internal-key"


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch):
    """ai/.env를 읽지 않고, 백엔드와 공유하는 내부 키와 OpenAI 키를 테스트 값으로 둔다."""
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setenv("INTERNAL_API_KEY", TEST_INTERNAL_API_KEY)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def internal_api_key(isolated_settings):
    return TEST_INTERNAL_API_KEY


@pytest.fixture
async def async_client(fastapi_app: FastAPI, internal_api_key: str):
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers={"X-Internal-Api-Key": internal_api_key},
    ) as client:
        yield client


@pytest.fixture
def callback_recorder(monkeypatch):
    """
    httpx.AsyncClient을 대체해 콜백 요청을 캡처합니다.
    """
    captured: List[Dict[str, Any]] = []

    class _RecorderClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json, headers=None):
            captured.append({"url": url, "json": json, "headers": headers})
            return type("Resp", (), {"status_code": 200})

    monkeypatch.setattr("server.callback.httpx.AsyncClient", _RecorderClient)
    return captured


def pytest_configure(config):
    """anyio 백엔드를 asyncio로 제한하여 trio 관련 의존성 오류를 방지"""
    config.option.anyio_backend = ["asyncio"]


@pytest.fixture(autouse=True)
def skip_trio_backend(request):
    """anyio가 trio 백엔드로 파라미터라이즈될 때는 스킵"""
    callspec = getattr(request.node, "callspec", None)
    if callspec:
        backend = callspec.params.get("anyio_backend")
        if backend == "trio":
            pytest.skip("trio backend is not supported in this test suite")
