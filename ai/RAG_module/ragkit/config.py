"""Configuration for RAG service."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RAGConfig:
    """Configuration for RAG service.
    
    Attributes:
        persist_dir: Directory for ChromaDB persistence
        embedding_model: OpenAI embedding model (text-embedding-3-large recommended)
        openai_api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        
    Example:
        >>> config = RAGConfig(
        ...     persist_dir="./my_vectordb",
        ...     embedding_model="text-embedding-3-large"
        ... )
    """
    
    persist_dir: str = "./test_chroma_data"
    embedding_model: str = "text-embedding-3-large"
    openai_api_key: str | None = None
    
    def __post_init__(self):
        """Ensure persist_dir exists."""
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
