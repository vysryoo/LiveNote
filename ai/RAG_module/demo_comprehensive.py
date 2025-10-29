"""Comprehensive demo of RAGKit functionality.

This script demonstrates:
1. Upserting 10 text documents
2. Upserting 1 PDF file
3. Running 3 different queries with top_k=2
"""

import os
import sys
from pathlib import Path

from ragkit import RAGService, RAGConfig
from ragkit.models import UpsertItem, RetrieveFilters


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_result(label: str, value: any):
    """Print a labeled result."""
    print(f"{'':>4}✓ {label}: {value}")


def main():
    """Run comprehensive demo."""
    
    print_section("🚀 RAGKit Comprehensive Demo")
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set. Please set it:")
        print("   export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)
    
    # Initialize service
    print("📦 Initializing RAG service...")
    config = RAGConfig(
        persist_dir="./demo_chroma_data",
        embedding_model="text-embedding-3-small"  # Faster for demo
    )
    service = RAGService(config)
    print_result("Service initialized", "✓")
    
    # -------------------------------------------------------------------------
    # Part 1: Upsert 10 text documents
    # -------------------------------------------------------------------------
    print_section("1️⃣  Upserting 10 Text Documents")
    
    text_items = [
        UpsertItem(
            text="Vector databases are specialized systems designed to store and query high-dimensional vectors efficiently.",
            metadata={"category": "database", "topic": "vectors", "difficulty": "intermediate"}
        ),
        UpsertItem(
            text="Embeddings are numerical representations of text that capture semantic meaning in a dense vector space.",
            metadata={"category": "ml", "topic": "embeddings", "difficulty": "intermediate"}
        ),
        UpsertItem(
            text="RAG (Retrieval-Augmented Generation) combines retrieval of relevant documents with text generation.",
            metadata={"category": "nlp", "topic": "rag", "difficulty": "advanced"}
        ),
        UpsertItem(
            text="ChromaDB is an open-source embedding database that makes it easy to build LLM applications.",
            metadata={"category": "database", "topic": "chromadb", "difficulty": "beginner"}
        ),
        UpsertItem(
            text="Semantic search finds documents based on meaning rather than exact keyword matches.",
            metadata={"category": "search", "topic": "semantic", "difficulty": "intermediate"}
        ),
        UpsertItem(
            text="Python is a versatile programming language widely used for data science and machine learning.",
            metadata={"category": "programming", "topic": "python", "difficulty": "beginner"}
        ),
        UpsertItem(
            text="Transformers revolutionized natural language processing with their attention mechanism.",
            metadata={"category": "ml", "topic": "transformers", "difficulty": "advanced"}
        ),
        UpsertItem(
            text="OpenAI provides powerful APIs for embeddings, chat completion, and image generation.",
            metadata={"category": "api", "topic": "openai", "difficulty": "intermediate"}
        ),
        UpsertItem(
            text="LangChain is a framework for developing applications powered by language models.",
            metadata={"category": "framework", "topic": "langchain", "difficulty": "intermediate"}
        ),
        UpsertItem(
            text="Fine-tuning adapts pre-trained models to specific tasks or domains with custom data.",
            metadata={"category": "ml", "topic": "fine-tuning", "difficulty": "advanced"}
        ),
    ]
    
    result = service.upsert_text("demo_collection", text_items)
    print_result("Documents upserted", result['count'])
    print_result("Embedding dimension", result['embedding_dim'])
    print_result("Collection ID", result['collection_id'])
    
    # -------------------------------------------------------------------------
    # Part 2: Upsert 1 PDF
    # -------------------------------------------------------------------------
    print_section("2️⃣  Upserting PDF Document")
    
    pdf_path = "./test_data/simple_test.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF not found: {pdf_path}")
        print("   Skipping PDF upsert...")
    else:
        result = service.upsert_pdf(
            "demo_collection",
            pdf_path,
            base_metadata={
                "document_type": "test_pdf",
                "source": "demo",
                "timestamp": 1704067200  # 2024-01-01
            }
        )
        print_result("PDF pages upserted", result['count'])
        print_result("Embedding dimension", result['embedding_dim'])
        print_result("PDF file", pdf_path)
    
    # -------------------------------------------------------------------------
    # Part 3: Run 3 queries with top_k=2
    # -------------------------------------------------------------------------
    print_section("3️⃣  Running Queries (top_k=2)")
    
    queries = [
        {
            "query": "What are vector databases used for?",
            "filters": None,
            "description": "General query about vector databases"
        },
        {
            "query": "How does machine learning work?",
            "filters": RetrieveFilters(custom={"category": "ml"}),
            "description": "ML query with category filter"
        },
        {
            "query": "Explain embeddings and their applications",
            "filters": RetrieveFilters(custom={"difficulty": "intermediate"}),
            "description": "Query filtered by difficulty level"
        },
    ]
    
    for i, q in enumerate(queries, 1):
        print(f"\n{'─' * 80}")
        print(f"Query #{i}: {q['description']}")
        print(f"{'─' * 80}")
        print(f"  Question: \"{q['query']}\"")
        
        if q['filters']:
            filter_info = []
            if q['filters'].subject:
                filter_info.append(f"subject={q['filters'].subject}")
            if q['filters'].custom:
                for k, v in q['filters'].custom.items():
                    filter_info.append(f"{k}={v}")
            print(f"  Filters:  {', '.join(filter_info)}")
        else:
            print(f"  Filters:  None")
        
        print()
        
        chunks = service.retrieve(
            "demo_collection",
            q['query'],
            top_k=2,
            filters=q['filters']
        )
        
        if not chunks:
            print("  ⚠️  No results found")
            continue
        
        for j, chunk in enumerate(chunks, 1):
            print(f"  Result #{j}:")
            print(f"    Score:    {chunk.score:.4f}")
            print(f"    ID:       {chunk.id}")
            
            # Print metadata
            meta_items = []
            for key, value in chunk.metadata.items():
                if key not in ['source']:  # Skip less important metadata
                    meta_items.append(f"{key}={value}")
            if meta_items:
                print(f"    Metadata: {', '.join(meta_items)}")
            
            # Print text (truncated if too long)
            text_preview = chunk.text[:120]
            if len(chunk.text) > 120:
                text_preview += "..."
            print(f"    Text:     {text_preview}")
            print()
    
    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    print_section("✅ Demo Completed Successfully")
    
    print("Summary:")
    print(f"  • Upserted 10 text documents")
    if Path(pdf_path).exists():
        print(f"  • Upserted 1 PDF file (3 pages)")
    print(f"  • Ran 3 different queries")
    print(f"  • Retrieved top 2 results per query")
    print(f"  • Collection: demo_collection")
    print(f"  • Data stored in: {config.persist_dir}")
    print()


if __name__ == "__main__":
    main()
