"""Tests for PDF upserting functionality."""

import pytest
from pathlib import Path


@pytest.mark.live
def test_pdf_pages_counted_correctly(rag_service, sample_pdf_path):
    """Test that PDF pages are counted correctly with deterministic IDs."""
    collection_id = "test_pdf_pages"
    
    result = rag_service.upsert_pdf(
        collection_id,
        sample_pdf_path,
    )
    
    assert result["count"] == 3  # simple_test.pdf has 3 pages
    assert result["embedding_dim"] > 0
    
    # Retrieve all pages
    chunks = rag_service.retrieve(collection_id, "test document", top_k=10)
    
    # Check IDs are in format: {basename}|p{page_num}
    expected_basename = Path(sample_pdf_path).stem
    ids = [chunk.id for chunk in chunks]
    
    assert f"{expected_basename}|p0" in ids
    assert f"{expected_basename}|p1" in ids
    assert f"{expected_basename}|p2" in ids
    
    print(f"\n[PDF Pages] count={result['count']} ids={ids}")


@pytest.mark.live
def test_base_metadata_merged(rag_service, sample_pdf_path):
    """Test that base_metadata is merged into each page."""
    collection_id = "test_pdf_metadata"
    
    base_metadata = {
        "subject": "Computer Science",
        "year": 2025,
        "semester": "Spring",
    }
    
    rag_service.upsert_pdf(
        collection_id,
        sample_pdf_path,
        base_metadata=base_metadata,
    )
    
    # Retrieve pages
    chunks = rag_service.retrieve(collection_id, "page", top_k=3)
    
    # Verify metadata is present in all pages
    for chunk in chunks:
        assert chunk.metadata["subject"] == "Computer Science"
        assert chunk.metadata["year"] == 2025
        assert chunk.metadata["semester"] == "Spring"
        assert "source" in chunk.metadata  # PDF filename
        assert "page" in chunk.metadata  # Page number
    
    print(f"\n[PDF Metadata] subject={chunks[0].metadata['subject']} page={chunks[0].metadata['page']}")


@pytest.mark.live
def test_pdf_reupsert_idempotent(rag_service, sample_pdf_path):
    """Test that re-upserting same PDF is idempotent."""
    collection_id = "test_pdf_idempotent"
    
    # First upsert
    result1 = rag_service.upsert_pdf(collection_id, sample_pdf_path)
    count1 = result1["count"]
    
    # Second upsert
    result2 = rag_service.upsert_pdf(collection_id, sample_pdf_path)
    count2 = result2["count"]
    
    assert count1 == count2
    
    # Verify total count hasn't doubled
    chunks = rag_service.retrieve(collection_id, "document", top_k=20)
    assert len(chunks) == count1
    
    print(f"\n[PDF Idempotent] first_count={count1} second_count={count2} total_unique={len(chunks)}")


@pytest.mark.live
def test_invalid_pdf_path_raises(rag_service):
    """Test that corrupt/invalid path raises ValueError."""
    collection_id = "test_pdf_invalid"
    
    # Non-existent file
    with pytest.raises(ValueError, match="not found"):
        rag_service.upsert_pdf(collection_id, "/nonexistent/file.pdf")
    
    # Non-PDF file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"Not a PDF")
        txt_path = f.name
    
    try:
        with pytest.raises(ValueError, match="not a PDF"):
            rag_service.upsert_pdf(collection_id, txt_path)
    finally:
        Path(txt_path).unlink()
    
    print("\n[PDF Invalid] ValueError raised as expected")


@pytest.mark.live
def test_large_pdf_performance(rag_service, sample_lecture_pdf_path):
    """Test that larger PDF processes within reasonable time."""
    import time
    
    collection_id = "test_pdf_large"
    
    start_time = time.time()
    
    result = rag_service.upsert_pdf(
        collection_id,
        sample_lecture_pdf_path,
        base_metadata={"course": "CS301"}
    )
    
    elapsed = time.time() - start_time
    
    assert result["count"] == 6  # sample_lecture.pdf has 6 pages
    assert elapsed < 30  # Should complete within 30 seconds (with real API)
    
    print(f"\n[PDF Performance] count={result['count']} elapsed={elapsed:.2f}s")
