"""Tests for text upserting functionality."""

import pytest

from ragkit.models import UpsertItem


@pytest.mark.live
def test_single_item_upsert(rag_service):
    """Test upserting a single item generates ID and correct count."""
    collection_id = "test_single"
    
    items = [
        UpsertItem(
            text="This is a test document about vector databases.",
            metadata={"source": "test", "index": 0}
        )
    ]
    
    result = rag_service.upsert_text(collection_id, items)
    
    assert result["collection_id"] == collection_id
    assert result["count"] == 1
    assert result["embedding_dim"] > 0
    
    print(f"\n[Upsert] collection={collection_id} count={result['count']} dim={result['embedding_dim']}")


@pytest.mark.live
def test_multiple_items_idempotent(rag_service):
    """Test upserting multiple items is idempotent on re-upsert."""
    collection_id = "test_multiple"
    
    # First upsert
    items = [
        UpsertItem(
            id="doc1",
            text="First document about embeddings.",
            metadata={"index": 1}
        ),
        UpsertItem(
            id="doc2",
            text="Second document about retrieval.",
            metadata={"index": 2}
        ),
        UpsertItem(
            id="doc3",
            text="Third document about generation.",
            metadata={"index": 3}
        ),
    ]
    
    result1 = rag_service.upsert_text(collection_id, items)
    assert result1["count"] == 3
    
    # Re-upsert same items (should be idempotent)
    result2 = rag_service.upsert_text(collection_id, items)
    assert result2["count"] == 3
    
    # Retrieve to verify only 3 items exist
    chunks = rag_service.retrieve(collection_id, "document", top_k=10)
    assert len(chunks) == 3
    
    print(f"\n[Upsert Idempotent] collection={collection_id} count={result2['count']} unique_ids=3")


@pytest.mark.live
def test_metadata_stored_and_retrievable(rag_service):
    """Test that metadata is stored and can be retrieved."""
    collection_id = "test_metadata"
    
    items = [
        UpsertItem(
            text="Machine learning is a subset of artificial intelligence.",
            metadata={
                "subject": "AI",
                "timestamp": 1234567890,
                "author": "John Doe",
                "language": "en"
            }
        )
    ]
    
    rag_service.upsert_text(collection_id, items)
    
    # Retrieve
    chunks = rag_service.retrieve(collection_id, "machine learning", top_k=1)
    
    assert len(chunks) == 1
    chunk = chunks[0]
    
    assert chunk.metadata["subject"] == "AI"
    assert chunk.metadata["timestamp"] == 1234567890
    assert chunk.metadata["author"] == "John Doe"
    assert chunk.metadata["language"] == "en"
    
    print(f"\n[Metadata] subject={chunk.metadata['subject']} timestamp={chunk.metadata['timestamp']}")


@pytest.mark.live
def test_unicode_korean_text(rag_service):
    """Test that unicode/Korean text works correctly."""
    collection_id = "test_korean"
    
    items = [
        UpsertItem(
            text="벡터 데이터베이스는 고차원 벡터를 효율적으로 저장하고 검색합니다.",
            metadata={"language": "ko", "topic": "vector_db"}
        ),
        UpsertItem(
            text="RAG는 검색 증강 생성을 의미합니다.",
            metadata={"language": "ko", "topic": "rag"}
        ),
    ]
    
    result = rag_service.upsert_text(collection_id, items)
    assert result["count"] == 2
    
    # Retrieve with Korean query
    chunks = rag_service.retrieve(collection_id, "벡터 데이터베이스", top_k=2)
    
    assert len(chunks) > 0
    assert "벡터" in chunks[0].text
    
    print(f"\n[Korean] query='벡터 데이터베이스' -> text='{chunks[0].text[:30]}...'")


@pytest.mark.live
def test_different_collections_isolated(rag_service):
    """Test that different collections are isolated."""
    collection1 = "test_coll1"
    collection2 = "test_coll2"
    
    # Upsert to collection 1
    items1 = [
        UpsertItem(text="Document in collection 1", metadata={"coll": "1"})
    ]
    rag_service.upsert_text(collection1, items1)
    
    # Upsert to collection 2
    items2 = [
        UpsertItem(text="Document in collection 2", metadata={"coll": "2"})
    ]
    rag_service.upsert_text(collection2, items2)
    
    # Retrieve from each collection
    chunks1 = rag_service.retrieve(collection1, "document", top_k=10)
    chunks2 = rag_service.retrieve(collection2, "document", top_k=10)
    
    assert len(chunks1) == 1
    assert len(chunks2) == 1
    assert chunks1[0].metadata["coll"] == "1"
    assert chunks2[0].metadata["coll"] == "2"
    
    print(f"\n[Isolation] coll1_count={len(chunks1)} coll2_count={len(chunks2)}")
