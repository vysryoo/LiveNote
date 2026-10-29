"""Tests for retrieval functionality."""

import pytest

from ragkit.models import UpsertItem, RetrieveFilters


@pytest.mark.live
def test_top_k_size_respected_sorted(rag_service):
    """Test that top_k size is respected and scores are sorted descending."""
    collection_id = "test_retrieve_topk"
    
    # Upsert multiple documents
    items = [
        UpsertItem(text="Python is a programming language", metadata={"id": "1"}),
        UpsertItem(text="Java is also a programming language", metadata={"id": "2"}),
        UpsertItem(text="Databases store structured data", metadata={"id": "3"}),
        UpsertItem(text="Vector databases store embeddings", metadata={"id": "4"}),
        UpsertItem(text="Machine learning uses neural networks", metadata={"id": "5"}),
    ]
    
    rag_service.upsert_text(collection_id, items)
    
    # Retrieve with top_k=3
    chunks = rag_service.retrieve(collection_id, "programming language", top_k=3)
    
    assert len(chunks) == 3
    
    # Verify scores are sorted descending
    scores = [chunk.score for chunk in chunks]
    assert scores == sorted(scores, reverse=True)
    
    print(f"\n[Top-K] query='programming language' -> count={len(chunks)} scores={[round(s, 2) for s in scores]}")


@pytest.mark.live
def test_filter_by_subject(rag_service):
    """Test filtering by subject metadata field."""
    collection_id = "test_retrieve_subject"
    
    # Upsert documents with different subjects
    items = [
        UpsertItem(text="Python programming basics", metadata={"subject": "Programming"}),
        UpsertItem(text="Java OOP concepts", metadata={"subject": "Programming"}),
        UpsertItem(text="Photosynthesis in plants", metadata={"subject": "Biology"}),
        UpsertItem(text="DNA replication process", metadata={"subject": "Biology"}),
    ]
    
    rag_service.upsert_text(collection_id, items)
    
    # Retrieve with subject filter
    filters = RetrieveFilters(subject="Programming")
    chunks = rag_service.retrieve(collection_id, "concepts", top_k=10, filters=filters)
    
    # Should only get Programming documents
    assert len(chunks) == 2
    for chunk in chunks:
        assert chunk.metadata["subject"] == "Programming"
    
    print(f"\n[Filter Subject] subject='Programming' -> count={len(chunks)} texts={[c.text[:20] for c in chunks]}")


@pytest.mark.live
def test_filter_by_min_timestamp(rag_service):
    """Test filtering by minimum timestamp removes older chunks."""
    collection_id = "test_retrieve_timestamp"
    
    # Upsert documents with different timestamps
    items = [
        UpsertItem(text="Old document from 2020", metadata={"timestamp": 1577836800}),  # 2020-01-01
        UpsertItem(text="Recent document from 2024", metadata={"timestamp": 1704067200}),  # 2024-01-01
        UpsertItem(text="Very recent document from 2025", metadata={"timestamp": 1735689600}),  # 2025-01-01
    ]
    
    rag_service.upsert_text(collection_id, items)
    
    # Retrieve with min_timestamp filter (2024+)
    filters = RetrieveFilters(min_timestamp=1704067200)
    chunks = rag_service.retrieve(collection_id, "document", top_k=10, filters=filters)
    
    # Should only get 2024+ documents
    assert len(chunks) == 2
    for chunk in chunks:
        assert chunk.metadata["timestamp"] >= 1704067200
    
    print(f"\n[Filter Timestamp] min_timestamp=2024 -> count={len(chunks)}")


@pytest.mark.live
def test_similar_query_returns_known_page(rag_service, sample_pdf_path):
    """Test that similar query returns the expected page first."""
    collection_id = "test_retrieve_similar"
    
    # Upsert PDF
    rag_service.upsert_pdf(collection_id, sample_pdf_path)
    
    # Query for STL vector (should match page 1)
    chunks = rag_service.retrieve(collection_id, "STL vector capacity", top_k=3)
    
    assert len(chunks) > 0
    
    # First result should be the page about STL vector
    top_chunk = chunks[0]
    assert "vector" in top_chunk.text.lower() or "capacity" in top_chunk.text.lower()
    assert top_chunk.metadata["page"] == 1  # Page 1 is about STL vector
    
    print(f"\n[Similar Query] q='STL vector capacity' -> page={top_chunk.metadata['page']} score={top_chunk.score:.2f}")


@pytest.mark.live
def test_empty_collection_returns_empty(rag_service):
    """Test that querying empty collection returns empty list."""
    collection_id = "test_retrieve_empty"
    
    # Create empty collection
    rag_service.vector_store.create_collection(collection_id)
    
    # Query
    chunks = rag_service.retrieve(collection_id, "anything", top_k=5)
    
    assert len(chunks) == 0
    
    print("\n[Empty Collection] query returned [] as expected")
