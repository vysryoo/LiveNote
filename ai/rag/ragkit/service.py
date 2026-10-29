"""RAG 서비스: 강의 자료·섹션 요약 저장과 검색.

LangChain Chroma 벡터 저장소와 OpenAI 임베딩을 쓴다.
강의 자료(PDF)는 설정한 분할 방식(page, recursive, semantic)으로 조각내 저장하고,
조각마다 출처(source_type), 쪽 범위, 순서, 분할 방식을 메타데이터로 남긴다.
"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List

import chromadb
from chromadb.config import Settings
from chromadb.errors import NotFoundError
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from .config import RAGConfig
from .models import RetrievedChunk, RetrieveFilters, UpsertItem
from .splitters import ChunkSettings, PageText, split_document
from .utils.pdf import load_pdf_pages
from .utils.text import make_id

logger = logging.getLogger(__name__)

SOURCE_PDF = "pdf"
SOURCE_SUMMARY = "summary"
EMBEDDING_DIMENSIONS = {"text-embedding-3-large": 3072, "text-embedding-3-small": 1536}


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


def _passes_filters(chunk: RetrievedChunk, filters: RetrieveFilters) -> bool:
    # Chroma where 절은 문자열·숫자가 섞인 timestamp 비교를 지원하지 않아 검색 후 걸러냄
    timestamp = chunk.metadata.get("timestamp")
    if timestamp is not None:
        if filters.min_timestamp is not None and timestamp < filters.min_timestamp:
            return False
        if filters.max_timestamp is not None and timestamp > filters.max_timestamp:
            return False
    return filters.confidence is None or chunk.score >= filters.confidence


class RAGService:
    """강의별 컬렉션에 강의 자료와 섹션 요약을 저장하고 검색한다."""

    def __init__(
        self,
        config: RAGConfig | None = None,
        chunk_settings: ChunkSettings | None = None,
        embeddings=None,
    ):
        """서비스를 만든다.

        Args:
            config: 저장 경로·임베딩 모델 설정. None이면 기본값
            chunk_settings: 분할 설정. None이면 환경변수(RAG_CHUNK_STRATEGY 등)
            embeddings: LangChain Embeddings. None이면 config의 OpenAI 임베딩 모델
        """
        self.config = config or RAGConfig()
        self.chunk_settings = chunk_settings or ChunkSettings.from_env()
        self.embeddings = embeddings or OpenAIEmbeddings(
            model=self.config.embedding_model, api_key=self.config.openai_api_key
        )
        self.client = chromadb.PersistentClient(
            path=self.config.persist_dir,
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
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
            "embedding_dim": EMBEDDING_DIMENSIONS.get(self.config.embedding_model, 0) if count else 0,
        }

    def upsert_text(self, collection_id: str, items: List[UpsertItem] | List[Dict[str, Any]]) -> Dict[str, Any]:
        """텍스트(섹션 요약 등)를 저장한다. 같은 ID는 덮어쓴다.

        Args:
            collection_id: 컬렉션 이름
            items: UpsertItem 또는 text·id·metadata·section_id를 가진 dict 목록
        Returns:
            {"collection_id", "count", "embedding_dim"}
        """
        if not items:
            logger.warning("No items to upsert")
            return self._result(collection_id, 0)
        upsert_items = [UpsertItem(**item) if isinstance(item, dict) else item for item in items]
        documents, ids = [], []
        for item in upsert_items:
            metadata = dict(item.metadata)
            if item.section_id:
                metadata["section_id"] = item.section_id
            documents.append(Document(page_content=item.text, metadata=clean_metadata(metadata)))
            ids.append(item.id or make_id(item.text))
        self._store(collection_id).add_documents(documents, ids=ids)
        logger.info("[Upsert Text] collection=%s count=%d", collection_id, len(ids))
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
        pages = [PageText(page=doc.metadata["page"], text=doc.page_content) for doc in load_pdf_pages(pdf_path)]
        if not pages:
            logger.warning("No pages loaded from %s", pdf_path)
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
        logger.info(
            "[Upsert PDF] collection=%s file=%s strategy=%s chunks=%d", collection_id, file_name, settings.strategy, len(ids)
        )
        return self._result(collection_id, len(ids))

    def _search(self, collection_id: str, query: str, top_k: int, where: Dict[str, Any] | None) -> List[RetrievedChunk]:
        if top_k <= 0 or not self._exists(collection_id):
            return []
        results = self._store(collection_id).similarity_search_with_score(query, k=top_k, filter=where)
        return [
            RetrievedChunk(
                id=document.id or "",
                text=document.page_content,
                score=to_score(distance),
                metadata=dict(document.metadata),
                section_id=document.metadata.get("section_id"),
            )
            for document, distance in results
        ]

    def retrieve(
        self,
        collection_id: str,
        query: str,
        top_k: int = 5,
        filters: RetrieveFilters | None = None,
    ) -> List[RetrievedChunk]:
        """질의와 가까운 조각을 찾는다.

        Args:
            collection_id: 컬렉션 이름. 영문·숫자·하이픈·밑줄만 허용
            query: 질의 텍스트
            top_k: 돌려줄 개수
            filters: 메타데이터 조건, timestamp 범위, 최소 점수
        Returns:
            점수 내림차순 조각 목록. 컬렉션이 없으면 빈 목록
        Raises:
            ValueError: 컬렉션 이름이나 질의가 비었거나 형식이 맞지 않는 경우
        """
        import re

        if not collection_id or not collection_id.strip():
            raise ValueError("collection_id는 비어 있을 수 없습니다")
        if not query or not query.strip():
            raise ValueError("query는 비어 있을 수 없습니다")
        if not re.match(r"^[a-zA-Z0-9_-]+$", collection_id):
            raise ValueError("collection_id는 영문, 숫자, 하이픈, 언더스코어만 사용 가능합니다")
        if filters and filters.confidence is not None and not 0.0 <= filters.confidence <= 1.0:
            raise ValueError("confidence는 0.0과 1.0 사이여야 합니다")

        where: Dict[str, Any] = {}
        if filters:
            if filters.subject:
                where["subject"] = filters.subject
            if filters.section_id:
                where["section_id"] = filters.section_id
            where.update(filters.custom)
        if len(where) > 1:
            where = {"$and": [{key: value} for key, value in where.items()]}
        chunks = self._search(collection_id, query, top_k, where or None)
        if filters:
            chunks = [c for c in chunks if _passes_filters(c, filters)]
        return sorted(chunks, key=lambda c: c.score, reverse=True)

    def retrieve_context(
        self,
        collection_id: str,
        query: str,
        section_index: int,
        pdf_top_k: int,
        summary_top_k: int,
        recent_window: int,
    ) -> List[RetrievedChunk]:
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
        summaries: List[RetrievedChunk] = []
        if oldest_allowed > 0:
            summaries = self._search(
                collection_id,
                query,
                summary_top_k,
                {"$and": [{"source_type": SOURCE_SUMMARY}, {"section_index": {"$lt": oldest_allowed}}]},
            )
        return pdf_chunks + summaries
