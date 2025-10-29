"""Example: Ingest PDF pages into RAG system."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ragkit import RAGService, RAGConfig


def main():
    """Ingest a PDF file into RAG system."""
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    # Get PDF path from command line
    if len(sys.argv) < 2:
        print("Usage: python ingest_pdf_pages.py <pdf_path> [collection_id]")
        print("\nExample:")
        print("  python ingest_pdf_pages.py ../test_data/sample_lecture.pdf lectures_2025")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    collection_id = sys.argv[2] if len(sys.argv) > 2 else "default_collection"
    
    # Verify PDF exists
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    print(f"📚 Ingesting PDF: {pdf_path}")
    print(f"📦 Collection: {collection_id}\n")
    
    # Create RAG service
    config = RAGConfig(
        persist_dir="./chroma_data",
        embedding_model="text-embedding-3-large"
    )
    service = RAGService(config)
    
    # Upsert PDF
    base_metadata = {
        "document_type": "lecture",
        "ingestion_date": "2025-03-15"
    }
    
    result = service.upsert_pdf(
        collection_id=collection_id,
        pdf_path=pdf_path,
        base_metadata=base_metadata
    )
    
    print(f"✅ Success!")
    print(f"   Pages ingested: {result['count']}")
    print(f"   Embedding dimension: {result['embedding_dim']}")
    print(f"   Collection: {result['collection_id']}")
    
    # Test retrieval
    print(f"\n🔍 Testing retrieval with query: 'vector database'")
    chunks = service.retrieve(collection_id, "vector database", top_k=3)
    
    print(f"\n📄 Top {len(chunks)} results:")
    for i, chunk in enumerate(chunks, 1):
        print(f"\n{i}. [Score: {chunk.score:.3f}] {chunk.id}")
        print(f"   Page: {chunk.metadata.get('page', 'N/A')}")
        print(f"   Text preview: {chunk.text[:100]}...")


if __name__ == "__main__":
    main()
