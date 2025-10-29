"""Configuration for RAG service."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RAGConfig:
    """Configuration for RAG service.
    
    Attributes:
        persist_dir: Directory for persistent Chroma storage
        embedding_model: OpenAI embedding model name
        chunk_size: Default chunk size for text splitting (not used if not chunking)
        chunk_overlap: Overlap between chunks (not used if not chunking)
        openai_api_key: OpenAI API key (if None, reads from OPENAI_API_KEY env var)
        
    Example:
        >>> config = RAGConfig(
        ...     persist_dir="./my_chroma_data",
        ...     embedding_model="text-embedding-3-large"
        ... )
    """
    
    persist_dir: str = "./chroma_data"
    embedding_model: str = "text-embedding-3-large"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    openai_api_key: str | None = None
    
    def __post_init__(self):
        """Ensure persist_dir exists."""
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
