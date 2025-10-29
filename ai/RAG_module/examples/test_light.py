"""Simple test example for RAGKit."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ragkit import RAGService, RAGConfig
from ragkit.models import UpsertItem


def main():
    """Simple example showing basic RAGKit usage."""
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)
    
    print("🚀 RAGKit Simple Example\n")
    
    # 1. Create RAG service
    print("1️⃣ Creating RAG service...")
    config = RAGConfig(
        persist_dir="./example_chroma_data",
        embedding_model="text-embedding-3-small"  # Smaller model for demo
    )
    service = RAGService(config)
    print("   ✓ Service created\n")
    
    # 2. Create collection and upsert documents
    print("2️⃣ Upserting documents...")
    collection_id = "demo_collection"
    
    docs = [
        UpsertItem(
            text="Vector databases are specialized systems for storing and querying high-dimensional vectors.",
            metadata={"topic": "databases", "difficulty": "intermediate"}
        ),
        UpsertItem(
            text="RAG combines retrieval with generation to create more accurate AI responses.",
            metadata={"topic": "ai", "difficulty": "advanced"}
        ),
        UpsertItem(
            text="Embeddings transform text into numerical vectors that capture semantic meaning.",
            metadata={"topic": "nlp", "difficulty": "beginner"}
        ),
    ]
    
    result = service.upsert_text(collection_id, docs)
    print(f"   ✓ Upserted {result['count']} documents")
    print(f"   ✓ Embedding dimension: {result['embedding_dim']}\n")
    
    # 3. Query the collection
    print("3️⃣ Querying collection...")
    query = "What are vector databases?"
    
    chunks = service.retrieve(collection_id, query, top_k=2)
    
    print(f"   Query: '{query}'")
    print(f"   Found {len(chunks)} results:\n")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"   Result {i}:")
        print(f"   └─ Score: {chunk.score:.3f}")
        print(f"   └─ Topic: {chunk.metadata.get('topic', 'N/A')}")
        print(f"   └─ Text: {chunk.text}")
        print()
    
    print("✅ Demo completed successfully!")


if __name__ == "__main__":
    main()
