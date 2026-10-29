from __future__ import annotations

from pathlib import Path

from langchain_core.embeddings import DeterministicFakeEmbedding

from rag.ragkit.config import RAGConfig
from rag.ragkit.models import RetrieveFilters
from rag.ragkit.service import RAGService
from rag.ragkit.splitters import ChunkSettings

PDF_PATH = Path(__file__).resolve().parent.parent / "rag" / "test_data" / "simple_test.pdf"


def _service(tmp_path, strategy: str = "page", **settings) -> RAGService:
    return RAGService(
        RAGConfig(persist_dir=str(tmp_path), openai_api_key="test"),
        ChunkSettings(strategy=strategy, **settings),
        embeddings=DeterministicFakeEmbedding(size=16),
    )


def test_retrieve_on_missing_collection_returns_empty_without_creating(tmp_path):
    service = _service(tmp_path)

    assert service.retrieve("lecture_999", "질의", top_k=3) == []
    assert service.retrieve_context("lecture_999", "질의", 5, 2, 1, 3) == []
    assert not service._exists("lecture_999")


def test_upsert_pdf_tags_chunks_and_replaces_previous_chunks_of_same_file(tmp_path):
    page_service = _service(tmp_path, "page")
    first = page_service.upsert_pdf("lecture_1", str(PDF_PATH))
    collection = page_service.client.get_collection("lecture_1")
    metadata = collection.get(include=["metadatas"])["metadatas"][0]

    assert first["count"] == collection.count()
    assert metadata["source_type"] == "pdf"
    assert metadata["strategy"] == "page"
    assert metadata["file_name"] == PDF_PATH.name

    recursive_service = _service(tmp_path, "recursive", chunk_tokens=20, chunk_overlap_tokens=0)
    second = recursive_service.upsert_pdf("lecture_1", str(PDF_PATH))
    strategies = {m["strategy"] for m in collection.get(include=["metadatas"])["metadatas"]}

    assert collection.count() == second["count"]
    assert strategies == {"recursive"}


def test_retrieve_context_excludes_recent_summaries(tmp_path):
    service = _service(tmp_path)
    service.upsert_pdf("lecture_2", str(PDF_PATH))
    service.upsert_text(
        "lecture_2",
        [
            {"text": f"섹션 {i} 요약", "id": f"s{i}", "metadata": {"source_type": "summary", "section_index": i}}
            for i in range(6)
        ],
    )

    chunks = service.retrieve_context("lecture_2", "섹션 요약", section_index=6, pdf_top_k=2, summary_top_k=5, recent_window=3)

    pdf = [c for c in chunks if c.metadata["source_type"] == "pdf"]
    summaries = [c for c in chunks if c.metadata["source_type"] == "summary"]
    assert len(pdf) == 2
    assert sorted(c.metadata["section_index"] for c in summaries) == [0, 1, 2]
    assert chunks[: len(pdf)] == pdf


def _upsert(service: RAGService, collection_id: str, metadatas: list[dict]) -> None:
    service.upsert_text(
        collection_id, [{"text": f"문서 {i}", "id": f"d{i}", "metadata": m} for i, m in enumerate(metadatas)]
    )


def test_retrieve_respects_top_k_and_sorts_by_score(tmp_path):
    service = _service(tmp_path)
    _upsert(service, "lecture_3", [{"index": i} for i in range(5)])

    chunks = service.retrieve("lecture_3", "문서", top_k=3)

    assert len(chunks) == 3
    assert [c.score for c in chunks] == sorted((c.score for c in chunks), reverse=True)


def test_retrieve_filters_by_subject_and_timestamp(tmp_path):
    service = _service(tmp_path)
    _upsert(
        service,
        "lecture_4",
        [
            {"subject": "CS", "timestamp": 100},
            {"subject": "CS", "timestamp": 200},
            {"subject": "Bio", "timestamp": 300},
        ],
    )

    by_subject = service.retrieve("lecture_4", "문서", top_k=10, filters=RetrieveFilters(subject="CS"))
    by_time = service.retrieve("lecture_4", "문서", top_k=10, filters=RetrieveFilters(min_timestamp=150, max_timestamp=250))

    assert {c.metadata["subject"] for c in by_subject} == {"CS"} and len(by_subject) == 2
    assert [c.metadata["timestamp"] for c in by_time] == [200]


def test_upsert_text_with_same_ids_overwrites_and_collections_are_isolated(tmp_path):
    service = _service(tmp_path)
    _upsert(service, "lecture_5", [{"index": 0}, {"index": 1}])
    _upsert(service, "lecture_5", [{"index": 0}, {"index": 1}])
    _upsert(service, "lecture_6", [{"index": 0}])

    assert service.client.get_collection("lecture_5").count() == 2
    assert service.client.get_collection("lecture_6").count() == 1
