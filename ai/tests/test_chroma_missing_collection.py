from __future__ import annotations

from rag.ragkit.vectordb.chroma import ChromaVectorStore


def test_query_on_missing_collection_returns_no_results(tmp_path):
    store = ChromaVectorStore(persist_dir=str(tmp_path))

    assert store.query(collection_id="lecture_999", query_embedding=[0.1, 0.2, 0.3], top_k=3) == []


def test_query_on_existing_collection_still_returns_results(tmp_path):
    store = ChromaVectorStore(persist_dir=str(tmp_path))
    store.create_collection("lecture_1")
    store.upsert_many("lecture_1", ids=["a"], texts=["스택"], embeddings=[[0.1, 0.2, 0.3]], metadatas=[{"section_id": 1}])

    results = store.query(collection_id="lecture_1", query_embedding=[0.1, 0.2, 0.3], top_k=3)

    assert [r["id"] for r in results] == ["a"]
