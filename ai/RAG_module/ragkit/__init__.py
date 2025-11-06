"""RAGKit - A Python library for RAG (Retrieval-Augmented Generation) using Chroma and OpenAI.

This package provides a clean, production-ready interface for:
- Upserting text documents and PDF files into vector databases
- Retrieving relevant chunks based on semantic similarity
- Managing collections with persistent storage

Example:
    >>> from ragkit import RAGService, RAGConfig
    >>> config = RAGConfig()
    >>> service = RAGService(config)
    >>> result = service.upsert_text("my_collection", [
    ...     {"text": "Hello world", "metadata": {"source": "test"}}
    ... ])
    >>> chunks = service.retrieve("my_collection", "greeting", top_k=3)
"""

from .config import RAGConfig
from .models import UpsertItem, RetrieveFilters, RetrievedChunk
from .service import RAGService

__version__ = "0.1.0"

__all__ = [
    "RAGConfig",
    "RAGService",
    "UpsertItem",
    "RetrieveFilters",
    "RetrievedChunk",
]
