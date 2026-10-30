"""RAG 서비스: 강의 자료·섹션 요약 저장과 검색.

LangChain Chroma 벡터 저장소와 OpenAI 임베딩을 쓴다.
강의 자료(PDF)는 설정한 분할 방식(page, recursive, semantic)으로 조각내 저장하고,
조각마다 출처(source_type), 쪽 범위, 순서, 분할 방식을 메타데이터로 남긴다.
"""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.errors import NotFoundError
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from core.config import Settings
from core.schemas import RAGChunk

from .pdf import load_pdf_pages
from .splitters import ChunkSettings, split_document

logger = logging.getLogger(__name__)

SOURCE_PDF = "pdf"
SOURCE_SUMMARY = "summary"
EMBEDDING_DIMENSIONS = {"text-embedding-3-large": 3072, "text-embedding-3-small": 1536}
COLLECTION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


@dataclass
class SummaryItem:
    """저장할 섹션 요약."""

    text: str
    id: Optional[str] = None
    section_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


def to_score(distance: float) -> float:
    """Chroma 거리(L2, 작을수록 가까움)를 0~1 유사도 점수(클수록 가까움)로 바꾼다.

    Args:
        distance: Chroma가 돌려준 거리
    Returns:
        1 / (1 + 거리)
    """
    return 1.0 / (1.0 + distance)


def clean_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Chroma가 받는 값(str, int, float, bool)만 남기고 나머지는 문자열로 바꾼다.

    Args:
        metadata: 원래 메타데이터
    Returns:
        정리한 메타데이터. None 값은 제외
    """
    return {
        key: value if isinstance(value, (str, int, float, bool)) else str(value)
        for key, value in metadata.items()
        if value is not None
    }


def make_id(text: str) -> str:
    """텍스트 내용으로 같은 텍스트면 같은 ID를 만든다.

    Args:
        text: 텍스트
    Returns:
        SHA-256 앞 14자리
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:14]


class RAGService:
    """강의별 컬렉션에 강의 자료와 섹션 요약을 저장하고 검색한다."""

    def __init__(
        self,
        settings: Settings,
        chunk_settings: ChunkSettings | None = None,
        embeddings=None,
    ):
        """서비스를 만든다. 저장 폴더가 없으면 만든다.

        Args:
            settings: 서버 설정 (저장 경로, 임베딩 모델, API 키, 분할 설정)
            chunk_settings: 분할 설정. None이면 서버 설정의 RAG_CHUNK_*·RAG_SEMANTIC_* 값
            embeddings: LangChain Embeddings. None이면 서버 설정의 OpenAI 임베딩 모델
        """
        self.embedding_model = settings.rag_embedding_model
        self.chunk_settings = chunk_settings or ChunkSettings.from_settings(settings)
        self.embeddings = embeddings or OpenAIEmbeddings(
            model=self.embedding_model, api_key=settings.rag_openai_api_key or settings.openai_api_key or None
        )
        settings.rag_persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(settings.rag_persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
        )
        logger.info("RAGService initialized (strategy=%s)", self.chunk_settings.strategy)

    def _store(self, collection_id: str) -> Chroma:
        return Chroma(client=self.client, collection_name=collection_id, embedding_function=self.embeddings)

    def _exists(self, collection_id: str) -> bool:
        try:
            self.client.get_collection(name=collection_id)
            return True
        except NotFoundError:
            return False

    def _result(self, collection_id: str, count: int) -> Dict[str, Any]:
        return {
            "collection_id": collection_id,
            "count": count,
            "embedding_dim": EMBEDDING_DIMENSIONS.get(self.embedding_model, 0) if count else 0,
        }

    def upsert_summaries(self, collection_id: str, items: List[SummaryItem]) -> Dict[str, Any]:
        """백엔드가 확정한 섹션 요약을 저장한다. 같은 ID는 덮어쓴다.

        강의 자료와 구분하도록 source_type을 summary로 표시하고, 숫자 section_id는 섹션 번호(section_index)로도
        남겨 retrieve_context가 직전 섹션 요약을 뺄 수 있게 한다.

        Args:
            collection_id: 컬렉션 이름
            items: 요약 목록. id가 없으면 텍스트 내용으로 만듦
        Returns:
            {"collection_id", "count", "embedding_dim"}
        """
        if not items:
            return self._result(collection_id, 0)
        documents, ids = [], []
        for item in items:
            metadata = {**item.metadata, "source_type": SOURCE_SUMMARY}
            if item.section_id:
                metadata["section_id"] = item.section_id
                if item.section_id.isdigit():
                    metadata["section_index"] = int(item.section_id)
            documents.append(Document(page_content=item.text, metadata=clean_metadata(metadata)))
            ids.append(item.id or make_id(item.text))
        self._store(collection_id).add_documents(documents, ids=ids)
        logger.info("요약 저장: collection=%s count=%d", collection_id, len(ids))
        return self._result(collection_id, len(ids))

    def upsert_pdf(
        self,
        collection_id: str,
        pdf_path: str,
        base_metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """PDF를 분할 설정에 따라 조각내 저장한다. 같은 파일의 이전 조각은 먼저 지운다.

        분할 방식이 바뀌면 조각 수가 달라져 덮어쓰기만으로는 이전 조각이 남기 때문이다.

        Args:
            collection_id: 컬렉션 이름
            pdf_path: PDF 경로
            base_metadata: 모든 조각에 붙일 메타데이터
        Returns:
            {"collection_id", "count", "embedding_dim"}
        Raises:
            ValueError: PDF를 읽지 못한 경우
        """
        pages = load_pdf_pages(pdf_path)
        if not pages:
            logger.warning("텍스트가 있는 쪽 없음: %s", pdf_path)
            return self._result(collection_id, 0)

        file_name = Path(pdf_path).name
        settings = self.chunk_settings
        chunks = split_document(pages, settings, self.embeddings)
        doc_hash = hashlib.sha256(Path(pdf_path).read_bytes()).hexdigest()[:12]

        store = self._store(collection_id)
        store.delete(where={"$and": [{"source_type": SOURCE_PDF}, {"file_name": file_name}]})
        documents, ids = [], []
        for chunk in chunks:
            metadata = {
                **(base_metadata or {}),
                "source_type": SOURCE_PDF,
                "source": file_name,
                "file_name": file_name,
                "page": chunk.page_start,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "chunk_index": chunk.index,
                "strategy": settings.strategy,
            }
            documents.append(Document(page_content=chunk.text, metadata=clean_metadata(metadata)))
            ids.append(f"pdf|{doc_hash}|{settings.strategy}|c{chunk.index}")
        if documents:
            store.add_documents(documents, ids=ids)
        logger.info("PDF 저장: collection=%s file=%s strategy=%s chunks=%d", collection_id, file_name, settings.strategy, len(ids))
        return self._result(collection_id, len(ids))

    def _search(self, collection_id: str, query: str, top_k: int, where: Dict[str, Any] | None) -> List[RAGChunk]:
        if top_k <= 0 or not self._exists(collection_id):
            return []
        results = self._store(collection_id).similarity_search_with_score(query, k=top_k, filter=where)
        return [
            RAGChunk(id=document.id, text=document.page_content, score=to_score(distance), metadata=dict(document.metadata))
            for document, distance in results
        ]

    def retrieve(self, collection_id: str, query: str, top_k: int = 5) -> List[RAGChunk]:
        """질의와 가까운 조각을 찾는다. 평가(검색 단계 측정)에서 쓴다.

        Args:
            collection_id: 컬렉션 이름. 영문·숫자·하이픈·밑줄만 허용
            query: 질의 텍스트
            top_k: 돌려줄 개수
        Returns:
            점수 내림차순 조각 목록. 컬렉션이 없으면 빈 목록
        Raises:
            ValueError: 컬렉션 이름이나 질의가 비었거나 형식이 맞지 않는 경우
        """
        if not COLLECTION_ID_PATTERN.match(collection_id or ""):
            raise ValueError("collection_id는 영문, 숫자, 하이픈, 언더스코어로 된 비어 있지 않은 문자열이어야 함")
        if not query or not query.strip():
            raise ValueError("query는 비어 있을 수 없음")
        return sorted(self._search(collection_id, query, top_k, None), key=lambda c: c.score, reverse=True)

    def retrieve_context(
        self,
        collection_id: str,
        query: str,
        section_index: int,
        pdf_top_k: int,
        summary_top_k: int,
        recent_window: int,
    ) -> List[RAGChunk]:
        """강의 자료 조각과 이전 섹션 요약을 따로 검색해 합친다.

        직전 recent_window개 섹션 요약은 백엔드가 previousSummaries로 따로 보내므로 검색에서 뺀다.

        Args:
            collection_id: 컬렉션 이름
            query: 질의 (현재 섹션 요약)
            section_index: 현재 섹션 번호 (0부터)
            pdf_top_k: 강의 자료 조각 개수
            summary_top_k: 이전 요약 개수
            recent_window: 검색에서 뺄 직전 섹션 수
        Returns:
            강의 자료 조각(점수순) 뒤에 이전 요약(점수순)을 이은 목록
        """
        pdf_chunks = self._search(collection_id, query, pdf_top_k, {"source_type": SOURCE_PDF})
        oldest_allowed = section_index - recent_window
        summaries: List[RAGChunk] = []
        if oldest_allowed > 0:
            summaries = self._search(
                collection_id,
                query,
                summary_top_k,
                {"$and": [{"source_type": SOURCE_SUMMARY}, {"section_index": {"$lt": oldest_allowed}}]},
            )
        return pdf_chunks + summaries
